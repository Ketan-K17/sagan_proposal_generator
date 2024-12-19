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

# Input paths
INPUT_PDF_FOLDER = SAGAN_ROOT / "data"

# Output paths - PROJECT_ROOT is already 'spaider_agent_temp'
OUTPUT_BASE = PROJECT_ROOT
OUTPUT_PDF_PATH = OUTPUT_BASE / "output_pdf"
RETRIEVED_IMAGES_PATH = OUTPUT_BASE / "retrieved_images"
TEX_OUTPUT_PATH = OUTPUT_PDF_PATH / "output.tex"
PDF_OUTPUT_PATH = OUTPUT_PDF_PATH / "output.pdf"
MD_OUTPUT_PATH = OUTPUT_PDF_PATH / "output.md"
NODEWISE_OUTPUT_PATH = OUTPUT_PDF_PATH / "nodewise_output"
CONSOLIDATED_TEMPLATE_PATH = OUTPUT_BASE / "utils" / "consolidated_template"

# Environment file
ENV_PATH = SAGAN_ROOT / ".env"

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