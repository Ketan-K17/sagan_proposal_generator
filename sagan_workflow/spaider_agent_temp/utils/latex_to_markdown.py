# utils/latex_to_markdown.py

import re
import subprocess
import os
from pathlib import Path
import logging

class LatexToMarkdownPipeline:
    def __init__(self):
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        self.logger = logging.getLogger('latex_to_md_pipeline')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _clean_latex_content(self, content):
        """Clean LaTeX content before conversion."""
        # Remove LaTeX comments
        content = re.sub(r'%.*?\n', '\n', content)
        
        # Remove document class and packages
        content = re.sub(r'\\documentclass.*?\n', '', content)
        content = re.sub(r'\\usepackage.*?\n', '', content)
        
        # Clean up multiple newlines
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()

    def _convert_sections(self, content):
        """Convert LaTeX sections to Markdown headings."""
        # Convert section commands
        content = re.sub(r'\\section{(.*?)}', r'# \1', content)
        content = re.sub(r'\\subsection{(.*?)}', r'## \1', content)
        content = re.sub(r'\\subsubsection{(.*?)}', r'### \1', content)
        
        return content

    def _convert_formatting(self, content):
        """Convert LaTeX formatting to Markdown formatting."""
        # Basic formatting
        content = re.sub(r'\\textbf{(.*?)}', r'**\1**', content)
        content = re.sub(r'\\textit{(.*?)}', r'*\1*', content)
        content = re.sub(r'\\emph{(.*?)}', r'*\1*', content)
        
        # Lists
        content = re.sub(r'\\begin{itemize}', '', content)
        content = re.sub(r'\\end{itemize}', '', content)
        content = re.sub(r'\\item\s+', '- ', content)
        
        # Enumerate
        content = re.sub(r'\\begin{enumerate}', '', content)
        content = re.sub(r'\\end{enumerate}', '', content)
        content = re.sub(r'\\item\s+', '1. ', content)
        
        return content

    def _convert_math(self, content):
        """Convert LaTeX math to Markdown math."""
        # Inline math
        content = re.sub(r'\$([^$]+?)\$', r'$\1$', content)
        
        # Display math
        content = re.sub(r'\\begin{equation\*?}(.*?)\\end{equation\*?}', r'$$\1$$', content, flags=re.DOTALL)
        content = re.sub(r'\\begin{align\*?}(.*?)\\end{align\*?}', r'$$\1$$', content, flags=re.DOTALL)
        
        return content

    def convert_latex_to_markdown(self, tex_file_path, output_dir=None):
        """
        Convert LaTeX file to Markdown.
        
        Args:
            tex_file_path (str): Path to the LaTeX file
            output_dir (str, optional): Output directory for the Markdown file
            
        Returns:
            dict: Contains success status, markdown content, and file path
        """
        try:
            # Ensure input file exists
            if not os.path.exists(tex_file_path):
                return {
                    "success": False,
                    "error": f"LaTeX file not found: {tex_file_path}",
                    "markdown_content": None,
                    "markdown_path": None
                }

            # Set up output directory
            if output_dir is None:
                output_dir = os.path.dirname(tex_file_path)
            os.makedirs(output_dir, exist_ok=True)

            # Read LaTeX content
            with open(tex_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract content between \begin{document} and \end{document}
            document_match = re.search(r'\\begin{document}(.*?)\\end{document}', 
                                     content, re.DOTALL)
            if document_match:
                content = document_match.group(1)

            # Convert content
            content = self._clean_latex_content(content)
            content = self._convert_sections(content)
            content = self._convert_formatting(content)
            content = self._convert_math(content)

            # Save markdown file
            md_file_path = os.path.join(
                output_dir,
                os.path.splitext(os.path.basename(tex_file_path))[0] + '.md'
            )
            
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Successfully converted to Markdown: {md_file_path}")
            
            return {
                "success": True,
                "markdown_content": content,
                "markdown_path": md_file_path
            }

        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "markdown_content": None,
                "markdown_path": None
            }

def create_markdown_pipeline():
    """Factory function to create a LatexToMarkdownPipeline instance."""
    return LatexToMarkdownPipeline()