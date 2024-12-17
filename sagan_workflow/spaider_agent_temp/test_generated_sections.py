import json
import os
from pathlib import Path
from utils.latex_utils import latex_to_pdf, latex_to_pdf_pandoc, extract_latex_and_message
from config import *

def test_latex_generation():
    """
    Test script to convert generated LaTeX sections to PDF.
    """
    try:
        # Load the JSON data
        input_file = OUTPUT_PDF_PATH / "generated_sections.txt"
        if not input_file.exists():
            print(f"Input file {input_file} not found!")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)

        # Create LaTeX document
        latex_content = []
        latex_content.append(r"""\documentclass[a4paper,12pt]{article}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{hyperref}
\usepackage{geometry}
\geometry{margin=1in}

\title{AI-Driven Autonomous Spacecraft Operations}
\author{}
\date{}

\begin{document}
\maketitle
\tableofcontents
\newpage
""")

        # Process each section
        for section_title, section_content in sections_data.items():
            print(f"Processing section: {section_title}")
            # Extract LaTeX content (remove ```latex and ``` markers)
            latex_only, ai_message = extract_latex_and_message(section_content)
            if latex_only and isinstance(latex_only, str):
                latex_content.append(latex_only)
                latex_content.append("\n\n") # Add some spacing between sections

        latex_content.append(r"\end{document}")

        # Combine all content
        final_latex_document = '\n'.join(latex_content)
        # final_latex_document is a string.

        ##


        # Write out the LaTeX file
        tex_path = OUTPUT_PDF_PATH / "generated_section_test.tex"
        tex_path.write_text(final_latex_document, encoding='utf-8')
        print(f"LaTeX file written to: {tex_path}")

        # Attempt to compile PDF
        # original_dir = os.getcwd()
        # os.chdir(str(OUTPUT_PDF_PATH))
        success = latex_to_pdf(str(tex_path), str(OUTPUT_PDF_PATH))
        if not success:
            print("pdflatex failed, trying pandoc...")
            success = latex_to_pdf_pandoc(str(tex_path), str(OUTPUT_PDF_PATH))
        
        if success:
            pdf_path = OUTPUT_PDF_PATH / "generated_section_test.pdf"
            if pdf_path.exists():
                print(f"Successfully generated PDF at: {pdf_path}")
            else:
                print("PDF generation failed - file not found")
                success = False
        else:
            print("PDF generation failed")
        
    except Exception as e:
        print(f"Error processing LaTeX content: {e}")

if __name__ == "__main__":
    test_latex_generation()