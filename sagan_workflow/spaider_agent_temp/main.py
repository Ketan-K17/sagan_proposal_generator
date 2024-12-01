# from langchain_core.runnables.config import RunnableConfig
# # LOCAL IMPORTS.
# from graph import create_graph, compile_graph, print_stream
# import os 
# # api handling imports.
# from fastapi import FastAPI,File, UploadFile,HTTPException, Request
# from pydantic import BaseModel
# from fastapi.responses import StreamingResponse, JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# import os
# from pathlib import Path
# from pypdf import PdfReader
# import uvicorn
# import base64
# import subprocess



# app = FastAPI()
# class UserInput(BaseModel):
#     message: str

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# DATA_FOLDER = Path("testfolder")
# DATA_FOLDER.mkdir(exist_ok=True)

# DATA_RFP_FOLDER = Path("testfolder")
# DATA_RFP_FOLDER.mkdir(exist_ok=True)

# verbose = True
# builder = create_graph()
# graph = compile_graph(builder)

# config = RunnableConfig(
#     recursion_limit=50,
#     configurable={"thread_id": "1"}
# )


# class UserInput(BaseModel):
#     message: str
    
    
# @app.post("/process-input")
# async def process_input(user_input: UserInput):
#     try:   
#         print(f"Processing input: {user_input.message}")
        
#         # Run the graph with the input
#         _ = list(graph.stream(
#             {"messages": [("user", user_input.message)]}, 
#             stream_mode="values", 
#             config=config
#         ))

#         # Get the file paths
#         project_root = Path(__file__).parent.parent
#         output_dir = project_root / "spaider_agent_temp" / "output_pdf"
#         tex_file = output_dir / "output.tex"
#         pdf_file = output_dir / "output.pdf"
#         md_file = output_dir / "output.md"  # Define markdown file path
        
#         # Ensure output directory exists
#         output_dir.mkdir(parents=True, exist_ok=True)

#         try:
#             # First check if the tex file exists
#             if not tex_file.exists():
#                 raise HTTPException(
#                     status_code=404,
#                     detail=f"LaTeX file not found at {tex_file}"
#                 )

#             print(f"Found LaTeX file at: {tex_file}")

#             # Run pdflatex multiple times to resolve references
#             # for i in range(3):
#             #     process = subprocess.run([
#             #         'pdflatex',
#             #         '-interaction=nonstopmode',
#             #         f'-output-directory={str(output_dir)}',
#             #         str(tex_file)
#             #     ], check=True, capture_output=True, text=True)
#             #     print(f"PDFLaTeX run {i+1} completed")

#             print(f"Looking for PDF file at: {pdf_file}")

#             # Additional debug information
#             print(f"Files in output directory: {list(output_dir.glob('*'))}")

#             # Check files with detailed logging
#             if not tex_file.exists():
#                 print(f"TeX file missing at: {tex_file}")
#                 raise HTTPException(
#                     status_code=404,
#                     detail="LaTeX file not found after compilation"
#                 )

#             if not pdf_file.exists():
#                 print(f"PDF file missing at: {pdf_file}")
#                 raise HTTPException(
#                     status_code=404,
#                     detail="PDF file not generated successfully"
#                 )

#             print("Both files exist, proceeding with conversion")

#             # Convert to Markdown
#             from utils.latex_to_markdown import create_markdown_pipeline
#             md_pipeline = create_markdown_pipeline()
#             md_result = md_pipeline.convert_latex_to_markdown(str(tex_file), str(output_dir))

#             # Read all files
#             try:
#                 # Read LaTeX content
#                 with open(tex_file, 'r', encoding='utf-8') as f:
#                     latex_content = f.read()
#                 print("Successfully read LaTeX content")

#                 # Read PDF content
#                 with open(pdf_file, 'rb') as f:
#                     pdf_content = base64.b64encode(f.read()).decode('utf-8')
#                 print("Successfully read PDF content")

#                 # Read or create Markdown content
#                 markdown_content = None
#                 if md_result["success"]:
#                     # Save markdown to file if not already saved
#                     if md_result["markdown_content"]:
#                         with open(md_file, 'w', encoding='utf-8') as f:
#                             f.write(md_result["markdown_content"])
                        
