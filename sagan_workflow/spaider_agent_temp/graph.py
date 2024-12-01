from langgraph.graph import StateGraph, END, START
from langgraph.constants import END
from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv

# LOCAL IMPORTS
from nodes_and_conditional_edges.nodes import *
from nodes_and_conditional_edges.conditional_edges import *
from tools import *
from schemas import State


load_dotenv()

def create_graph():
    # GRAPH INSTANCE
    builder = StateGraph(State)

    # ADD NODES TO THE GRAPH

    builder.add_node("prompt_parser", prompt_parser)
    builder.add_node("abstract_questions_generator", abstract_questions_generator)
    builder.add_node("abstract_answers_generator", abstract_answers_generator)
    builder.add_node("aag_toolnode", research_tools_node)  
    builder.add_node("ste_toolnode", research_tools_node)  
    builder.add_node("sag_toolnode", research_tools_node)  

    builder.add_node("section_topic_extractor", section_topic_extractor)
    builder.add_node("section_wise_question_generator", section_wise_question_generator)
    builder.add_node("section_wise_answers_generator", section_wise_answers_generator)
    builder.add_node("generation_node", generation_node)
    builder.add_node("plan_node", plan_node)

    # ADD EDGES/CONDITIONAL EDGES FOR THE GRAPH
    builder.add_edge(START, "prompt_parser")
    builder.add_edge("prompt_parser", "abstract_questions_generator")
    builder.add_edge("abstract_questions_generator", "abstract_answers_generator")
    builder.add_conditional_edges(
        "abstract_answers_generator",
        aag_tools_condition,
        {
            "aag_toolnode": "aag_toolnode",
            "section_topic_extractor": "section_topic_extractor"
        }
    )
    builder.add_edge("aag_toolnode", "abstract_answers_generator")
    
    builder.add_conditional_edges(
        "section_topic_extractor",
        ste_tools_condition,
        {
            "ste_toolnode": "ste_toolnode",
            "section_wise_question_generator": "section_wise_question_generator"
        }
    )    
    builder.add_edge("ste_toolnode", "section_topic_extractor")
    builder.add_edge("section_wise_question_generator", "section_wise_answers_generator")
    builder.add_conditional_edges(
        "section_wise_answers_generator",
        sag_tools_condition,
        {
            "sag_toolnode": "sag_toolnode",
            "plan_node": "plan_node"
        }
    )   
    builder.add_edge("sag_toolnode", "section_wise_answers_generator")
    builder.add_edge("plan_node", "generation_node")
    builder.add_edge("generation_node", END)


    return builder

def compile_graph(builder):
    '''COMPILE GRAPH'''
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
