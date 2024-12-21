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
from .node_utils import save_state_for_testing, copy_figures
from utils.latex_to_markdown import create_markdown_pipeline

'''IMPORT ALL TOOLS HERE AND CREATE LIST OF TOOLS TO BE PASSED TO THE AGENT.'''
from tools.script_executor import run_script
from tools.file_tree import get_file_tree
from tools.query_chromadb import query_chromadb
from tools.multimodal_query import NomicVisionQuerier
#from utils.latextopdf import latex_to_pdf

import logging
from langchain_core.messages import SystemMessage, HumanMessage
from colorama import Fore, Style
#from utils.latextopdf import latex_to_pdf

import logging
from typing import Dict, Any
from colorama import Fore, Style
from langchain_core.messages import SystemMessage, HumanMessage
import os
from schemas import State
from utils.latex_utils import extract_latex_and_message, build_content_summary, latex_to_pdf, latex_to_pdf_pandoc, verify_image_paths, verify_miktex_installation

from pathlib import Path
import importlib.util

# Dynamically resolve the path to config.py
CURRENT_FILE = Path(__file__).resolve()
SAGAN_MULTIMODAL = CURRENT_FILE.parent.parent.parent.parent
CONFIG_PATH = SAGAN_MULTIMODAL / "config.py"

# Load config.py dynamically
spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