#                         # Read the saved markdown file
#                         with open(md_file, 'r', encoding='utf-8') as f:
#                             markdown_content = f.read()
#                         print("Successfully created and read Markdown file")

#                 response_data = {
#                     "tex_file": latex_content,
#                     "pdf_file": pdf_content,
#                     "md_file": markdown_content,
#                     "success": True,
#                     "file_paths": {
#                         "tex": str(tex_file),
#                         "pdf": str(pdf_file),
#                         "md": str(md_file) if markdown_content else None
#                     }
#                 }

#                 if not markdown_content:
#                     response_data["markdown_error"] = md_result.get("error", "Unknown conversion error")
#                     print(f"Markdown conversion failed: {response_data['markdown_error']}")

#                 # Clean up auxiliary files but keep the main outputs
#                 aux_extensions = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
#                 for ext in aux_extensions:
#                     aux_file = output_dir / f"output{ext}"
#                     if aux_file.exists():
#                         aux_file.unlink()
#                 print("Cleaned up auxiliary files")

#                 return JSONResponse(response_data)

#             except Exception as e:
#                 print(f"Error reading files: {str(e)}")
#                 raise HTTPException(
#                     status_code=500,
#                     detail=f"Error reading generated files: {str(e)}"
#                 )

#         except subprocess.CalledProcessError as e:
#             print(f"LaTeX compilation error: {e.stderr}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"LaTeX compilation failed: {e.stderr}"
#             )
    
#     except Exception as e:
#         print(f"Error in process-input endpoint: {str(e)}")
#         raise HTTPException(
#             status_code=500, 
#             detail=str(e)
#         )
    

    
# @app.post("/interact")
# async def interact(user_input: UserInput):
#     """
#     Endpoint to interact with the graph using user input.
#     """
#     # data = await request.json()
#     # user_input  = user_input.message
#     message = user_input.message

    
#     if not message:
#         raise HTTPException(status_code=400, detail="No input provided")

#     try:
#         # Stream the responses from the graph
#         async def event_generator():
#             for response in graph.stream({"messages": [("user", message)]}, stream_mode="values", config=config):
#                 yield f"data: {response}\n\n"

#         return StreamingResponse(event_generator(), media_type="text/event-stream")

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))





# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8001)



# # @app.post("/upload")
# # async def upload_file(file: UploadFile = File(...)):
# #     if file.content_type != "application/pdf":
# #         return JSONResponse(status_code=400, content={"message": "Invalid file type. Please upload a PDF."})

# #     file_location = DATA_FOLDER / file.filename
# #     with open(file_location, "wb") as f:
# #         f.write(await file.read())

# #     # Validate the PDF and read all pages
# #     try:
# #         with open(file_location, "rb") as pdf_file:
# #             reader = PdfReader(pdf_file)
# #             # Iterate through all pages to ensure the PDF is fully readable
# #             for page_num, page in enumerate(reader.pages):
# #                 text = page.extract_text()
# #                 print(f"Text from page {page_num + 1}: {text}")
# #     except Exception as e:
# #         # Delete the file if it's not a valid PDF
# #         os.remove(file_location)
# #         return JSONResponse(status_code=400, content={"message": "The file is not a valid PDF."})

# #     return JSONResponse(content={"message": "File uploaded and verified successfully!"})



# # # upload rfp
# # @app.post("/upload-files")
# # async def upload_files(files: list[UploadFile] = File(...)):
# #     if not all(file.content_type == "application/pdf" for file in files):
# #         return JSONResponse(status_code=400, content={"message": "Invalid file type. Please upload only PDF files."})

# #     successful_uploads = []
# #     failed_uploads = []

# #     for file in files:
# #         file_location = DATA_RFP_FOLDER / file.filename
# #         try:
# #             with open(file_location, "wb") as f:
# #                 f.write(await file.read())

