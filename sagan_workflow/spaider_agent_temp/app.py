# from langchain_core.runnables.config import RunnableConfig
# from graph import create_graph, compile_graph
# from colorama import init, Fore, Style
# import os
# from config import OUTPUT_DIR, IMAGES_DIR

# def initialize_directories():
#     """Initialize necessary directories."""
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     os.makedirs(IMAGES_DIR, exist_ok=True)

# def main():
#     # Initialize colorama for colored output
#     init()
    
#     # Initialize directories
#     initialize_directories()
    
#     # Create and compile graph
#     print(f"{Fore.CYAN}Initializing workflow graph...{Style.RESET_ALL}")
#     builder = create_graph()
#     graph = compile_graph(builder)
    
#     # Print graph structure
#     print(f"{Fore.GREEN}Workflow graph structure:{Style.RESET_ALL}")
#     print(graph.get_graph().draw_mermaid())
    
#     # Configure runtime settings
#     config = RunnableConfig(
#         recursion_limit=50,
#         configurable={"thread_id": "1"}
#     )
    
#     # Main interaction loop
#     while True:
#         try:
#             user_input = input(f"\n{Fore.YELLOW}Enter your query (or 'quit' to exit): {Style.RESET_ALL}")
            
#             if user_input.lower() == 'quit':
#                 break
                
#             # Run the graph
#             for event in graph.stream(
#                 {"messages": [("user", user_input)]},
#                 config=config,
#                 stream_mode="values"
#             ):
#                 if isinstance(event, dict) and "messages" in event:
#                     for role, content in event["messages"]:
#                         if role not in ["system", "error"]:
#                             print(f"\n{Fore.GREEN}{role.capitalize()}: {content}{Style.RESET_ALL}")
                        
#         except Exception as e:
#             print(f"{Fore.RED}Error during execution: {str(e)}{Style.RESET_ALL}")

# if __name__ == "__main__":
#     main()


from langchain_core.runnables.config import RunnableConfig
# LOCAL IMPORTS.
from graph import create_graph, compile_graph, print_stream


config = RunnableConfig(
    recursion_limit=50,
    configurable={"thread_id": "1"}
)
print(config)

if __name__ == "__main__":
    # creating graph workflow instance and then compiling it.
    # verbose = True
    builder = create_graph()
    graph = compile_graph(builder)

    # print the mermaid diagram of the graph.
    print(graph.get_graph().draw_mermaid())
    
    while True:
        user_input = input("############# User: ")
        print_stream(graph.stream({"messages": [("user", user_input)]}, stream_mode="values", config=config))
