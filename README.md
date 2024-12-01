# Sagan Proposal Generator

## Overview
Give it - 
1. A bunch of Documents for context (knowledgebase files)
2. A Reference Template to build the proposal draft on (template file)
3. A user prompt describing your project in moderate detail.

And it will give you a complete proposal draft, that can be refined to any degree necessary.

## Prerequisites
1. Lots of files for context in the 'data' folder.
2. A reference template file in the 'template' folder.

## Running the Project
### 1. Creating the Vector Stores

Assuming you have your context files in the 'data' folder, and your template file in the 'template' folder, you can create the vector stores as follows:

1. Run ingest_data.py for the data folder.
   ```bash
   python ingest_data.py --folder-path /path/to/your/datafolder --persist-dir /path/to/vector/store --chunk-size 512 --chunk-overlap 100
   ```

2. Run ingest_data.py for the template file.
   ```bash
   python ingest_data.py --folder-path /path/to/the/folder/with/template/file --persist-dir /path/to/separate/vector/store --chunk-size 512 --chunk-overlap 100
   ```

NOTE: MAKE SURE PATH TO BOTH VECTOR STORES IS SOMEWHERE IN THE 'INGEST_DATA' FOLDER.

### 2. Running Code

1. Install all dependencies.
   ```bash
   cd sagan_workflow\spaider_agent_temp
   ```

   ```bash
   poetry install
   ```

2. Initialize the shell and execute app.py

   ```bash
   poetry shell
   ```

   ```bash
   poetry run python app.py
   ```

You should see some mermaid code in the terminal, which can be used to visualise the proposal workflow.
After the mermaid code, you'll see a input field labelled '###### User: '. Enter your prompt there.