# #             # Validate the PDF and read all pages
# #             with open(file_location, "rb") as pdf_file:
# #                 reader = PdfReader(pdf_file)
# #                 # Iterate through all pages to ensure the PDF is fully readable
# #                 for page_num, page in enumerate(reader.pages):
# #                     text = page.extract_text()
# #                     print(f"Text from file '{file.filename}' page {page_num + 1}: {text}")

# #             successful_uploads.append(file.filename)

# #         except Exception as e:
# #             # Delete the file if it's not a valid PDF or an error occurred
# #             if file_location.exists():
# #                 os.remove(file_location)
# #             failed_uploads.append(file.filename)

# #     if failed_uploads:
# #         return JSONResponse(status_code=400, content={
# #             "message": "Some files were not valid PDFs.",
# #             "failed_uploads": failed_uploads
# #         })

# #     return JSONResponse(content={
# #         "message": "All files uploaded and verified successfully!",
# #         "successful_uploads": successful_uploads
# #     })


from langchain_core.runnables.config import RunnableConfig
# LOCAL IMPORTS.
from graph import create_graph, compile_graph, print_stream
import os 
# api handling imports.
from fastapi import FastAPI,File, UploadFile,HTTPException, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from pypdf import PdfReader
import uvicorn
import base64
import subprocess
import json
from schemas import State
import re

app = FastAPI()
class UserInput(BaseModel):
    message: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATA_FOLDER = Path("testfolder")
DATA_FOLDER.mkdir(exist_ok=True)

DATA_RFP_FOLDER = Path("testfolder")
DATA_RFP_FOLDER.mkdir(exist_ok=True)

verbose = True
builder = create_graph()
graph = compile_graph(builder)

config = RunnableConfig(
    recursion_limit=50,
    configurable={"thread_id": "1"}
)

def extract_section_headings(latex_content):
    # Regular expression to match section headings
    # This regex will match \section, \subsection, \subsubsection, etc.
    section_headings = re.findall(r'\\(sub)*section\*?\{([^}]+)\}', latex_content)
    # Extract just the section titles
    headings = [title for _, title in section_headings]
    return headings

class UserInput(BaseModel):
    message: str


@app.post("/upload-files")
async def upload_files(files: list[UploadFile] = File(...)):
    if not all(file.content_type == "application/pdf" for file in files):
        return JSONResponse(status_code=400, content={"message": "Invalid file type. Please upload only PDF files."})

    successful_uploads = []
    failed_uploads = []

    for file in files:
        file_location = DATA_RFP_FOLDER / file.filename
        try:
            with open(file_location, "wb") as f:
                f.write(await file.read())

            # Validate the PDF and read all pages
            with open(file_location, "rb") as pdf_file:
                reader = PdfReader(pdf_file)
                # Iterate through all pages to ensure the PDF is fully readable
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    print(f"Text from file '{file.filename}' page {page_num + 1}: {text}")

            successful_uploads.append(file.filename)

        except Exception as e:
            # Delete the file if it's not a valid PDF or an error occurred
            if file_location.exists():
                os.remove(file_location)
            failed_uploads.append(file.filename)

    if failed_uploads:
        return JSONResponse(status_code=400, content={
            "message": "Some files were not valid PDFs.",
            "failed_uploads": failed_uploads
        })

    return JSONResponse(content={
        "message": "All files uploaded and verified successfully!",
        "successful_uploads": successful_uploads
    })


