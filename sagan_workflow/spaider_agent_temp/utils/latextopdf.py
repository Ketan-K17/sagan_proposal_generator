import subprocess
import os
import logging
from typing import Optional

# local imports
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

def latex_to_pdf(latex_file_path: str, output_directory: Optional[str] = None) -> bool:
    """
    Converts a LaTeX file to PDF format using pdflatex.
    
    This function handles the conversion process with proper error checking and logging.
    It ensures the input file exists, the output directory is valid, and captures any
    compilation errors that might occur during the conversion process.
    
    Args:
        latex_file_path (str): Path to the input LaTeX file
        output_directory (Optional[str]): Directory for output files. If None, uses default path
        
    Returns:
        bool: True if conversion was successful, False otherwise
        
    Raises:
        FileNotFoundError: If the input LaTeX file doesn't exist
        ValueError: If the output directory is invalid
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Convert to Path objects for better path handling
        latex_path = Path(latex_file_path)
        
        # Verify input file exists
        if not latex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {latex_file_path}")
        
        # Set up output directory
        if output_directory is None:
            output_directory = config.OUTPUT_PDF_PATH
        
        output_path = Path(output_directory)
        
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Log conversion attempt
        logger.info(f"Starting LaTeX to PDF conversion for: {latex_path.name}")
        logger.info(f"Output directory: {output_path}")
        
        # Prepare pdflatex command with enhanced options
        pdflatex_command = [
            'pdflatex',
            '-interaction=nonstopmode',  # Don't stop for errors
            '-halt-on-error',           # Stop on serious errors
            '-file-line-error',         # Give file and line for errors
            f'-output-directory={output_path}',
            latex_path
        ]
        
        # Run pdflatex twice to resolve references
        for run in range(2):
            logger.debug(f"Running pdflatex (pass {run + 1}/2)")
            
            # Execute pdflatex command and capture output
            process = subprocess.run(
                pdflatex_command,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception immediately
            )
            
            # Check for errors
            if process.returncode != 0:
                logger.error("PDF generation failed")
                logger.error(f"Error output:\n{process.stderr}")
                logger.error(f"Standard output:\n{process.stdout}")
                return False
            
            logger.debug(f"Pass {run + 1} completed successfully")
        
        # Verify PDF was created
        pdf_path = output_path / latex_path.with_suffix('.pdf').name
        if not pdf_path.exists():
            logger.error("PDF file not found after compilation")
            return False
        
        logger.info(f"PDF generated successfully: {pdf_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error during PDF generation: {e}")
        logger.error(f"Command output: {e.output}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error during PDF generation: {e}")
        return False