import json
import logging
from typing import List
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from colorama import init, Fore, Style

'''LOCAL IMPORTS'''
from schemas import State
from prompts.prompts import *
from models.chatgroq import BuildChatGroq, BuildChatOpenAI
from config import *
from .node_utils import save_state_for_testing, copy_figures

'''IMPORT ALL TOOLS HERE AND CREATE LIST OF TOOLS TO BE PASSED TO THE AGENT.'''
from tools.script_executor import run_script
from tools.file_tree import get_file_tree
from tools.query_chromadb import query_chromadb
from tools.multimodal_query import NomicVisionQuerier
#from utils.latextopdf import latex_to_pdf

from pathlib import Path
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from colorama import Fore, Style
#from utils.latextopdf import latex_to_pdf

import logging
from pathlib import Path
from typing import Dict, Any
from colorama import Fore, Style
from langchain_core.messages import SystemMessage, HumanMessage
import os
from schemas import State
from utils.latex_utils import extract_latex_and_message, build_content_summary, latex_to_pdf, latex_to_pdf_pandoc, verify_image_paths, verify_miktex_installation

# Initialize multimodal_vectordb_query from NomicVisionQuerier
# multimodal_vectordb_query = NomicVisionQuerier().search_similar

load_dotenv()
init()

logger = logging.getLogger(__name__)

# Define tools for terminal and research nodes
terminal_tools = [run_script, get_file_tree]
research_tools = [query_chromadb]

'''LLM TO USE'''
MODEL = "gpt-4o"
llm = BuildChatOpenAI(model=MODEL, temperature=0)

llm_with_terminal_tools = llm.bind_tools(terminal_tools)
llm_with_research_tools = llm.bind_tools(research_tools)

# SCHEMAS FOR THE OUTPUTS OF THE NODES
class PromptParserOutput(BaseModel):
    """Ensure that this is the output of the prompt_parser node."""
    project_title: str = Field(description="The title of the project.")
    project_description: str = Field(description="The description of the project based on the project title.")

class AbstractQuestionsGeneratorOutput(BaseModel):
    """Ensure that this is the output of the abstract_questions_generator node."""
    abstract_questions: list[str] = Field(description="A list of questions that may help the Agent understand the project better.")

class AbstractAnswersGeneratorOutput(BaseModel):
    """Ensure that this is the output of the abstract_answers_generator node."""
    abstract_qa_pairs: dict[str, str] = Field(description="A dictionary of questions and answers.")
    abstract_text: str = Field(description="A summary of the project based on the answers to the questions.")

class SectionTopicExtractorOutput(BaseModel):
    """Ensure that this is the output of the section_topic_extractor node."""
    section_topics: list[str] = Field(description="A list of sections and topics that need to be filled in the template.")

class SectionWiseQuestionGeneratorOutput(BaseModel):
    """Ensure that this is the output of the section_wise_question_generator node."""
    section_questions: dict[str, list[str]] = Field(description="A dictionary of sections and their corresponding list of questions.")

# NODES
terminal_tools_node = ToolNode(terminal_tools)
research_tools_node = ToolNode(research_tools)

def prompt_parser(state: State) -> State:
    """
    Given a user prompt, this node parses the prompt to extract the project title and description based on the project title.
    """
    print(f"{Fore.YELLOW}################ PROMPT PARSER BEGIN #################")
    system_prompt = SystemMessage(PROMPT_PARSER_PROMPT)
    state["messages"].append(system_prompt)

    try:
        response = llm.invoke(state["messages"])

        if not response or not hasattr(response, 'content'):
            raise ValueError("Invalid response from LLM.")
        
        llm_with_structured_output = llm.with_structured_output(PromptParserOutput)
        structured_response = llm_with_structured_output.invoke(response.content)

        if not hasattr(structured_response, 'project_title') or not hasattr(structured_response, 'project_description'):
            raise ValueError("Project title or description not found in the structured output.")

        # updating state before end-of-node logging
        state["messages"].append(response)
        state["project_title"] = structured_response.project_title
        state["project_description"] = structured_response.project_description

        # saving state in human readable format and machine readable format under outputpdf/nodewise_output
        save_state_for_testing(state, "prompt_parser")

        print(f"################ PROMPT PARSER END #################{Style.RESET_ALL}")
        return state

    except Exception as e:
        print(f"Error in prompt_parser: {e}")
        raise

