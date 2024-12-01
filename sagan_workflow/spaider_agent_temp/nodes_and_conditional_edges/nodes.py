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

'''IMPORT ALL TOOLS HERE AND CREATE LIST OF TOOLS TO BE PASSED TO THE AGENT.'''
from tools.script_executor import run_script
from tools.file_tree import get_file_tree
from tools.query_chromadb import query_chromadb
from tools.multimodal_query import NomicVisionQuerier  # Correct import for multimodal query tool
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
    project_title: str = Field(description="The title of the project.")
    project_description: str = Field(description="The description of the project based on the project title.")

class AbstractQuestionsGeneratorOutput(BaseModel):
    abstract_questions: list[str] = Field(description="A list of questions that may help the Agent understand the project better.")

class AbstractAnswersGeneratorOutput(BaseModel):
    abstract_qa_pairs: dict[str, str] = Field(description="A dictionary of questions and answers.")
    abstract_text: str = Field(description="A summary of the project based on the answers to the questions.")

class SectionTopicExtractorOutput(BaseModel):
    section_topics: list[str] = Field(description="A list of sections and topics that need to be filled in the template.")

class SectionWiseQuestionGeneratorOutput(BaseModel):
    section_questions: dict[str, list[str]] = Field(description="A dictionary of sections and their corresponding list of questions.")

# Define nodes
terminal_tools_node = ToolNode(terminal_tools)
research_tools_node = ToolNode(research_tools)

def prompt_parser(state: State) -> State:
    print(f"{Fore.YELLOW}################ PROMPT PARSER BEGIN #################")
    system_prompt = SystemMessage(PROMPT_PARSER_PROMPT)
    state["messages"].append(system_prompt)

    try:
        response = llm.invoke(state["messages"])
        if not response or not hasattr(response, 'content'):
            raise ValueError("Invalid response from LLM.")
        llm_with_structured_output = llm.with_structured_output(PromptParserOutput)
        structured_response = llm_with_structured_output.invoke(response.content)

        state["messages"].append(response)
        state["project_title"] = structured_response.project_title
        state["project_description"] = structured_response.project_description
        print(f"PROMPT PARSER OUTPUT: {structured_response}")
        return state

    except Exception as e:
        print(f"Error in prompt_parser: {e}")
        raise


def abstract_questions_generator(state: State) -> State:
    """
    Generates a list of abstract-related questions based on project title and description.
    """
    print(f"{Fore.RED}################ ABSTRACT QUESTIONS GENERATOR BEGIN #################")
    try:
        project_title = state.get("project_title", "")
        project_description = state.get("project_description", "")
        system_prompt = SystemMessage(ABSTRACT_QUESTIONS_GENERATOR_PROMPT.format(
            project_title=project_title, 
            project_description=project_description
        ))
        state["messages"].append(system_prompt)

        response = llm.invoke(state["messages"])
        llm_with_structured_output = llm.with_structured_output(AbstractQuestionsGeneratorOutput)
        structured_response = llm_with_structured_output.invoke(response.content)

        # Update state
        state["messages"].append(response)
        state["abstract_questions"] = structured_response.abstract_questions
        return state

    except Exception as e:
        print(f"Error in abstract_questions_generator: {e}")
        state["messages"].append(SystemMessage(content=f"Error: {e}"))
        state["abstract_questions"] = None
        return state

