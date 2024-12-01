from fastapi import FastAPI, HTTPException, WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
import uvicorn
import subprocess
import base64
from typing import Optional,Dict
import os
import asyncio
import json
import uuid
# Import LaTeX and Markdown conversion utilities
from utils.latex_to_markdown import create_markdown_pipeline
from utils.latextopdf import LaTeXPipeline
from nodes_and_conditional_edges.nodes import ws_manager,research_query_generator
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from models.chatgroq import BuildChatGroq, BuildChatOpenAI
# LOCAL IMPORTS
from graph import create_graph, compile_graph, print_stream
from schemas import State
from prompts.prompts import RESEARCH_QUERY_GENERATOR_PROMPT

# Update UserInput model to include human input fields
class UserInput(BaseModel):
    message: str
    section_number: Optional[int] = None


MODEL = "gpt-4o"
# llm = BuildChatGroq(model=MODEL, temperature=0)
llm = BuildChatOpenAI(model=MODEL, temperature=0)
# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize paths and configurations
DATA_FOLDER = Path("testfolder")
DATA_FOLDER.mkdir(exist_ok=True)

DATA_RFP_FOLDER = Path("testfolder")
DATA_RFP_FOLDER.mkdir(exist_ok=True)

# Initialize graph
verbose = True
builder = create_graph()
graph = compile_graph(builder)

# Configure runnable
config = RunnableConfig(
    recursion_limit=50,
    configurable={"thread_id": "1"}
)