def abstract_questions_generator(state: State) -> State:
    """
    Given the project title and description, this node creates a list of questions that may help it understand the project better. The answers to these questions will then be used to create a project abstract.
    """
    print(f"{Fore.RED}################ ABSTRACT QUESTIONS GENERATOR BEGIN #################")
    project_title = state.get("project_title", "")
    project_description = state.get("project_description", "")
    system_prompt = SystemMessage(ABSTRACT_QUESTIONS_GENERATOR_PROMPT.format(
        project_title=project_title, 
        project_description=project_description
    ))
    state["messages"].append(system_prompt)

    try:

        response = llm.invoke(state["messages"])

        if not response or not hasattr(response, 'content'):
            raise ValueError("Invalid response from LLM.")

        llm_with_structured_output = llm.with_structured_output(AbstractQuestionsGeneratorOutput)
        structured_response = llm_with_structured_output.invoke(response.content)

        if not hasattr(structured_response, 'abstract_questions'):
            raise ValueError("Abstract questions not found in the structured output.")
        
        # Update state before end-of-node logging
        state["messages"].append(response)
        state["abstract_questions"] = structured_response.abstract_questions

        # saving state in human readable format and machine readable format under outputpdf/nodewise_output
        save_state_for_testing(state, "abstract_questions_generator")

        print(f"################ ABSTRACT QUESTIONS GENERATOR END #################{Style.RESET_ALL}")
        return state

    except Exception as e:
        print(f"Error in abstract_questions_generator: {e}")
        print(f"################ ABSTRACT QUESTIONS GENERATOR END #################{Style.RESET_ALL}")
        state["messages"].append(SystemMessage(content=f"Error: {e}"))
        state["abstract_questions"] = None
        return state

def abstract_answers_generator(state: State) -> State:
    """
    Given the list of questions, this node creates answers to the questions generated by the abstract_questions_generator node.
    """
    print(f"{Fore.BLUE}################ ABSTRACT ANSWERS GENERATOR BEGIN #################")
    abstract_questions = state["abstract_questions"]
    system_prompt = SystemMessage(ABSTRACT_ANSWERS_GENERATOR_PROMPT.format(
        questions_list=abstract_questions, 
        vector_store_path=str(VECTOR_DB_PATHS['astro_db']),  # Use path from config
        llm_name=MODEL_SETTINGS['SENTENCE_TRANSFORMER']  # Use model setting from config
    ))
    state["messages"].append(system_prompt)

    try:
        # Use the research tools to actually query the database
        qa_pairs = {}
        for question in abstract_questions:
            result = query_chromadb(
                str(VECTOR_DB_PATHS['astro_db']),  # Use path from config
                MODEL_SETTINGS['SENTENCE_TRANSFORMER'],  # Use model setting from config
                question
            )
            answer = llm.invoke((f"Frame the following texts into one cohesive answer: {result}"))
            qa_pairs[question] = answer.content
            # print(f"Question: {question}\nAnswer: {answer.content} \n\n\n\n")

        # Now use the LLM to generate an abstract based on the retrieved answers
        project_title = state["project_title"]
        abstract_prompt = f"Based on the following question-answer pairs, generate a concise abstract for the {project_title} project:\n\n"
        for q, a in qa_pairs.items():
            abstract_prompt += f"Q: {q}\nA: {a}\n\n"
        
        abstract_response = llm.invoke(abstract_prompt)
        abstract_text = abstract_response.content

        structured_response = AbstractAnswersGeneratorOutput(
            abstract_qa_pairs=qa_pairs,
            abstract_text=abstract_text
        )

        # Updating state before end-of-node logging
        state["messages"].append(abstract_response)
        state["abstract_text"] = structured_response.abstract_text

        # saving state in human readable format and machine readable format under outputpdf/nodewise_output
        save_state_for_testing(state, "abstract_answers_generator")

        print(f"################ ABSTRACT ANSWERS GENERATOR END #################{Style.RESET_ALL}")

        return state


    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"################ ABSTRACT ANSWERS GENERATOR END #################{Style.RESET_ALL}")
        state["messages"] = [str(e)]
        state["abstract_text"] = None
        return state
    
