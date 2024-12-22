from typing import Tuple, Dict
import logging
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

def extract_latex_and_message(full_content: str) -> Tuple[str, str]:
    """
    Extracts LaTeX content and AI message from the full response.
    """
    latex_content = full_content
    ai_message = ""
    
    try:
        # Extract AI message if present
        if "<START_OF_AI_MESSAGE>" in full_content:
            parts = full_content.split("<START_OF_AI_MESSAGE>")
            latex_content = parts[0].strip()
            if len(parts) > 1 and "<END_OF_AI_MESSAGE>" in parts[1]:
                ai_message = parts[1].split("<END_OF_AI_MESSAGE>")[0].strip()
        
        # Clean LaTeX content
        latex_content = latex_content.strip()
        if latex_content.startswith("```latex"):
            latex_content = latex_content[7:]
        if latex_content.endswith("```"):
            latex_content = latex_content[:-3]
        latex_content = latex_content.strip()
        
        # Ensure proper LaTeX structure
        if not latex_content.startswith(r'\documentclass'):
            latex_content = r'\documentclass[12pt]{article}' + '\n' + latex_content
            
        if r'\usepackage{graphicx}' not in latex_content:
            latex_content = latex_content.replace(r'\documentclass[12pt]{article}', 
                r'\documentclass[12pt]{article}' + '\n' + r'\usepackage{graphicx}')
            
        if r'\begin{document}' not in latex_content:
            # Find position after packages
            packages_end = latex_content.find(r'\usepackage{graphicx}') + len(r'\usepackage{graphicx}')
            latex_content = latex_content[:packages_end] + '\n\n' + r'\begin{document}' + '\n' + latex_content[packages_end:]
            
        if not latex_content.endswith(r'\end{document}'):
            latex_content += '\n' + r'\end{document}'
            
        return latex_content.strip(), ai_message.strip()
        
    except Exception as e:
        logging.error(f"Error extracting content: {e}")
        return latex_content.strip(), ai_message.strip()

def build_content_summary(section_texts: dict) -> str:
    """
    Creates a structured summary of section contents with absolute paths for images.
    
    This function processes the section texts and ensures that all image paths are
    properly formatted with the complete absolute path. It maintains the original
    content structure while enhancing image references for LaTeX processing.
    
    Args:
        section_texts: Dictionary containing section contents and their associated images
        
    Returns:
        str: Formatted string containing the content summary with absolute image paths
    """
    logger = logging.getLogger(__name__)
    root_path = config.FIRST_WORKFLOW_ROOT
    summary_parts = []
    
    logger.info(f"Processing content summary with root path: {root_path}")
    
    for section, answers in section_texts.items():
        logger.debug(f"Processing section: {section}")
        section_parts = [f"\n{section}:"]
        
        for idx, answer in enumerate(answers, 1):
            content = answer.get('content', '')
            images = answer.get('images', [])
            
            if content:
                logger.debug(f"Adding content for section {section}, entry {idx}")
                section_parts.append(f"\nContent {idx}:\n{content}")
            
            if images:
                logger.debug(f"Processing {len(images)} images for section {section}, entry {idx}")
                absolute_paths = []
                for img_path in images:
                    if not img_path.startswith(root_path):
                        absolute_path = root_path + img_path
                        logger.debug(f"Converting relative path '{img_path}' to absolute: '{absolute_path}'")
                    else:
                        absolute_path = img_path
                        logger.debug(f"Path already absolute: '{img_path}'")
                    absolute_paths.append(absolute_path)
                
                section_parts.append(f"Available images: {', '.join(absolute_paths)}")
        
        summary_parts.append('\n'.join(section_parts))
    
    logger.info("Content summary generation completed")
    return '\n\n'.join(summary_parts)