

def generation_node(state: State) -> State:
    """Generates LaTeX document based on the final plan and content.
    This refactored version focuses on ensuring the abstract is included in the final output."""
    print(f"{Fore.LIGHTGREEN_EX}################ GENERATION NODE BEGIN #################")
    try:
        base_output_path = OUTPUT_PDF_PATH
        base_output_path.mkdir(parents=True, exist_ok=True)

        # Copy figures from consolidated_template to output path
        copy_figures(CONSOLIDATED_TEMPLATE_PATH, base_output_path)
        
        # Read the LaTeX preamble from the consolidated template
        with open(CONSOLIDATED_TEMPLATE_PATH / "consolidated.tex", "r", encoding='utf-8') as f:
            latex_preamble = ""
            for line in f:
                if line.strip() == "\\begin{document}":
                    break
                latex_preamble += line

        # Retrieve required fields from state
        project_title = state.get("project_title", "Research Project")
        project_abstract = state.get("abstract_text", "No abstract provided.")
        section_answers = state.get("section_answers", {})

        # Debug: Print the abstract we have from the state
        print("DEBUG: Abstract text from state:", project_abstract)

        # Construct the final LaTeX document
        latex_body = ""
        for section_name, answers in section_answers.items():
            latex_body += f"\\section{{{section_name}}}\n\n"
            for ans in answers:
                content = ans.get("content", "")
                latex_body += f"{content}\n\n"

        latex_end = r"\end{document}"

        final_latex_document = latex_preamble + latex_body + latex_end

        # Debug: Print the first 300 chars of the final document to confirm abstract insertion
        print("DEBUG: Beginning of final LaTeX document:\n", final_latex_document[:300])

        # Write out the LaTeX file
        tex_path = base_output_path / "output.tex"
        tex_path.write_text(final_latex_document, encoding='utf-8')
        print(f"LaTeX file written to: {tex_path}")

        # Attempt to compile PDF
        original_dir = os.getcwd()
        os.chdir(str(base_output_path))
        try:
            success = latex_to_pdf("output.tex", str(base_output_path))
            if not success:
                print("pdflatex failed, trying pandoc...")
                success = latex_to_pdf_pandoc("output.tex", str(base_output_path))
            if success:
                pdf_path = base_output_path / "output.pdf"
                if pdf_path.exists():
                    print("Successfully generated PDF with abstract included")
                    state.update({
                        "pdf_status": "success",
                        "pdf_path": str(pdf_path),
                        "generation_message": "Document generated successfully"
                    })
                else:
                    print("PDF generation failed - file not found")
                    success = False
                    state.update({
                        "pdf_status": "failed",
                        "error": "PDF not found after compilation"
                    })
            else:
                print("PDF generation failed")
                state.update({
                    "pdf_status": "failed",
                    "error": "PDF generation failed"
                })
        finally:
            os.chdir(original_dir)

        # Store final latex content in state
        state["draft"] = final_latex_document

    except Exception as e:
        print(f"Error in generation node: {e}")
        state.update({
            "error": str(e),
            "pdf_status": "error",
            "generation_message": f"Error during generation: {str(e)}"
        })

    # Save state in both human-readable and machine-readable formats
    save_state_for_testing(state, "generation_node")

    print(f"################ GENERATION NODE END #################{Style.RESET_ALL}")
    return state