def extract_section(draft_path: str, section_number: int) -> tuple[str, str]:
    """
    Extract section title and text from a LaTeX file based on section number.
    Returns a tuple of (section_title, section_text).
    """
    import re

    def clean_latex_command(text: str) -> str:
        """Remove LaTeX commands from text while preserving content."""
        # Remove comments
        text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        # Remove specific LaTeX commands while keeping their content
        text = re.sub(r'\\textbf{(.*?)}', r'\1', text)
        text = re.sub(r'\\textit{(.*?)}', r'\1', text)
        text = re.sub(r'\\emph{(.*?)}', r'\1', text)
        return text.strip()

    try:
        with open(draft_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Extract content between \begin{document} and \end{document}
        doc_match = re.search(r'\\begin{document}(.*?)\\end{document}', content, re.DOTALL)
        if not doc_match:
            raise ValueError("Could not find document environment in LaTeX file")
        
        main_content = doc_match.group(1)

        # Find all sections
        sections = []
        section_titles = []
        
        # Regular expression for section commands
        section_pattern = r'\\section\{([^}]+)\}'
        
        # Find all section positions
        section_matches = list(re.finditer(section_pattern, main_content))
        
        if not section_matches:
            # Handle case with no sections
            return "", clean_latex_command(main_content)
        
        # Process each section
        for i, match in enumerate(section_matches):
            section_start = match.start()
            section_end = section_matches[i + 1].start() if i < len(section_matches) - 1 else len(main_content)
            
            # Extract title and content
            section_content = main_content[section_start:section_end]
            title_match = re.search(section_pattern, section_content)
            
            if title_match:
                title = clean_latex_command(title_match.group(1))
                # Get content after the section command
                content_start = title_match.end()
                content = section_content[content_start:].strip()
                
                section_titles.append(title)
                sections.append(clean_latex_command(content))

        # Validate section number
        if section_number < 1 or section_number > len(sections):
            raise ValueError(f"Section number {section_number} is out of range. File has {len(sections)} sections.")

        # Get the requested section
        section_index = section_number - 1
        return section_titles[section_index], sections[section_index]

    except FileNotFoundError:
        raise FileNotFoundError(f"LaTeX file not found: {draft_path}")
    except Exception as e:
        raise ValueError(f"Error processing LaTeX file: {str(e)}")
    
# @app.websocket("/ws/{session_id}")
# async def websocket_endpoint(websocket: WebSocket, session_id: str):
#     await ws_manager.connect(websocket, session_id)
#     try:
#         print("142")
#         while True:
#             # data = await websocket.receive_json()
#             # if "type" in data and data["type"] == "USER_RESPONSE":

#             #     ws_manager.set_user_response(session_id, data["response"])
#             # # if data["typed"] == "USER_RESPONSE":
#             # else:
#             #     res =  await ws_manager.wait_for_response(session_id)
#             #     print(res,"res 155")
#             message = await ws_manager.receive_text(session_id)
#             print('custom',message)
                
#     except WebSocketDisconnect:
#         ws_manager.disconnect(session_id)
#     except Exception as e:
#         print(f"WebSocket error: {e}")
#         ws_manager.disconnect(session_id)



@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket API that allows clients to connect with a session_id."""
    await ws_manager.connect(websocket, session_id)
    try:
        print('try block')
        while True:
            message = await ws_manager.receive_message(session_id)
            # if message:
            #     await ws_manager.send_message(session_id, f"Echo: {message}")
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)

# @app.post("/process-input")
# async def process_input(user_input: UserInput,websocket: WebSocket):
#     try:
#         await websocket.accept()

#         output_dir = Path("C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/sagan_workflow/spaider_agent_temp/output_pdf")
#         tex_file = output_dir / "output.tex"
#         pdf_file = output_dir / "output.pdf"
#         md_file = output_dir / "output.md"

#         # Ensure output directory exists
#         output_dir.mkdir(parents=True, exist_ok=True)

#         # Initialize the state
#         state = {
#             "messages": [
#                 {"type": "system", "content": "Research query generator initialized."},
#                 {"type": "user", "content": user_input.message}
#             ]
#         }

#         # Extract section if section number and draft path are provided
#         if user_input.section_number:
#             draft_path = tex_file  # Now using tex_file as draft path
#             s_title, s_text = extract_section(str(draft_path), user_input.section_number)
#             research_query_generator_prompt = RESEARCH_QUERY_GENERATOR_PROMPT.format(
#                 section_title=s_title,
#                 section_text=s_text
#             )
            
#             initial_input = {
#                 "messages": [
#                     SystemMessage(content=research_query_generator_prompt),
#                     HumanMessage(content=user_input.message)
#                 ],
#                 "section_text": s_text,
#                 "section_title": s_title,
#                 "section_number": user_input.section_number,
#                 "rough_draft_path": str(draft_path)
#             }
#         else:
#             initial_input = {"messages": [("user", user_input.message)]}

#         # Process through graph and capture the final state
#         state = None
#         try:
#             # Collect all outputs from the graph stream
#             outputs = list(graph.stream(
#                 initial_input,
#                 stream_mode="values",
#                 config=config
#             ))
            
#             # Get the final state from the last output
#             if outputs:
#                 state = outputs[-1]
                
#                 # Debug logging
#                 print("\nState after graph processing:")
#                 print(f'State: {state}')
#                 print(f"AI Message in state: {state.get('ai_message')}")
#                 print(f"Modified text in state: {bool(state.get('modified_section_text'))}")

#             if not state:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="No state returned from graph processing"
#                 )
            

#             llm_response = llm.invoke(state["messages"])
#             if not llm_response or not hasattr(llm_response, 'content'):
#                 raise ValueError("Invalid response from LLM.")
#             initial_queries = json.loads(llm_response.content).get("research_queries", [])

#         # Gather user inputs via WebSocket for query modification
#             modified_queries = await gather_user_inputs(websocket, initial_queries)

#         # Process the state and queries synchronously
#             state = research_query_generator(state, modified_queries)

#         # Send the final state back to the client
#             await websocket.send_json({
#             "type": "final_state",
#             "content": state
#             })

#             # return JSONResponse({"success": True, "state": state})

#             # Build initial response data with default values
#             response_data = {
#                 "success": True,
#                 "message": "Processing completed",
#                 "ai_message": state.get("ai_message"),
#                 "modified_section_text": state.get("modified_section_text")
#             }

#             print("\nConstructing response with state data:")
#             print(f"AI Message: {response_data['ai_message']}")
#             print(f"Modified text present: {bool(response_data['modified_section_text'])}")

#             # If save was successful and we need to process files
#             if response_data.get("success"):  # Changed condition here
#                 print("Save was successful, processing PDF and Markdown conversions...")

#                 # Run pdflatex multiple times to resolve references
#                 # for i in range(3):
#                 #     try:
#                 #         process = subprocess.run([
#                 #             'pdflatex',
#                 #             '-interaction=nonstopmode',
#                 #             f'-output-directory={str(output_dir)}',
#                 #             str(tex_file)
#                 #         ], check=True, capture_output=True, text=True)
#                 #         print(f"PDFLaTeX run {i+1} completed")


#                 #     except subprocess.CalledProcessError as e:
#                 #         print(f"PDFLaTeX error on run {i+1}: {e.stderr}")
#                 #         raise HTTPException(
#                 #             status_code=500,
#                 #             detail=f"PDFLaTeX compilation failed on run {i+1}"
#                 #         )

#                 print(f"Looking for PDF file at: {pdf_file}")
#                 print(f"Files in output directory: {list(output_dir.glob('*'))}")

#                 # Verify files exist
#                 if not tex_file.exists():
#                     print(f"TeX file missing at: {tex_file}")
#                     raise HTTPException(
#                         status_code=404,
#                         detail="LaTeX file not found after compilation"
#                     )

#                 if not pdf_file.exists():
#                     print(f"PDF file missing at: {pdf_file}")
#                     raise HTTPException(
#                         status_code=404,
#                         detail="PDF file not generated successfully"
#                     )

#                 print("Both files exist, proceeding with markdown conversion")

#                 # Convert to Markdown
#                 md_pipeline = create_markdown_pipeline()
#                 md_result = md_pipeline.convert_latex_to_markdown(str(tex_file), str(output_dir))

#                 try:
#                     # Read LaTeX content
#                     with open(tex_file, 'r', encoding='utf-8') as f:
#                         latex_content = f.read()
#                     print("Successfully read LaTeX content")

#                     # Read PDF content
#                     with open(pdf_file, 'rb') as f:
#                         pdf_content = base64.b64encode(f.read()).decode('utf-8')
#                     print("Successfully read PDF content")

#                     # Handle Markdown content
#                     markdown_content = None
#                     if md_result["success"]:
#                         markdown_content = md_result["markdown_content"]
#                         # Save to file
#                         with open(md_file, 'w', encoding='utf-8') as f:
#                             f.write(markdown_content)
#                         print("Successfully created Markdown file")

#                     # Update response data with file information
#                     response_data.update({
#                         "tex_file": latex_content,
#                         "pdf_file": pdf_content,
#                         "md_file": markdown_content,
#                         "file_paths": {
#                             "tex": str(tex_file),
#                             "pdf": str(pdf_file),
#                             "md": str(md_file) if markdown_content else None
#                         }
#                     })

#                     if not markdown_content:
#                         response_data["markdown_error"] = md_result.get("error", "Unknown conversion error")
#                         print(f"Markdown conversion failed: {response_data['markdown_error']}")

#                     # Clean up auxiliary files
#                     aux_extensions = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
#                     for ext in aux_extensions:
#                         aux_file = output_dir / f"output{ext}"
#                         if aux_file.exists():
#                             aux_file.unlink()
#                     print("Cleaned up auxiliary files")

#                 except Exception as e:
#                     print(f"Error processing output files: {str(e)}")
#                     raise HTTPException(
#                         status_code=500,
#                         detail=f"Error processing output files: {str(e)}"
#                     )

#             else:
#                 print("No file processing needed or save was not successful")

#             # Final debug logging
#             print("\nFinal response data:")
#             print(f"AI Message: {response_data['ai_message']}")
#             print(f"Modified text present: {bool(response_data.get('modified_section_text'))}")
            
#             return JSONResponse(response_data)

#         except Exception as e:
#             print(f"Error in process-input: {str(e)}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error in process-input: {str(e)}"
#             )

#     except Exception as e:
#         print(f"Error in outer process-input: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error in process-input endpoint: {str(e)}"
#         )


# @app.post("/process-input")
# async def process_input(user_input: UserInput):
#     try:
#         # Accept WebSocket connection
        

#         # Set up paths for file handling
#         output_dir = Path("C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/sagan_workflow/spaider_agent_temp/output_pdf")
#         tex_file = output_dir / "output.tex"
#         pdf_file = output_dir / "output.pdf"
#         md_file = output_dir / "output.md"

#         # Ensure the output directory exists
#         output_dir.mkdir(parents=True, exist_ok=True)

#         # Initialize the state
#         state = {
#             "messages": [
#                 {"type": "system", "content": "Research query generator initialized."},
#                 {"type": "user", "content": user_input.message}
#             ]
#         }

#         # Handle section extraction if a section number is provided
#         if user_input.section_number:
#             draft_path = tex_file  # Using tex_file as the draft path
#             s_title, s_text = extract_section(str(draft_path), user_input.section_number)
#             research_query_generator_prompt = RESEARCH_QUERY_GENERATOR_PROMPT.format(
#                 section_title=s_title,
#                 section_text=s_text
#             )
            
#             # Prepare initial input for graph processing
#             initial_input = {
#                 "messages": [
#                     SystemMessage(content=research_query_generator_prompt),
#                     HumanMessage(content=user_input.message)
#                 ],
#                 "section_text": s_text,
#                 "section_title": s_title,
#                 "section_number": user_input.section_number,
#                 "rough_draft_path": str(draft_path)
#             }
#         else:
#             # Default input if no section is provided
#             initial_input = {"messages": [("user", user_input.message)]}

#         # Process through the graph and capture the state
#         outputs = []
#         try:
#             outputs = list(graph.stream(
#                 initial_input,
#                 stream_mode="values",
#                 config=config
#             ))
#         except Exception as e:
#             print(f"Error in graph processing: {e}")
#             raise HTTPException(status_code=500, detail="Error during graph processing.")

#         # Get the final state from graph outputs
#         if outputs:
#             state = outputs[-1]
#         else:
#             raise HTTPException(status_code=500, detail="No output from graph processing.")

#         # Extract queries from LLM if applicable
#         llm_response = llm.invoke(state["messages"])
#         if not llm_response or not hasattr(llm_response, 'content'):
#             raise ValueError("Invalid response from LLM.")
#         initial_queries = json.loads(llm_response.content).get("research_queries", [])

#         # Gather user inputs via WebSocket for query modification
#         modified_queries = await gather_user_inputs(websocket, initial_queries)

#         # Process the state and queries synchronously
#         state = research_query_generator(state, modified_queries)

#         # Build initial response data with default values
#         response_data = {
#             "success": True,
#             "message": "Processing completed",
#             "ai_message": state.get("ai_message"),
#             "modified_section_text": state.get("modified_section_text"),
#         }

#         print("\nConstructing response with state data:")
#         print(f"AI Message: {response_data['ai_message']}")
#         print(f"Modified text present: {bool(response_data['modified_section_text'])}")

#         # Finalize and send response to the WebSocket client
#         await websocket.send_json({
#             "type": "final_state",
#             "content": response_data
#         })

#         return JSONResponse({"success": True, "response": response_data})

#     except Exception as e:
#         # Handle errors and send an error message via WebSocket
#         await websocket.send_json({
#             "type": "error",
#             "content": f"Error in process-input: {str(e)}"
#         })
#         raise HTTPException(status_code=500, detail=f"Error in process-input: {str(e)}")

    

    # orioginal code below
# @app.post("/process-input")
# async def process_input(user_input: UserInput):
#     try:
#         # session_id = str(uuid.uuid4())
#         # await ws_manager.send_message(session_id,{
#         #     "message":"hey"
#         # })
#         # Default paths and configurations using Path objects

#         # await ws_manager.send_message("1234",{
#         #     "type":"question",
#         #     "data":"would you like too ?"
#         # })

#         # response = await ws_manager.wait_for_response("1234")
#         # print(response)
#         output_dir = Path("C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/sagan_workflow/spaider_agent_temp/output_pdf")
#         tex_file = output_dir / "output.tex"
#         pdf_file = output_dir / "output.pdf"
#         md_file = output_dir / "output.md"

#         # Ensure output directory exists
#         output_dir.mkdir(parents=True, exist_ok=True)

#         # Extract section if section number and draft path are provided
#         if user_input.section_number:
#             draft_path = tex_file  # Now using tex_file as draft path
#             s_title, s_text = extract_section(str(draft_path), user_input.section_number)
#             research_query_generator_prompt = RESEARCH_QUERY_GENERATOR_PROMPT.format(
#                 section_title=s_title,
#                 section_text=s_text
#             )
            
#             initial_input = {
#                 "messages": [
#                     SystemMessage(content=research_query_generator_prompt),
#                     HumanMessage(content=user_input.message)
#                 ],
#                 "section_text": s_text,
#                 "section_title": s_title,
#                 "section_number": user_input.section_number,
#                 "rough_draft_path": str(draft_path)
#             }
#         else:
#             initial_input = {"messages": [("user", user_input.message)]}

#         # Process through graph and capture the final state
#         state = None
#         try:
#             # Collect all outputs from the graph stream
#             # outputs = list(graph.stream(
#             #     initial_input,
#             #     stream_mode="values",
#             #     config=config
#             # ))


#             async for output in graph.astream(
#                 initial_input,
#                 stream_mode="values",
#                 config=config
#             ):
#                 state = output  # Capture the last state

#             if not state:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="No state returned from graph processing"
#                 )
            
#             # Get the final state from the last output
#             # if outputs:
#             #     state = outputs[-1]
                
#                 # Debug logging
#                 print("\nState after graph processing:")
#                 print(f'State: {state}')
#                 print(f"AI Message in state: {state.get('ai_message')}")
#                 print(f"Modified text in state: {bool(state.get('modified_section_text'))}")

#             if not state:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="No state returned from graph processing"
#                 )

#             # Build initial response data with default values
#             response_data = {
#                 "success": True,
#                 "message": "Processing completed",
#                 "ai_message": state.get("ai_message"),
#                 "modified_section_text": state.get("modified_section_text")
#             }

#             print("\nConstructing response with state data:")
#             print(f"AI Message: {response_data['ai_message']}")
#             print(f"Modified text present: {bool(response_data['modified_section_text'])}")

#             # If save was successful and we need to process files
#             if response_data.get("success"):  # Changed condition here
#                 print("Save was successful, processing PDF and Markdown conversions...")

#                 # Run pdflatex multiple times to resolve references
#                 # for i in range(3):
#                 #     try:
#                 #         process = subprocess.run([
#                 #             'pdflatex',
#                 #             '-interaction=nonstopmode',
#                 #             f'-output-directory={str(output_dir)}',
#                 #             str(tex_file)
#                 #         ], check=True, capture_output=True, text=True)
#                 #         print(f"PDFLaTeX run {i+1} completed")


#                 #     except subprocess.CalledProcessError as e:
#                 #         print(f"PDFLaTeX error on run {i+1}: {e.stderr}")
#                 #         raise HTTPException(
#                 #             status_code=500,
#                 #             detail=f"PDFLaTeX compilation failed on run {i+1}"
#                 #         )

#                 print(f"Looking for PDF file at: {pdf_file}")
#                 print(f"Files in output directory: {list(output_dir.glob('*'))}")

#                 # Verify files exist
#                 if not tex_file.exists():
#                     print(f"TeX file missing at: {tex_file}")
#                     raise HTTPException(
#                         status_code=404,
#                         detail="LaTeX file not found after compilation"
#                     )

#                 if not pdf_file.exists():
#                     print(f"PDF file missing at: {pdf_file}")
#                     raise HTTPException(
#                         status_code=404,
#                         detail="PDF file not generated successfully"
#                     )

#                 print("Both files exist, proceeding with markdown conversion")

#                 # Convert to Markdown
#                 md_pipeline = create_markdown_pipeline()
#                 md_result = md_pipeline.convert_latex_to_markdown(str(tex_file), str(output_dir))

#                 try:
#                     # Read LaTeX content
#                     with open(tex_file, 'r', encoding='utf-8') as f:
#                         latex_content = f.read()
#                     print("Successfully read LaTeX content")

#                     # Read PDF content
#                     with open(pdf_file, 'rb') as f:
#                         pdf_content = base64.b64encode(f.read()).decode('utf-8')
#                     print("Successfully read PDF content")

#                     # Handle Markdown content
#                     markdown_content = None
#                     if md_result["success"]:
#                         markdown_content = md_result["markdown_content"]
#                         # Save to file
#                         with open(md_file, 'w', encoding='utf-8') as f:
#                             f.write(markdown_content)
#                         print("Successfully created Markdown file")

#                     # Update response data with file information
#                     response_data.update({
#                         "tex_file": latex_content,
#                         "pdf_file": pdf_content,
#                         "md_file": markdown_content,
#                         "file_paths": {
#                             "tex": str(tex_file),
#                             "pdf": str(pdf_file),
#                             "md": str(md_file) if markdown_content else None
#                         }
#                     })

#                     if not markdown_content:
#                         response_data["markdown_error"] = md_result.get("error", "Unknown conversion error")
#                         print(f"Markdown conversion failed: {response_data['markdown_error']}")

#                     # Clean up auxiliary files
#                     aux_extensions = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
#                     for ext in aux_extensions:
#                         aux_file = output_dir / f"output{ext}"
#                         if aux_file.exists():
#                             aux_file.unlink()
#                     print("Cleaned up auxiliary files")

#                 except Exception as e:
#                     print(f"Error processing output files: {str(e)}")
#                     raise HTTPException(
#                         status_code=500,
#                         detail=f"Error processing output files: {str(e)}"
#                     )

#             else:
#                 print("No file processing needed or save was not successful")

#             # Final debug logging
#             print("\nFinal response data:")
#             print(f"AI Message: {response_data['ai_message']}")
#             print(f"Modified text present: {bool(response_data.get('modified_section_text'))}")
            
#             return JSONResponse(response_data)

#         except Exception as e:
#             print(f"Error in process-input: {str(e)}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error in process-input: {str(e)}"
#             )

#     except Exception as e:
#         print(f"Error in outer process-input: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error in process-input endpoint: {str(e)}"
#         )

# the one im workign right now below 
# @app.post("/process-input")
# async def process_input(user_input: UserInput,websocket: WebSocket):
#     try:
#         session_id = str(uuid.uuid4())
#         await ws_manager.connect(websocket, session_id)
#         # await ws_manager.send_message(session_id,{
#         #     "message":"hey"
#         # })
#         # Default paths and configurations using Path objects

#         # await ws_manager.send_message("1234",{
#         #     "type":"question",
#         #     "data":"would you like too ?"
#         # })

#         # response = await ws_manager.wait_for_response("1234")
#         # print(response)
#         output_dir = Path("C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/sagan_workflow/spaider_agent_temp/output_pdf")
#         tex_file = output_dir / "output.tex"
#         pdf_file = output_dir / "output.pdf"
#         md_file = output_dir / "output.md"

#         # Ensure output directory exists
#         output_dir.mkdir(parents=True, exist_ok=True)

#         # Extract section if section number and draft path are provided
#         if user_input.section_number:
#             draft_path = tex_file  # Now using tex_file as draft path
#             s_title, s_text = extract_section(str(draft_path), user_input.section_number)
#             research_query_generator_prompt = RESEARCH_QUERY_GENERATOR_PROMPT.format(
#                 section_title=s_title,
#                 section_text=s_text
#             )
            
#             initial_input = {
#                 "messages": [
#                     SystemMessage(content=research_query_generator_prompt),
#                     HumanMessage(content=user_input.message)
#                 ],
#                 "section_text": s_text,
#                 "section_title": s_title,
#                 "section_number": user_input.section_number,
#                 "rough_draft_path": str(draft_path)
#             }
#         else:
#             initial_input = {"messages": [("user", user_input.message)]}

#         # Process through graph and capture the final state
#         state = None
#         try:
#             # Collect all outputs from the graph stream
#             # outputs = list(graph.stream(
#             #     initial_input,
#             #     stream_mode="values",
#             #     config=config
#             # ))


#             async for output in graph.astream(
#                 initial_input,
#                 stream_mode="values",
#                 config=config
#             ):
#                 state = output  # Capture the last state

#             if not state:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="No state returned from graph processing"
#                 )
            
#             # Get the final state from the last output
#             # if outputs:
#             #     state = outputs[-1]
                
#                 # Debug logging
#                 print("\nState after graph processing:")
#                 print(f'State: {state}')
#                 print(f"AI Message in state: {state.get('ai_message')}")
#                 print(f"Modified text in state: {bool(state.get('modified_section_text'))}")

#             if not state:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="No state returned from graph processing"
#                 )

#             # Build initial response data with default values
#             response_data = {
#                 "success": True,
#                 "message": "Processing completed",
#                 "ai_message": state.get("ai_message"),
#                 "modified_section_text": state.get("modified_section_text")
#             }

#             print("\nConstructing response with state data:")
#             print(f"AI Message: {response_data['ai_message']}")
#             print(f"Modified text present: {bool(response_data['modified_section_text'])}")

#             # If save was successful and we need to process files
#             if response_data.get("success"):  # Changed condition here
#                 print("Save was successful, processing PDF and Markdown conversions...")

#                 # Run pdflatex multiple times to resolve references
#                 # for i in range(3):
#                 #     try:
#                 #         process = subprocess.run([
#                 #             'pdflatex',
#                 #             '-interaction=nonstopmode',
#                 #             f'-output-directory={str(output_dir)}',
#                 #             str(tex_file)
#                 #         ], check=True, capture_output=True, text=True)
#                 #         print(f"PDFLaTeX run {i+1} completed")


#                 #     except subprocess.CalledProcessError as e:
#                 #         print(f"PDFLaTeX error on run {i+1}: {e.stderr}")
#                 #         raise HTTPException(
#                 #             status_code=500,
#                 #             detail=f"PDFLaTeX compilation failed on run {i+1}"
#                 #         )

#                 print(f"Looking for PDF file at: {pdf_file}")
#                 print(f"Files in output directory: {list(output_dir.glob('*'))}")

#                 # Verify files exist
#                 if not tex_file.exists():
#                     print(f"TeX file missing at: {tex_file}")
#                     raise HTTPException(
#                         status_code=404,
#                         detail="LaTeX file not found after compilation"
#                     )

#                 if not pdf_file.exists():
#                     print(f"PDF file missing at: {pdf_file}")
#                     raise HTTPException(
#                         status_code=404,
#                         detail="PDF file not generated successfully"
#                     )

#                 print("Both files exist, proceeding with markdown conversion")

#                 # Convert to Markdown
#                 md_pipeline = create_markdown_pipeline()
#                 md_result = md_pipeline.convert_latex_to_markdown(str(tex_file), str(output_dir))

#                 try:
#                     # Read LaTeX content
#                     with open(tex_file, 'r', encoding='utf-8') as f:
#                         latex_content = f.read()
#                     print("Successfully read LaTeX content")

#                     # Read PDF content
#                     with open(pdf_file, 'rb') as f:
#                         pdf_content = base64.b64encode(f.read()).decode('utf-8')
#                     print("Successfully read PDF content")

#                     # Handle Markdown content
#                     markdown_content = None
#                     if md_result["success"]:
#                         markdown_content = md_result["markdown_content"]
#                         # Save to file
#                         with open(md_file, 'w', encoding='utf-8') as f:
#                             f.write(markdown_content)
#                         print("Successfully created Markdown file")

#                     # Update response data with file information
#                     response_data.update({
#                         "tex_file": latex_content,
#                         "pdf_file": pdf_content,
#                         "md_file": markdown_content,
#                         "file_paths": {
#                             "tex": str(tex_file),
#                             "pdf": str(pdf_file),
#                             "md": str(md_file) if markdown_content else None
#                         }
#                     })

#                     if not markdown_content:
#                         response_data["markdown_error"] = md_result.get("error", "Unknown conversion error")
#                         print(f"Markdown conversion failed: {response_data['markdown_error']}")

#                     # Clean up auxiliary files
#                     aux_extensions = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
#                     for ext in aux_extensions:
#                         aux_file = output_dir / f"output{ext}"
#                         if aux_file.exists():
#                             aux_file.unlink()
#                     print("Cleaned up auxiliary files")

#                 except Exception as e:
#                     print(f"Error processing output files: {str(e)}")
#                     raise HTTPException(
#                         status_code=500,
#                         detail=f"Error processing output files: {str(e)}"
#                     )

#             else:
#                 print("No file processing needed or save was not successful")

#             # Final debug logging
#             print("\nFinal response data:")
#             print(f"AI Message: {response_data['ai_message']}")
#             print(f"Modified text present: {bool(response_data.get('modified_section_text'))}")
            
#             return JSONResponse(response_data)

#         except Exception as e:
#             print(f"Error in process-input: {str(e)}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error in process-input: {str(e)}"
#             )

#     except Exception as e:
#         print(f"Error in outer process-input: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error in process-input endpoint: {str(e)}"
#         )



# new one 

@app.post("/process-input")
async def process_input(user_input: UserInput):
    try:
        # Step 1: Generate a session ID and connect WebSocket
        session_id = "1234"
        # await ws_manager.connect(session_id,{
        #    "message":"hey  from 943"
        # })

        # Step 2: Default paths and configurations
        output_dir = Path("C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/sagan_workflow/spaider_agent_temp/output_pdf")
        tex_file = output_dir / "output.tex"
        pdf_file = output_dir / "output.pdf"
        md_file = output_dir / "output.md"
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Extract section if section number and draft path are provided
        if user_input.section_number:
            draft_path = tex_file  # Using tex_file as draft path
            s_title, s_text = extract_section(str(draft_path), user_input.section_number)
            research_query_generator_prompt = RESEARCH_QUERY_GENERATOR_PROMPT.format(
                section_title=s_title,
                section_text=s_text
            )

            initial_input = {
                "messages": [
                    SystemMessage(content=research_query_generator_prompt),
                    HumanMessage(content=user_input.message)
                ],
                "section_text": s_text,
                "section_title": s_title,
                "section_number": user_input.section_number,
                "rough_draft_path": str(draft_path)
            }
        else:
            initial_input = {"messages": [("user", user_input.message)]}

        # Step 4: Process through graph and capture the final state
        state = None
        try:
            async for output in graph.astream(
                initial_input,
                stream_mode="values",
                config=config
            ):
                state = output  # Capture the last state

                # WebSocket: Send progress updates
                # await websocket.send_json({"type": "progress", "content": state})

            if not state:
                raise HTTPException(
                    status_code=500,
                    detail="No state returned from graph processing"
                )

            # Debug logging
            print("\nState after graph processing:")
            print(f"State: {state}")
            print(f"AI Message in state: {state.get('ai_message')}")
            print(f"Modified text in state: {bool(state.get('modified_section_text'))}")

            # Step 5: Build initial response data
            response_data = {
                "success": True,
                "message": "Processing completed",
                "ai_message": state.get("ai_message"),
                "modified_section_text": state.get("modified_section_text")
            }

            # WebSocket: Send final state
            # await websocket.send_json({"type": "final_state", "content": response_data})

            print("\nConstructing response with state data:")
            print(f"AI Message: {response_data['ai_message']}")
            print(f"Modified text present: {bool(response_data['modified_section_text'])}")

            # Step 6: Handle file processing for successful state
            if response_data.get("success"):
                print("Save was successful, processing PDF and Markdown conversions...")

                # Verify files exist
                if not tex_file.exists():
                    print(f"TeX file missing at: {tex_file}")
                    raise HTTPException(
                        status_code=404,
                        detail="LaTeX file not found after compilation"
                    )

                if not pdf_file.exists():
                    print(f"PDF file missing at: {pdf_file}")
                    raise HTTPException(
                        status_code=404,
                        detail="PDF file not generated successfully"
                    )

                print("Both files exist, proceeding with markdown conversion")

                # Convert to Markdown
                md_pipeline = create_markdown_pipeline()
                md_result = md_pipeline.convert_latex_to_markdown(str(tex_file), str(output_dir))

                try:
                    # Read LaTeX content
                    with open(tex_file, 'r', encoding='utf-8') as f:
                        latex_content = f.read()
                    print("Successfully read LaTeX content")

                    # Read PDF content
                    with open(pdf_file, 'rb') as f:
                        pdf_content = base64.b64encode(f.read()).decode('utf-8')
                    print("Successfully read PDF content")

                    # Handle Markdown content
                    markdown_content = None
                    if md_result["success"]:
                        markdown_content = md_result["markdown_content"]
                        # Save to file
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)
                        print("Successfully created Markdown file")

                    # Update response data with file information
                    response_data.update({
                        "tex_file": latex_content,
                        "pdf_file": pdf_content,
                        "md_file": markdown_content,
                        "file_paths": {
                            "tex": str(tex_file),
                            "pdf": str(pdf_file),
                            "md": str(md_file) if markdown_content else None
                        }
                    })

                    if not markdown_content:
                        response_data["markdown_error"] = md_result.get("error", "Unknown conversion error")
                        print(f"Markdown conversion failed: {response_data['markdown_error']}")

                    # Clean up auxiliary files
                    aux_extensions = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
                    for ext in aux_extensions:
                        aux_file = output_dir / f"output{ext}"
                        if aux_file.exists():
                            aux_file.unlink()
                    print("Cleaned up auxiliary files")

                except Exception as e:
                    print(f"Error processing output files: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error processing output files: {str(e)}"
                    )
            else:
                print("No file processing needed or save was not successful")

            # Final debug logging
            print("\nFinal response data:")
            print(f"AI Message: {response_data['ai_message']}")
            print(f"Modified text present: {bool(response_data.get('modified_section_text'))}")

            return JSONResponse(response_data)

        except Exception as e:
            print(f"Error in process-input: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in process-input: {str(e)}"
            )

    except Exception as e:
        print(f"Error in outer process-input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in process-input endpoint: {str(e)}"
        )

    # finally:
    #     # Ensure WebSocket disconnects
    #     ws_manager.disconnect(session_id)





@app.post("/test-websocket")
async def test_websocket():
    try:
     await ws_manager.send_message("1234",{
        "type":"question1",
        "data":"Would you like to modify or add queries? (yes/no)"
    })
    except Exception as e:
        print(f"Error in test-websocket: {str(e)}")






@app.post("/interact")
async def interact(user_input: UserInput):
    """
    Endpoint to interact with the graph using user input with streaming response.
    """
    if not user_input.message:
        raise HTTPException(status_code=400, detail="No input provided")

    try:
        # Stream the responses from the graph
        async def event_generator():
            initial_input = {"messages": [("user", user_input.message)]}
            for response in graph.stream(initial_input, stream_mode="values", config=config):
                yield f"data: {response}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)