def section_topic_extractor(state: State) -> State:
    """
    This node extracts the topics for each section of the project from the template pdf given by the user.
    """
    print(f"{Fore.CYAN}################ SECTION TOPIC EXTRACTOR BEGIN #################")
    system_prompt = SystemMessage(SECTION_TOPIC_EXTRACTOR_PROMPT.format(
        vector_store_path=str(VECTOR_DB_PATHS['fnr_template_db']),  # Use path from config
        llm_name=MODEL_SETTINGS['SENTENCE_TRANSFORMER']  # Use model setting from config
    ))
    state["messages"].append(system_prompt)

    try:
        response = llm_with_research_tools.invoke(state["messages"])

        if not response or not hasattr(response, 'content'):
            raise ValueError("Invalid response from LLM.")

        llm_with_structured_output = llm.with_structured_output(SectionTopicExtractorOutput)
        structured_response = llm_with_structured_output.invoke(response.content)

        if not hasattr(structured_response, 'section_topics'):
            raise ValueError("Section topics not found in the structured output.")

        # Updating state before end-of-node logging
        state["messages"].append(response)
        state["section_topics"] = structured_response.section_topics

        # saving state in human readable format and machine readable format under outputpdf/nodewise_output
        save_state_for_testing(state, "section_topic_extractor")

        print(f"################ SECTION TOPIC EXTRACTOR END #################{Style.RESET_ALL}")


        return state

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"################ SECTION TOPIC EXTRACTOR END #################{Style.RESET_ALL}")
        state["messages"] = [str(e)]
        state["section_topics"] = None
        return state

def section_wise_question_generator(state: State) -> State:
    """
    Given the list of sections, this node creates a list of questions for each section.
    """
    print(f"{Fore.MAGENTA}################ SECTION WISE QUESTION GENERATOR BEGIN #################")
    section_topics = state["section_topics"]
    system_prompt = SystemMessage(SECTION_WISE_QUESTION_GENERATOR_PROMPT.format(section_topics=section_topics))
    state["messages"].append(system_prompt)

    try:
        response = llm.invoke(state["messages"])
        
        # Parse JSON response directly into section_questions dictionary
        section_questions = json.loads(response.content)

        # Updating state before end-of-node logging
        state["messages"].append(response)
        state["section_questions"] = section_questions
        
        # saving state in human readable format and machine readable format under outputpdf/nodewise_output
        save_state_for_testing(state, "section_wise_question_generator")

        print(f"################ SECTION WISE QUESTION GENERATOR END #################{Style.RESET_ALL}")


        return state

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"################ SECTION WISE QUESTION GENERATOR END #################{Style.RESET_ALL}")
        state["messages"] = [str(e)]
        state["section_questions"] = None
        return state

def section_wise_answers_generator(state: State) -> State:
    """
    Generates answers for section-wise questions using the multimodal_vectordb_query tool.
    Integrates results into the 'section_answers' schema.
    """
    print(f"{Fore.GREEN}################ SECTION WISE ANSWERS GENERATOR BEGIN #################")
    
    section_questions = state.get("section_questions")
    if not section_questions:
        error_msg = "No section questions found in state. Previous node may have failed."
        print(f"Error: {error_msg}")
        state["messages"].append(SystemMessage(content=error_msg))
        state["section_answers"] = None
        return state

    try:
        # Initialize the multimodal query tool
        multimodal_tool = NomicVisionQuerier()
        section_answers = {}

        # Define the output file path
        output_path = NODEWISE_OUTPUT_PATH / "section_wise_answers_generator_logging.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

        with output_path.open("w", encoding="utf-8") as file:
            # Iterate over each section and its questions
            for section, questions in section_questions.items():
                file.write(f"\nProcessing section: {section}\n")
                section_answers[section] = []
                
                for question in questions:
                    file.write(f"\nQuerying for question: \n{question}\n")
                    
                    try:
                        # Use the multimodal_vectordb_query tool with correct parameters
                        results = multimodal_tool.multimodal_vectordb_query(
                            persist_dir=str(VECTOR_DB_PATHS['astro_ai2']),
                            query=question,
                            k=5
                        )
                        
                        file.write(f"Query results: {results}\n")
                        
                        if results and "Results" in results:
                            # Process each result and format according to schema
                            for result in results["Results"]:
                                answer_entry = {
                                    "content": result.get("content", ""),
                                    "images": result.get("images", [])
                                }
                                
                                # Only add non-empty results
                                if answer_entry["content"] or answer_entry["images"]:
                                    section_answers[section].append(answer_entry)
                                    file.write(f"Added answer entry with content length: {len(answer_entry['content'])}\n")
                                    file.write(f"Number of images: {len(answer_entry['images'])}\n")
                        else:
                            file.write("No results found for query\n")
                            
                    except Exception as query_error:
                        file.write(f"Error processing query: {query_error}\n")
                        continue

                # If no answers were found for the section, add a placeholder
                if not section_answers[section]:
                    section_answers[section] = [{
                        "content": "No relevant information found.",
                        "images": []
                    }]

                file.write(f"Completed answers for section: {section}\n")
                file.write(f"Number of answers: {len(section_answers[section])}\n")

            # Update state with the collected answers
            state["messages"].append(SystemMessage(content="Section-wise answers generated successfully"))
            state["section_answers"] = section_answers

            # Debug output
            file.write("\nFinal section answers structure:\n")
            for section, answers in section_answers.items():
                file.write(f"\nSection: {section}\n")
                file.write(f"Number of answers: {len(answers)}\n")
                for idx, answer in enumerate(answers):
                    file.write(f"Answer {idx + 1} - Content length: {len(answer['content'])}\n")
                    file.write(f"Number of images: {len(answer['images'])}\n")

        # saving state in human readable format and machine readable format under outputpdf/nodewise_output
        save_state_for_testing(state, "section_wise_answers_generator")

        print(f"################ SECTION WISE ANSWERS GENERATOR END #################{Style.RESET_ALL}")
        return state

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"################ SECTION WISE ANSWERS GENERATOR END #################{Style.RESET_ALL}")
        state["messages"].append(str(e))
        state["section_answers"] = None
        return state

