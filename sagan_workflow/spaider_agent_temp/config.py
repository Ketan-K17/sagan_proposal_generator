import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DB_PATH = "C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/ingest_data/astroai2"

# Output directories
OUTPUT_DIR = os.path.join(BASE_DIR, "output_pdf")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

# Model settings
MODEL_NAME = "nomic-ai/nomic-embed-text-v1"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Query settings
DEFAULT_K = 3
MIN_RELEVANCE_SCORE = 0.5 