load_dotenv(dotenv_path=config.ENV_PATH)
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
        vector_store_path=str(config.VECTOR_DB_PATHS['astro_db']),  # Use path from config
        llm_name=config.MODEL_SETTINGS['SENTENCE_TRANSFORMER']  # Use model setting from config
    ))
    state["messages"].append(system_prompt)

    try:
        # Use the research tools to actually query the database
        qa_pairs = {}
        for question in abstract_questions:
            result = query_chromadb(
                str(config.VECTOR_DB_PATHS['astro_db']),  # Use path from config
                config.MODEL_SETTINGS['SENTENCE_TRANSFORMER'],  # Use model setting from config
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
        vector_store_path=str(config.VECTOR_DB_PATHS['fnr_template_db']),  # Use path from config
        llm_name=config.MODEL_SETTINGS['SENTENCE_TRANSFORMER']  # Use model setting from config
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
        output_path = config.NODEWISE_OUTPUT_PATH / "section_wise_answers_generator_logging.txt"
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
                            persist_dir=str(config.VECTOR_DB_PATHS['astro_ai2']),
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

    try:
        # Format the prompt with state data
        prompt = PLAN_PROMPT.format(
            abstract=state['abstract_text'],
            section_answers=json.dumps(state['section_answers'], indent=2)
        )

        messages = [SystemMessage(content=prompt)]
        response = llm.invoke(messages)
        print("DEBUG - Raw LLM response received")

        # Try to parse the response as JSON
        try:
            content = response.content.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                content = content[start_idx:end_idx]

            plan_dict = json.loads(content)
            if not isinstance(plan_dict, dict):
                raise ValueError("Parsed plan is not a dictionary")

            print(f"DEBUG - Successfully parsed plan with {len(plan_dict)} sections")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing plan: {e}")
            # Use section_topics to create a basic plan if parsing fails
            plan_dict = {
                section: ["Introduction and Background", 
                         "Main Concepts and Methods", 
                         "Analysis and Discussion", 
                         "Conclusions and Future Work"] 
                for section in state.get("section_topics", [])
            }
            print("Created fallback plan structure")

        # Update state
        state["messages"].append(response)
        state["plan"] = plan_dict

        # Save debug output
        output_path = config.NODEWISE_OUTPUT_PATH / "plan_node_logging.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as file:
            file.write("PLAN NODE OUTPUT:\n")
            json.dump(plan_dict, file, indent=4)
            file.write("\n\nFinal plan structure:\n")
            for section, steps in plan_dict.items():
                file.write(f"\n{section}:\n")
                for step in steps:
                    file.write(f"  - {step}\n")

        # Save state in both human-readable and machine-readable formats
        save_state_for_testing(state, "plan_node")

        print(f"################ PLAN NODE END #################{Style.RESET_ALL}")
        return state

    except Exception as e:
        print(f"Error in plan_node: {str(e)}")
        # Create basic plan structure using section_topics
        state["plan"] = {
            section: ["Introduction", "Main Content", "Conclusion"] 
            for section in state.get("section_topics", [])
        }
        return state


class GenerationError(Exception):
    """Custom exception for generation-related errors."""
    pass



def generation_node(state: dict) -> dict:
    """
    Generates LaTeX sections iteratively for each section using the plan structure.
    Returns updated state with generated sections.
    """
    print("################ GENERATION NODE BEGIN #################")

    try:
        # Debug print to check state
        print("DEBUG - State keys:", state.keys())
        print("DEBUG - Plan in state:", state.get("plan"))
        
        plan = state.get("plan")
        if not plan:
            raise ValueError("No plan found in state")
        
        if not isinstance(plan, dict) or len(plan) == 0:
            raise ValueError("Plan is empty or not a dictionary. Cannot proceed with generation.")

        generated_sections = {}

        # Import the WRITER_PROMPT
        # from prompts.prompts import WRITER_PROMPT

        for section_title, steps in plan.items():
            print(f"Generating content for section: {section_title}")

            # Convert list of steps into a bullet-point string
            section_plan_formatted = "\n".join(f"- {step}" for step in steps)

            # Get section data
            section_data = state.get("section_answers", {}).get(section_title, [])
            section_data_formatted = json.dumps(section_data, indent=4)

            prompt = WRITER_PROMPT.format(
                project_title=state.get("project_title", ""),
                project_description=state.get("project_description", ""),
                abstract=state.get("abstract_text", ""),
                section_title=section_title,
                section_plan=section_plan_formatted,
                section_data_formatted=section_data_formatted
            )

            messages = [SystemMessage(content=prompt)]
            response = llm.invoke(messages)
            section_latex = response.content.strip()

            if not section_latex:
                print(f"Warning: Empty response for section '{section_title}'. Skipping.")
                continue

            generated_sections[section_title] = section_latex
            state["messages"].extend([messages[0], response])

        # Update state with generated sections
        state["generated_sections"] = generated_sections

        # Save the generated sections to a file
        output_path = config.OUTPUT_PDF_PATH / "generated_sections.txt"
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(generated_sections, file, indent=4, ensure_ascii=False)

        # Save state in both human-readable and machine-readable formats
        save_state_for_testing(state, "generation_node")    

        print("################ GENERATION NODE END #################")
        return state

    except Exception as e:
        print(f"Critical error in generation_node: {str(e)}")
        state["messages"].append(SystemMessage(content=f"Error in generation_node: {str(e)}"))
        return state


def formatting_node(state: State) -> State:
    print(f"{Fore.LIGHTYELLOW_EX}################ FORMATTING NODE BEGIN #################")
    try:
        base_output_path = config.OUTPUT_PDF_PATH
        figures_path = Path(config.OUTPUT_PDF_PATH / "figures")
        figures_path.mkdir(parents=True, exist_ok=True)

        # Copy figures from consolidated_template to output path
        copy_figures(config.CONSOLIDATED_TEMPLATE_PATH, figures_path)

        template_path = config.CONSOLIDATED_TEMPLATE_PATH / "consolidated.tex"

        ############################################################################

        # Read the template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # Split template into parts
        doc_start = template_content.split('\\begin{document}')[0]
        
       
        # Insert margin settings before \begin{document}
        if '\\begin{document}' in doc_start:
            doc_parts = doc_start.split('\\begin{document}')
            doc_start = doc_parts[0] 
        else:
            doc_start = doc_start 

        doc_end = '\\end{document}' #template_content.split()[1]
        
        # Extract the initial fixed content (title and table)
        title_section = """
\\vspace{10cm}
\\maketitle

\\begin{center}
\\begin{tabular}{|p{4.5cm}|p{0.6\\textwidth}|}
\\hline
\\bf Project Acronym  &  \\\\ \\hline
\\bf Principal Investigator (PI)  &  Dr. Alexandre Bartel \\\\ \\hline
\\bf Host Institution  & \\\\ \\hline
\\end{tabular}
\\end{center}

\\newpage"""

        # # Get content from state
        # draft = state["draft"]
        # plan = state.get("plan", "")
        
        # Retrieve required fields from state
        generated_sections = state.get("generated_sections", {})

        # Build document content
        document_content = []
        document_content.append(doc_start)
        document_content.append('\\begin{document}')
        document_content.append(title_section)

        # Add generated sections directly from the draft
        if generated_sections:
            for section_header, section_content in generated_sections.items():

                # Strip 'latex\n' from the beginning and any trailing quotes or backticks
                cleaned_content = section_content
                if cleaned_content.startswith('```latex\n'):
                    cleaned_content = cleaned_content[8:]  # Remove ```latex\n
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]  # Remove trailing ```
                    
                document_content.append(cleaned_content)  # Add the section content
        
        document_content.append(doc_end)
        
        final_latex_document = '\n'.join(document_content)
        state["draft"] = final_latex_document
        
        
        output_path = Path(config.OUTPUT_PDF_PATH / "output.tex") # writing latex doc to output.tex
        output_path.write_text(final_latex_document, encoding='utf-8')
        print(f"LaTeX file written to: {output_path}")

        # # Create and use the LaTeX to Markdown converter
        # latex_to_md = create_markdown_pipeline()
        # conversion_result = latex_to_md.convert_latex_to_markdown(
        #     str(output_path),
        #     output_dir=str(OUTPUT_PDF_PATH)
        # )

        # if conversion_result["success"]:
        #     print(f"Successfully created Markdown file at: {conversion_result['markdown_path']}")
        #     state["markdown_path"] = conversion_result["markdown_path"]
        # else:
        #     print(f"Failed to convert to Markdown: {conversion_result.get('error', 'Unknown error')}")

        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        original_dir = os.getcwd()
        os.chdir(str(config.OUTPUT_PDF_PATH))
        
        # creating output.md from output.tex
        os.system("pandoc -s output.tex -o output.md")

        # creating output.pdf from output.tex (by first using pdflatex, and if that fails, pandoc)
        try:
            result = os.system("pdflatex output.tex")
            
            if result == 0:
                success = True

            else:
                success = False

            if success:
                pdf_path = config.OUTPUT_PDF_PATH / "output.pdf"
                if pdf_path.exists():
                    print(f"Successfully generated PDF found at: {pdf_path}")
                else:
                    print("Generated PDF file not found")
                    success = False
            else:
                print("PDF generation failed")
        finally:
            os.chdir(original_dir)


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






