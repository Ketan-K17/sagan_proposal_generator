# from pathlib import Path
# import os

# # # Base paths
# PROJECT_ROOT = Path(__file__).parent
# SAGAN_ROOT = PROJECT_ROOT.parent.parent

# # # Environment file
# ENV_PATH = PROJECT_ROOT / ".env"

# # Database paths
# ASTRO_DB_PATH = SAGAN_ROOT / "ingest_data" / "astroaidb"
# FNR_TEMPLATE_DB_PATH = SAGAN_ROOT / "ingest_data" / "fnr_template_db"
# ASTRO_AI2_DB_PATH = SAGAN_ROOT / "ingest_data" / "astroai2"

# # Output paths
# OUTPUT_PDF_PATH = PROJECT_ROOT / "output_pdf"
# RETRIEVED_IMAGES_PATH = PROJECT_ROOT / "retrieved_images"

# # # SSL Certificate path
# SSL_CERT_PATH = Path(os.getenv('SSL_CERT_FILE', '')) or Path(os.path.expanduser('~')) / "AppData/Local/.certifi/cacert.pem"

# # Create necessary directories
# def create_directories():
#     """Create all necessary directories if they don't exist."""
#     directories = [
#         OUTPUT_PDF_PATH,
#         RETRIEVED_IMAGES_PATH
#     ]
    
#     for directory in directories:
#         directory.mkdir(parents=True, exist_ok=True)

# # Create directories when config is imported
# create_directories()

# def verify_paths():
#     """Verify that all required paths exist."""
#     required_paths = {
#         "ENV_PATH": ENV_PATH,
#         "ASTRO_DB_PATH": ASTRO_DB_PATH,
#         "FNR_TEMPLATE_DB_PATH": FNR_TEMPLATE_DB_PATH,
#         "ASTRO_AI2_DB_PATH": ASTRO_AI2_DB_PATH,
#         "SSL_CERT_PATH": SSL_CERT_PATH
#     }
    
#     missing_paths = []
#     for name, path in required_paths.items():
#         if not path.exists():
#             missing_paths.append(f"{name}: {path}")
    
#     if missing_paths:
#         print("Warning: The following paths do not exist:")
#         for path in missing_paths:
#             print(f"  - {path}")
    
#     return len(missing_paths) == 0



# # Base paths
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# VECTOR_DB_PATH = "C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/ingest_data/astroai2"

# # Output directories
# OUTPUT_DIR = os.path.join(BASE_DIR, "output_pdf")
# IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

# # Model settings
# MODEL_NAME = "nomic-ai/nomic-embed-text-v1"
# EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# # Query settings
# DEFAULT_K = 3
# MIN_RELEVANCE_SCORE = 0.5 

from pathlib import Path
import os

# Base paths
PROJECT_ROOT = Path(__file__).parent
SAGAN_ROOT = PROJECT_ROOT.parent.parent

# Database paths
VECTOR_DB_PATHS = {
    'astro_db': SAGAN_ROOT / "ingest_data" / "astroaidb",
    'fnr_template_db': SAGAN_ROOT / "ingest_data" / "fnr_template_db",
    'astro_ai2': SAGAN_ROOT / "ingest_data" / "astroai2",
    'astro_ai3': SAGAN_ROOT / "ingest_data" / "astroai3"
}

# Output paths - PROJECT_ROOT is already 'spaider_agent_temp'
OUTPUT_BASE = PROJECT_ROOT
OUTPUT_PDF_PATH = OUTPUT_BASE / "output_pdf"
RETRIEVED_IMAGES_PATH = OUTPUT_BASE / "retrieved_images"
TEX_OUTPUT_PATH = OUTPUT_PDF_PATH / "output.tex"
PDF_OUTPUT_PATH = OUTPUT_PDF_PATH / "output.pdf"
MD_OUTPUT_PATH = OUTPUT_PDF_PATH / "output.md"

# Environment file
ENV_PATH = PROJECT_ROOT / ".env"

MODEL_SETTINGS = {
    'NOMIC_EMBED': "nomic-ai/nomic-embed-text-v1",
    'SENTENCE_TRANSFORMER': "sentence-transformers/all-MiniLM-L6-v2",
    'DEFAULT_K': 3,
    'MIN_RELEVANCE_SCORE': 0.5
}

# SSL Certificate path
SSL_CERT_PATH = Path(os.getenv('SSL_CERT_FILE', '')) or Path(os.path.expanduser('~')) / "AppData/Local/.certifi/cacert.pem"

def create_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        OUTPUT_PDF_PATH,
        RETRIEVED_IMAGES_PATH,
        OUTPUT_PDF_PATH / "images"  # For LaTeX images
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def verify_paths():
    """Verify that all required paths exist."""
    required_paths = {
        "ENV_PATH": ENV_PATH,
        **{f"VECTOR_DB_{k.upper()}": v for k, v in VECTOR_DB_PATHS.items()},
        "SSL_CERT_PATH": SSL_CERT_PATH
    }
    
    missing_paths = []
    for name, path in required_paths.items():
        if not path.exists():
            missing_paths.append(f"{name}: {path}")
    
    if missing_paths:
        print("Warning: The following paths do not exist:")
        for path in missing_paths:
            print(f"  - {path}")
    
    return len(missing_paths) == 0

# Create directories when config is imported
create_directories()