def abstract_answers_generator(state: State) -> State:
    """
    Given the list of questions, this node creates answers to the questions generated by the abstract_questions_generator node.
    """
    print(f"{Fore.BLUE}################ ABSTRACT ANSWERS GENERATOR BEGIN #################")
    abstract_questions = state["abstract_questions"]
    system_prompt = SystemMessage(ABSTRACT_ANSWERS_GENERATOR_PROMPT.format(questions_list=abstract_questions))
    state["messages"].append(system_prompt)

    try:
        # Use the research tools to actually query the database
        qa_pairs = {}
        for question in abstract_questions:
            result = query_chromadb(
                "C:/UniLu/Spaider/sagan/ketan_sagan/SAW_code_plus_db/ingest_data/astroaidb",
                "sentence-transformers/all-MiniLM-L6-v2",
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

        # print(f"Abstract QA pairs: {structured_response.abstract_qa_pairs}")
        # print(f"\n\n\n\nAbstract text: {structured_response.abstract_text}")
        
        # Updating state before end-of-node logging
        state["messages"].append(abstract_response)
        state["abstract_text"] = structured_response.abstract_text
        print(f"\n\n\n\nstate at the end of abstract_answers_generator: \n")
        print("Messages: ")
        messages = state["messages"]
        if len(messages) >= 3:
            for message in messages[-3:]:
                print(f"{message.type}: {message.content}")
        else:
            for message in messages:
                print(f"{message.type}: {message.content}")
        for field_name, field_value in state.items():
            if field_name != "messages":
                print(f"- {field_name}: {field_value}")
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
    system_prompt = SystemMessage(SECTION_TOPIC_EXTRACTOR_PROMPT)
    state["messages"].append(system_prompt)

    try:
        response = llm_with_research_tools.invoke(state["messages"])
        # print(f"Response content: {response.content}")
        # print(f"Response type: {type(response)}")

        if not response or not hasattr(response, 'content'):
            raise ValueError("Invalid response from LLM.")

        llm_with_structured_output = llm.with_structured_output(SectionTopicExtractorOutput)
        structured_response = llm_with_structured_output.invoke(response.content)

        if not hasattr(structured_response, 'section_topics'):
            raise ValueError("Section topics not found in the structured output.")

        # print(f"Response content: {response.content}")
        # print(f"Section topics: {structured_response.section_topics}")
        
        # Updating state before end-of-node logging
        state["messages"].append(response)
        state["section_topics"] = structured_response.section_topics
        print(f"\n\n\n\nstate at the end of section_topic_extractor: \n")
        print("Messages: ")
        messages = state["messages"]
        if len(messages) >= 3:
            for message in messages[-3:]:
                print(f"{message.type}: {message.content}")
        else:
            for message in messages:
                print(f"{message.type}: {message.content}")
        for field_name, field_value in state.items():
            if field_name != "messages":
                print(f"- {field_name}: {field_value}")
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
        
        print(f"\n\n\n\nstate at the end of section_wise_question_generator: \n")
        print("Messages: ")
        messages = state["messages"]
        if len(messages) >= 3:
            for message in messages[-3:]:
                print(f"{message.type}: {message.content}")
        else:
            for message in messages:
                print(f"{message.type}: {message.content}")
        for field_name, field_value in state.items():
            if field_name != "messages":
                print(f"- {field_name}: {field_value}")
        print(f"################ SECTION WISE QUESTION GENERATOR END #################{Style.RESET_ALL}")


        return state

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"################ SECTION WISE QUESTION GENERATOR END #################{Style.RESET_ALL}")
        state["messages"] = [str(e)]
        state["section_questions"] = None
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
    print(f"\n\n\n\nstate at the end of plan_node: \n")
    print("Messages: ")
    messages = state["messages"]
    if len(messages) >= 3:
        for message in messages[-3:]:
            print(f"{message.type}: {message.content}")
    else:
        for message in messages:
            print(f"{message.type}: {message.content}")
    for field_name, field_value in state.items():
        if field_name != "messages":
            print(f"- {field_name}: {field_value}")
    print(f"################ PLAN NODE END #################{Style.RESET_ALL}")


    return state

class GenerationError(Exception):
    """Custom exception for generation-related errors."""
    pass


# def generation_node(state: State) -> State:
#     """Generates LaTeX document with proper image handling."""
#     print(f"{Fore.LIGHTGREEN_EX}################ GENERATION NODE BEGIN #################")
#     try:
#         # Initialize output directory
#         base_output_path = Path("C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/sagan_workflow/spaider_agent_temp/output_pdf")
#         base_output_path.mkdir(parents=True, exist_ok=True)
        
#         # Create images directory within output directory
#         images_dir = base_output_path / "images"
#         images_dir.mkdir(exist_ok=True)
        
#         # Process and copy images from section content
#         section_texts = state.get("section_answers", {})
#         processed_sections = {}
        
#         for section, answers in section_texts.items():
#             processed_answers = []
#             for answer in answers:
#                 content = answer.get('content', '')
#                 images = answer.get('images', [])
                
#                 # Process each image
#                 processed_images = []
#                 for idx, img_path in enumerate(images, 1):
#                     try:
#                         # Get source image path
#                         src_path = Path(img_path)
#                         if src_path.exists():
#                             # Create relative destination path
#                             dest_filename = f"{section.lower().replace(' ', '_')}_img_{idx}{src_path.suffix}"
#                             dest_path = images_dir / dest_filename
                            
#                             # Copy image file
#                             import shutil
#                             shutil.copy2(src_path, dest_path)
                            
#                             # Store relative path for LaTeX
#                             processed_images.append(f"images/{dest_filename}")
#                             print(f"Copied image: {src_path} -> {dest_path}")
#                     except Exception as e:
#                         print(f"Error processing image {img_path}: {e}")
                
#                 processed_answers.append({
#                     'content': content,
#                     'images': processed_images
#                 })
#             processed_sections[section] = processed_answers