def plan_node(state: State):
    print(f"{Fore.LIGHTYELLOW_EX}################ PLAN NODE BEGIN #################")
    messages = [
        SystemMessage(content=PLAN_PROMPT), 
        HumanMessage(content=f"Project abstract: {state['abstract_text']}\n\nSection-wise texts: {state['section_answers']}")
    ]
    response = llm.invoke(messages)

    # Updating state before end-of-node logging
    state["messages"].append(response)
    state["plan"] = response.content

    # saving state in human readable format and machine readable format under outputpdf/nodewise_output
    save_state_for_testing(state, "plan_node")

    print(f"################ PLAN NODE END #################{Style.RESET_ALL}")


    return state

class GenerationError(Exception):
    """Custom exception for generation-related errors."""
    pass



def generation_node(state: dict) -> dict:
    """
    Generates LaTeX sections iteratively for each section in the document.
    Args:
        state (dict): The current state containing all necessary information
    Returns:    
        dict: Updated state with generated LaTeX sections
    """
    print("################ GENERATION NODE BEGIN #################")
    
    try:
        # Extract required fields from state with validation
        project_metadata = {
            'project_title': state.get('project_title', ''),
            'project_description': state.get('project_description', ''),
            'abstract': state.get('abstract_text', '')
        }
        
        section_answers = state.get('section_answers', {})
        if not section_answers:
            raise ValueError("No section_answers found in state")
            
        # Initialize the generated sections dictionary
        generated_sections = {}
        
        # Process each section
        for section_title, section_data in section_answers.items():
            print(f"\nProcessing section: {section_title}")
            
            try:
                # Prepare section data
                if not section_data:
                    print(f"Warning: Empty data for section '{section_title}'. Skipping.")
                    continue
                    
                # Format section data for prompt
                section_data_formatted = json.dumps(section_data, indent=4)
                
                # Create prompt with all required information
                prompt = WRITER_PROMPT.format(
                    project_title=project_metadata['project_title'],
                    project_description=project_metadata['project_description'],
                    abstract=project_metadata['abstract'],
                    section_title=section_title,
                    section_data_formatted=section_data_formatted
                )
                
                # Generate LaTeX content for the section
                messages = [SystemMessage(content=prompt)]
                response = llm.invoke(messages)
                
                # Validate response
                section_latex = response.content.strip()
                if not section_latex:
                    raise ValueError(f"Empty response received for section {section_title}")
                
                # Store the generated content
                generated_sections[section_title] = section_latex
                
                # Update state messages
                state['messages'].extend([messages[0], response])
                
                print(f"Successfully generated content for section: {section_title}")
                
            except Exception as section_error:
                error_msg = f"Error processing section '{section_title}': {str(section_error)}"
                print(error_msg)
                continue
        
        # Update state with generated sections
        state['generated_sections'] = generated_sections
        
        # Save output to file with proper error handling
        output_path = OUTPUT_PDF_PATH / "generated_sections.txt"
        try:
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(generated_sections, file, indent=4, ensure_ascii=False)
            print(f"\nGenerated sections saved to: {output_path}")
        except Exception as save_error:
            print(f"Warning: Could not save output to file: {str(save_error)}")
            
        # saving state in human readable format and machine readable format under outputpdf/nodewise_output
        save_state_for_testing(state, "generation_node")
        print("################ GENERATION NODE END #################")

        return state
        
    except Exception as e:
        print(f"Critical error in generation_node: {str(e)}")
        state['generated_sections'] = {}
        state['messages'].append(SystemMessage(content=f"Error in generation_node: {str(e)}"))
        return state
    
    finally:
        print("################ GENERATION NODE END #################")


