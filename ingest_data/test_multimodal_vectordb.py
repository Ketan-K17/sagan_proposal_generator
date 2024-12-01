from multimodal_query import MultiModalQueryTool
from rich.console import Console
from rich.panel import Panel
import json
import os
import shutil

def test_multimodal_query():
    console = Console()
    
    # Initialize the query tool
    console.print("\n[yellow]Initializing MultiModalQueryTool...[/yellow]")
    tool = MultiModalQueryTool()
    
    # Create directories for results and images
    results_dir = "query_results"
    images_dir = "retrieved_images"
    
    if os.path.exists(images_dir):
        shutil.rmtree(images_dir)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # Database path
    db_path = "C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/ingest_data/astroai2"
    
    while True:
        # Get query from user
        console.print("\n[yellow]Enter your query (or 'quit' to exit):[/yellow]")
        query = input().strip()
        
        if query.lower() == 'quit':
            break
            
        try:
            # Execute query
            console.print(f"\n[blue]Executing query: {query}[/blue]")
            results = tool.search_similar(
                persist_dir=db_path,
                query=query,
                k=3
            )
            
            # Display results
            if results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                html_path = tool.create_html_result(results, query, timestamp)
                
                console.print(f"\n[green]Found {len(results)} results.[/green]")
                console.print(f"Results saved to: {html_path}")
                console.print(f"Images saved to: {images_dir}")
                
                # Display text results in console
                for i, (doc, score) in enumerate(results, 1):
                    console.print(Panel(
                        f"[cyan]Score:[/cyan] {score:.4f}\n"
                        f"[cyan]Source:[/cyan] {doc.metadata.get('source', 'Unknown')}\n"
                        f"[cyan]Page:[/cyan] {doc.metadata.get('page', 0)}\n\n"
                        f"[white]{doc.page_content[:500]}...[/white]",
                        title=f"Result {i}",
                        border_style="blue"
                    ))
            else:
                console.print("[yellow]No results found.[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error during query: {str(e)}[/red]")
            import traceback
            console.print(traceback.format_exc())
            
        console.print("\n[yellow]Try another query? (y/n):[/yellow]")
        if input().lower() != 'y':
            break

if __name__ == "__main__":
    test_multimodal_query()