#         # Create LLM prompt using the writer prompt template
#         content_prompt = SystemMessage(WRITER_PROMPT)
#         human_message = HumanMessage(content=f"""
#         Project Title: {state.get("project_title", "Research Project")}
        
#         Abstract: {state.get("abstract_text", "")}
        
#         Please generate a complete LaTeX document that:
#         1. Uses the LaTeX template provided in the system prompt
#         2. Incorporates the abstract and following content naturally
#         3. Adds appropriate transitions between sections
#         4. Uses relative paths for images
#         5. Maintains academic writing style and formatting
        
#         Section Content:
#         {json.dumps(processed_sections, indent=2)}
#         """)
        
#         # Generate content using LLM
#         messages = [content_prompt, human_message]
#         response = llm.invoke(messages)
#         latex_content = response.content
        
#         # Extract actual LaTeX content and any AI messages
#         latex_content, ai_message = extract_latex_and_message(latex_content)
        
#         # Save LaTeX file
#         tex_path = base_output_path / "output.tex"
#         tex_path.write_text(latex_content, encoding='utf-8')
#         print(f"LaTeX file written to: {tex_path}")
        
#         # Change to output directory for PDF generation
#         original_dir = os.getcwd()
#         os.chdir(str(base_output_path))
        
#         try:
#             # Try PDF generation with pdflatex first
#             success = latex_to_pdf("output.tex", str(base_output_path))
#             if not success:
#                 print("pdflatex failed, trying pandoc...")
#                 success = latex_to_pdf_pandoc("output.tex", str(base_output_path))
#         finally:
#             # Restore original directory
#             os.chdir(original_dir)
        
#         # Update state
#         pdf_path = base_output_path / "output.pdf"
#         if success and pdf_path.exists():
#             print(f"PDF generated successfully at: {pdf_path}")
#             state.update({
#                 "pdf_status": "success",
#                 "pdf_path": str(pdf_path),
#                 "generation_message": ai_message if ai_message else "Document generated successfully"
#             })
#         else:
#             print("PDF generation failed")
#             state.update({
#                 "pdf_status": "failed",
#                 "error": "PDF generation failed",
#                 "generation_message": ai_message if ai_message else "Error during PDF generation"
#             })
        
#         # Store latex content in state
#         state["draft"] = latex_content
        
#     except Exception as e:
#         print(f"Error in generation node: {e}")
#         state.update({
#             "error": str(e),
#             "pdf_status": "error",
#             "generation_message": f"Error during generation: {str(e)}"
#         })
    
#     print(f"################ GENERATION NODE END #################{Style.RESET_ALL}")
#     return state