def formatting_node(state: State) -> State:
    print(f"{Fore.LIGHTYELLOW_EX}################ FORMATTING NODE BEGIN #################")
    try:
        base_output_path = OUTPUT_PDF_PATH
        base_output_path.mkdir(parents=True, exist_ok=True)

        # Copy figures from consolidated_template to output path
        copy_figures(CONSOLIDATED_TEMPLATE_PATH, base_output_path)
        
        # Read the LaTeX preamble from the consolidated template
        with open(CONSOLIDATED_TEMPLATE_PATH / "consolidated.tex", "r", encoding='utf-8') as f:
            latex_preamble = ""
            for line in f:
                if line.strip() == "\\begin{document}":
                    break
                latex_preamble += line

        # Retrieve required fields from state
        project_title = state.get("project_title", "Research Project")
        project_abstract = state.get("abstract_text", "No abstract provided.")
        generated_sections = state.get("generated_sections", {})

        if not generated_sections:
            raise ValueError("No generated sections found in state")

        # Debug: Print the abstract we have from the state
        print("DEBUG: Abstract text from state:", project_abstract)

        # Construct the LATEX document body using generated_sections
        latex_body = ""
        # Add generated sections directly from the draft
        if generated_sections:
            for section_header, section_content in generated_sections.items():
                latex_body += section_header  # Add the section header
                latex_body += section_content  # Add the section content

        latex_end = r"\end{document}"

        final_latex_document = latex_preamble + latex_body + latex_end

        # Debug: Print the first 300 chars of the final document to confirm abstract insertion
        print("DEBUG: Beginning of final LaTeX document:\n", final_latex_document[:300])

        # Write out the LaTeX file
        tex_path = base_output_path / "output.tex"
        tex_path.write_text(final_latex_document, encoding='utf-8')
        print(f"LaTeX file written to: {tex_path}")

        # Attempt to compile PDF
        original_dir = os.getcwd()
        os.chdir(str(base_output_path))
        try:
            success = latex_to_pdf("output.tex", str(base_output_path))
            if not success:
                print("pdflatex failed, trying pandoc...")
                success = latex_to_pdf_pandoc("output.tex", str(base_output_path))
            if success:
                pdf_path = base_output_path / "output.pdf"
                if pdf_path.exists():
                    print("Successfully generated PDF with abstract included")
                    state.update({
                        "pdf_status": "success",
                        "pdf_path": str(pdf_path),
                        "generation_message": "Document generated successfully"
                    })
                else:
                    print("PDF generation failed - file not found")
                    success = False
                    state.update({
                        "pdf_status": "failed",
                        "error": "PDF not found after compilation"
                    })
            else:
                print("PDF generation failed")
                state.update({
                    "pdf_status": "failed",
                    "error": "PDF generation failed"
                })
        finally:
            os.chdir(original_dir)

        # Store final latex content in state
        state["draft"] = final_latex_document

        # Define the output path
        output_path = Path(OUTPUT_PDF_PATH / "output.tex")

        # Write the final LaTeX document to the specified output path
        output_path.write_text(final_latex_document, encoding='utf-8')
        print(f"LaTeX file written to: {output_path}")

    except Exception as e:
        print(f"Error in formatting node: {e}")
        state.update({
            "error": str(e),
            "pdf_status": "error",
            "generation_message": f"Error during formatting: {str(e)}"
        })


    print(f"################ FORMATTING NODE END #################{Style.RESET_ALL}")

    # Save state in both human-readable and machine-readable formats
    save_state_for_testing(state, "formatting_node")

    return state