@app.post("/process-input-first-wrokflow")
async def process_input(user_input: UserInput):
    try:   
        print(f"Processing input: {user_input.message}")
        
        # Run the graph with the input
        outputs = list(graph.stream(
            {"messages": [("user", user_input.message)]}, 
            stream_mode="values", 
            config=config
        ))

        state = outputs[-1]

        # Get the file paths
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "spaider_agent_temp" / "output_pdf"
        tex_file = output_dir / "output.tex"
        pdf_file = output_dir / "output.pdf"
        md_file = output_dir / "output.md"  # Define markdown file path
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # First check if the tex file exists
            if not tex_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"LaTeX file not found at {tex_file}"
                )

            print(f"Found LaTeX file at: {tex_file}")

            # Run pdflatex multiple times to resolve references
            # for i in range(3):
            #     process = subprocess.run([
            #         'pdflatex',
            #         '-interaction=nonstopmode',
            #         f'-output-directory={str(output_dir)}',
            #         str(tex_file)
            #     ], check=True, capture_output=True, text=True)
            #     print(f"PDFLaTeX run {i+1} completed")

            print(f"Looking for PDF file at: {pdf_file}")

            # Additional debug information
            print(f"Files in output directory: {list(output_dir.glob('*'))}")

            # Check files with detailed logging
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

            print("Both files exist, proceeding with conversion")

            # Convert to Markdown
            from utils.latex_to_markdown import create_markdown_pipeline
            md_pipeline = create_markdown_pipeline()
            md_result = md_pipeline.convert_latex_to_markdown(str(tex_file), str(output_dir))

            # Read all files
            try:
                # Read LaTeX content
                with open(tex_file, 'r', encoding='utf-8') as f:
                    latex_content = f.read()
                print("Successfully read LaTeX content")

                # Extract section headings
                section_headings = extract_section_headings(latex_content)

                # Read PDF content
                with open(pdf_file, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                print("Successfully read PDF content")

                # Read or create Markdown content
                markdown_content = None
                if md_result["success"]:
                    # Save markdown to file if not already saved
                    if md_result["markdown_content"]:
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(md_result["markdown_content"])
                        
                        # Read the saved markdown file
                        with open(md_file, 'r', encoding='utf-8') as f:
                            markdown_content = f.read()
                        print("Successfully created and read Markdown file")

                response_data = {
                    "ai_message": state.get('ai_message'),
                    "tex_file": latex_content,
                    "pdf_file": pdf_content,
                    "md_file": markdown_content,
                    "section_headings": section_headings,
                    "success": True,
                    "file_paths": {
                        "tex": str(tex_file),
                        "pdf": str(pdf_file),
                        "md": str(md_file) if markdown_content else None
                    }
                }

                if not markdown_content:
                    response_data["markdown_error"] = md_result.get("error", "Unknown conversion error")
                    print(f"Markdown conversion failed: {response_data['markdown_error']}")

                # Clean up auxiliary files but keep the main outputs
                aux_extensions = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']
                for ext in aux_extensions:
                    aux_file = output_dir / f"output{ext}"
                    if aux_file.exists():
                        aux_file.unlink()
                print("Cleaned up auxiliary files")

                return JSONResponse(response_data)

            except Exception as e:
                print(f"Error reading files: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error reading generated files: {str(e)}"
                )

        except subprocess.CalledProcessError as e:
            print(f"LaTeX compilation error: {e.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"LaTeX compilation failed: {e.stderr}"
            )
    
    except Exception as e:
        print(f"Error in process-input endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=str(e)
        )
    

    
@app.post("/interact")
async def interact(user_input: UserInput):
    """
    Endpoint to interact with the graph using user input.
    """
    # data = await request.json()
    # user_input  = user_input.message
    message = user_input.message

    
    if not message:
        raise HTTPException(status_code=400, detail="No input provided")

    try:
        # Stream the responses from the graph
        async def event_generator():
            for response in graph.stream({"messages": [("user", message)]}, stream_mode="values", config=config):
                yield f"data: {response}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)



# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     if file.content_type != "application/pdf":
#         return JSONResponse(status_code=400, content={"message": "Invalid file type. Please upload a PDF."})

#     file_location = DATA_FOLDER / file.filename
#     with open(file_location, "wb") as f:
#         f.write(await file.read())

#     # Validate the PDF and read all pages
#     try:
#         with open(file_location, "rb") as pdf_file:
#             reader = PdfReader(pdf_file)
#             # Iterate through all pages to ensure the PDF is fully readable
#             for page_num, page in enumerate(reader.pages):
#                 text = page.extract_text()
#                 print(f"Text from page {page_num + 1}: {text}")
#     except Exception as e:
#         # Delete the file if it's not a valid PDF
#         os.remove(file_location)
#         return JSONResponse(status_code=400, content={"message": "The file is not a valid PDF."})

#     return JSONResponse(content={"message": "File uploaded and verified successfully!"})



# upload rfp