def generation_node(state: State) -> State:
    """Generates LaTeX document based on plan and content with proper image handling."""
    print(f"{Fore.LIGHTGREEN_EX}################ GENERATION NODE BEGIN #################")
    try:
        # Initialize output directory
        base_output_path = Path("C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/sagan_workflow/spaider_agent_temp/output_pdf")
        base_output_path.mkdir(parents=True, exist_ok=True)
        
        # Create images directory in the same directory as tex file
        images_dir = base_output_path / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Process and copy images from section content
        section_texts = state.get("section_answers", {})
        processed_sections = {}
        image_mappings = []  # Keep track of all image paths
        
        for section, answers in section_texts.items():
            processed_answers = []
            for answer in answers:
                content = answer.get('content', '')
                images = answer.get('images', [])
                
                processed_images = []
                for idx, img_path in enumerate(images, 1):
                    try:
                        src_path = Path(img_path)
                        if src_path.exists():
                            # Create a standardized filename for the image
                            dest_filename = f"{section.lower().replace(' ', '_')}_img_{idx}{src_path.suffix}"
                            dest_path = images_dir / dest_filename
                            
                            # Copy the image
                            import shutil
                            shutil.copy2(src_path, dest_path)
                            
                            # Store the mapping of original to new path
                            image_mappings.append({
                                'original': str(src_path),
                                'new': f"images/{dest_filename}",
                                'caption': f"Figure related to {section}",
                                'label': f"fig:{section.lower().replace(' ', '_')}_{idx}"
                            })
                            
                            processed_images.append({
                                'path': f"images/{dest_filename}",
                                'caption': f"Figure related to {section}",
                                'label': f"fig:{section.lower().replace(' ', '_')}_{idx}"
                            })
                            print(f"Copied image: {src_path} -> {dest_path}")
                    except Exception as e:
                        print(f"Error processing image {img_path}: {e}")
                
                processed_answers.append({
                    'content': content,
                    'images': processed_images
                })
            processed_sections[section] = processed_answers

        # Get plan
        plan = state.get("plan", "")
        
        # Create LLM prompt with explicit image information
        content_prompt = SystemMessage(WRITER_PROMPT)
        human_message = HumanMessage(content=f"""
        Project Information:
        Title: {state.get("project_title", "Research Project")}
        Abstract: {state.get("abstract_text", "")}
        
        Document Plan:
        {plan}
        
        Section Content and Images:
        {json.dumps(processed_sections, indent=2)}
        
        Available Images:
        {json.dumps(image_mappings, indent=2)}
        
        Please generate a complete LaTeX document following the provided structure and content.
        For each image, use the exact path, caption, and label provided in the image mappings.
        Use this format for including images:
        
        \\begin{{figure}}[htbp]
            \\centering
            \\includegraphics[width=0.85\\textwidth]{{path}}
            \\caption{{caption}}
            \\label{{label}}
        \\end{{figure}}
        """)
        
        # Generate content using LLM
        messages = [content_prompt, human_message]
        response = llm.invoke(messages)
        latex_content = response.content
        
        # Extract actual LaTeX content and any AI messages
        latex_content, ai_message = extract_latex_and_message(latex_content)
        
        # Save LaTeX file
        tex_path = base_output_path / "output.tex"
        tex_path.write_text(latex_content, encoding='utf-8')
        print(f"LaTeX file written to: {tex_path}")
        
        # Change to output directory for PDF generation
        original_dir = os.getcwd()
        os.chdir(str(base_output_path))
        
        try:
            # Try PDF generation with pdflatex first
            success = latex_to_pdf("output.tex", str(base_output_path))
            if not success:
                print("pdflatex failed, trying pandoc...")
                success = latex_to_pdf_pandoc("output.tex", str(base_output_path))
                
            # Verify the PDF contains images
            if success:
                pdf_path = base_output_path / "output.pdf"
                if pdf_path.exists():
                    print("Successfully generated PDF with images")
                else:
                    print("PDF generation failed - file not found")
                    success = False
        finally:
            os.chdir(original_dir)
        
        # Update state
        pdf_path = base_output_path / "output.pdf"
        if success and pdf_path.exists():
            print(f"PDF generated successfully at: {pdf_path}")
            state.update({
                "pdf_status": "success",
                "pdf_path": str(pdf_path),
                "generation_message": ai_message if ai_message else "Document generated successfully"
            })
        else:
            print("PDF generation failed")
            state.update({
                "pdf_status": "failed",
                "error": "PDF generation failed",
                "generation_message": ai_message if ai_message else "Error during PDF generation"
            })
        
        # Store latex content in state
        state["draft"] = latex_content
        
    except Exception as e:
        print(f"Error in generation node: {e}")
        state.update({
            "error": str(e),
            "pdf_status": "error",
            "generation_message": f"Error during generation: {str(e)}"
        })
    
    print(f"################ GENERATION NODE END #################{Style.RESET_ALL}")
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

        # Iterate over each section and its questions
        for section, questions in section_questions.items():
            print(f"\nProcessing section: {section}")
            section_answers[section] = []
            
            for question in questions:
                print(f"\nQuerying for question: {question}")
                
                try:
                    # Use the multimodal_vectordb_query tool with correct parameters
                    results = multimodal_tool.multimodal_vectordb_query(
                        persist_dir="C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/ingest_data/astroai2",
                        query=question,
                        k=5
                    )
                    
                    print(f"Query results: {results}")
                    
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
                                print(f"Added answer entry with content length: {len(answer_entry['content'])}")
                                print(f"Number of images: {len(answer_entry['images'])}")
                    else:
                        print("No results found for query")
                        
                except Exception as query_error:
                    print(f"Error processing query: {query_error}")
                    continue

            # If no answers were found for the section, add a placeholder
            if not section_answers[section]:
                section_answers[section] = [{
                    "content": "No relevant information found.",
                    "images": []
                }]

            print(f"Completed answers for section: {section}")
            print(f"Number of answers: {len(section_answers[section])}")

        # Update state with the collected answers
        state["messages"].append(SystemMessage(content="Section-wise answers generated successfully"))
        state["section_answers"] = section_answers

        # Debug output
        print("\nFinal section answers structure:")
        for section, answers in section_answers.items():
            print(f"\nSection: {section}")
            print(f"Number of answers: {len(answers)}")
            for idx, answer in enumerate(answers):
                print(f"Answer {idx + 1} - Content length: {len(answer['content'])}")
                print(f"Number of images: {len(answer['images'])}")

        print(f"################ SECTION WISE ANSWERS GENERATOR END #################{Style.RESET_ALL}")
        return state

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"################ SECTION WISE ANSWERS GENERATOR END #################{Style.RESET_ALL}")
        state["messages"].append(str(e))
        state["section_answers"] = None
        return state

