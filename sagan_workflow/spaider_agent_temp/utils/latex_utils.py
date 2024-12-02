from pylatex import Document, Command, Package
from pylatex.utils import NoEscape
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import os
import subprocess


def extract_latex_and_message(full_content: str) -> Tuple[str, str]:
    """
    Extracts LaTeX content and AI message from the LLM response.
    
    Args:
        full_content: Complete response from the language model
        
    Returns:
        Tuple containing the LaTeX content and AI message
    """
    latex_content = full_content
    ai_message = ""
    
    try:
        if "<START_OF_AI_MESSAGE>" in full_content:
            parts = full_content.split("<START_OF_AI_MESSAGE>")
            latex_content = parts[0].strip()
            if len(parts) > 1 and "<END_OF_AI_MESSAGE>" in parts[1]:
                ai_message = parts[1].split("<END_OF_AI_MESSAGE>")[0].strip()
        
        latex_content = latex_content.strip()
        if latex_content.startswith("```latex"):
            latex_content = latex_content[7:]
        if latex_content.endswith("```"):
            latex_content = latex_content[:-3]
        
    except Exception as e:
        logging.error(f"Error processing content: {e}")
    
    return latex_content.strip(), ai_message.strip()



def sync_latex_installation() -> bool:
    """
    Synchronizes the LaTeX installation to resolve user/admin sync issues.
    
    Returns:
        bool: True if synchronization was successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Update user database
        logger.info("Updating user database...")
        subprocess.run(
            ['miktex', '--verbose', 'update-db'],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Refresh filename database
        logger.info("Refreshing filename database...")
        subprocess.run(
            ['initexmf', '--update-fndb'],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check XeLaTeX installation
        logger.info("Verifying XeLaTeX installation...")
        result = subprocess.run(
            ['xelatex', '--version'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("LaTeX synchronization successful")
            return True
            
        logger.error("LaTeX verification failed")
        logger.error(f"Error output: {result.stderr}")
        return False
        
    except Exception as e:
        logger.exception(f"Error during LaTeX synchronization: {e}")
        return False


def verify_miktex_installation() -> bool:
    """
    Verifies MiKTeX installation and synchronizes updates.
    Returns True if successful, False otherwise.
    """
    logger = logging.getLogger(__name__)
    try:
        # Update MiKTeX database
        subprocess.run(['initexmf', '--update-fndb'], 
                     check=True, 
                     capture_output=True,
                     text=True)
        
        # Synchronize package database
        subprocess.run(['mpm', '--update-db'],
                     check=True,
                     capture_output=True,
                     text=True)
                     
        return True
    except Exception as e:
        logger.error(f"MiKTeX verification failed: {e}")
        return False



def latex_to_pdf_pandoc(latex_file_path: str, output_directory: Optional[str] = None) -> bool:
    """
    Converts LaTeX to PDF using pandoc with enhanced error handling and image support.
    
    Args:
        latex_file_path: Path to the LaTeX file
        output_directory: Optional directory for output files
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Setup paths
        input_path = Path(latex_file_path).resolve()
        output_dir = Path(output_directory).resolve() if output_directory else input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = output_dir / input_path.with_suffix('.pdf').name
        
        logger.info(f"Processing LaTeX file with pandoc: {input_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Verify pandoc installation
        try:
            version_check = subprocess.run(
                ['pandoc', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Pandoc version information:\n{version_check.stdout}")
        except Exception as e:
            logger.error(f"Pandoc not properly installed: {e}")
            return False
        
        # Store current directory
        original_dir = os.getcwd()
        
        try:
            # Change to output directory
            os.chdir(str(output_dir))
            logger.info(f"Working directory: {os.getcwd()}")
            
            # Configure pandoc command with enhanced options
            cmd = [
                'pandoc',
                str(input_path),
                '-o', str(pdf_path),
                '--pdf-engine=xelatex',
                '--variable=geometry:margin=1in',
                '--variable=graphics=true',
                '--standalone',
                '--verbose'
            ]
            
            # Run pandoc
            logger.info("Running pandoc conversion")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check output
            if result.stdout:
                logger.debug(f"Pandoc stdout:\n{result.stdout}")
            if result.stderr:
                # Pandoc often writes to stderr even for non-errors
                logger.info(f"Pandoc stderr:\n{result.stderr}")
            
            if result.returncode != 0:
                logger.error("Pandoc conversion failed")
                logger.error(f"Return code: {result.returncode}")
                return False
            
            # Verify output
            if pdf_path.exists():
                pdf_size = pdf_path.stat().st_size
                if pdf_size > 0:
                    logger.info(f"Successfully generated PDF using pandoc: {pdf_path} ({pdf_size} bytes)")
                    return True
                else:
                    logger.error("Generated PDF is empty")
                    return False
            else:
                logger.error("PDF file not created")
                return False
                
        finally:
            # Restore original directory
            os.chdir(original_dir)
            logger.info("Restored original directory")
            
    except Exception as e:
        logger.exception(f"Error during pandoc PDF generation: {e}")
        return False
    

def latex_to_pdf(latex_file_path: str, output_directory: Optional[str] = None) -> bool:
    """
    Converts LaTeX to PDF using pdflatex/xelatex with simplified error handling.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Setup paths
        input_path = Path(latex_file_path).resolve()
        output_dir = Path(output_directory).resolve() if output_directory else input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing LaTeX file: {input_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Store current directory
        original_dir = os.getcwd()
        
        try:
            # Change to output directory
            os.chdir(str(output_dir))
            logger.info(f"Working directory: {os.getcwd()}")
            
            # First try pdflatex
            cmd_options = [
                'pdflatex',
                '-interaction=nonstopmode',
                '-halt-on-error',
                '-file-line-error',
                str(input_path)
            ]
            
            logger.info("Attempting pdflatex compilation")
            result = subprocess.run(
                cmd_options,
                capture_output=True,
                text=True,
                check=False
            )
            
            # If pdflatex fails, try xelatex
            if result.returncode != 0:
                logger.info("pdflatex failed, trying xelatex")
                cmd_options[0] = 'xelatex'
                result = subprocess.run(
                    cmd_options,
                    capture_output=True,
                    text=True,
                    check=False
                )
            
            if result.returncode != 0:
                logger.error("Compilation failed with both pdflatex and xelatex")
                logger.error(f"Error output: {result.stderr}")
                return False
            
            # Verify PDF creation
            pdf_path = output_dir / input_path.with_suffix('.pdf').name
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                logger.info(f"Successfully generated PDF: {pdf_path}")
                return True
            
            logger.error("PDF file missing or empty")
            return False
            
        finally:
            os.chdir(original_dir)
            logger.info("Restored original directory")
            
    except Exception as e:
        logger.exception(f"Error during PDF generation: {e}")
        return False



def build_content_summary(section_texts: Dict) -> str:
    """Creates a structured summary of section contents with proper LaTeX image paths."""
    summary_parts = []
    
    for section, answers in section_texts.items():
        section_parts = [f"\n\\section{{{section}}}"]
        
        for idx, answer in enumerate(answers, 1):
            content = answer.get('content', '')
            images = answer.get('images', [])
            
            if content:
                # Add content with proper paragraph formatting
                section_parts.append(f"\n{content}\n")
            
            if images:
                for img_idx, img_path in enumerate(images, 1):
                    try:
                        # Convert path to absolute and normalize for LaTeX
                        img_abs_path = Path(img_path).resolve()
                        latex_path = str(img_abs_path).replace('\\', '/')
                        
                        if img_abs_path.exists():
                            # Create figure environment with proper LaTeX escaping
                            figure_env = (
                                "\\begin{figure}[htbp]\n"
                                "    \\centering\n"
                                f"    \\includegraphics[width=0.8\\textwidth]{{{latex_path}}}\n"
                                f"    \\caption{{Figure related to {section} (Part {img_idx})}}\n"
                                f"    \\label{{fig:{section.lower().replace(' ', '_')}_{img_idx}}}\n"
                                "\\end{figure}\n"
                            )
                            section_parts.append(figure_env)
                            print(f"Added image to LaTeX: {latex_path}")
                        else:
                            print(f"Image not found: {img_abs_path}")
                    except Exception as e:
                        print(f"Error processing image {img_path}: {e}")
                        continue
        
        summary_parts.append('\n'.join(section_parts))
    
    return '\n\n'.join(summary_parts)


def verify_image_paths(latex_content):
    import re
    pattern = r'\\includegraphics(?:\[.*?\])?\{(.*?)\}'
    image_paths = re.findall(pattern, latex_content)
    missing_images = []
    for path in image_paths:
        img_path = Path(path)
        if not img_path.exists():
            print(f"Missing image: {img_path.resolve()}")
            missing_images.append(str(path))
    return len(missing_images) == 0, missing_images