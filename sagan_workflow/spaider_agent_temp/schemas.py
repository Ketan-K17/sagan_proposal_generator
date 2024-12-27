from langgraph.graph import MessagesState
from dotenv import load_dotenv
from typing import List, Dict, Union
from pydantic import BaseModel, Field

load_dotenv()

class State(MessagesState):
    project_title: str
    project_description: str
    abstract_questions: List[str]
    abstract_text: str
    section_topics: List[str]
    section_questions: Dict[str, List[str]]  # key = section_topic, value = list of questions.
    section_answers: Dict[str, List[Dict[str, Union[str, List[str]]]]]
    plan: Dict[str, List[str]]  # key = section_topic, value = list of steps.
    draft: str
    generated_sections: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of LaTeX content for each section. Keys are section titles, and values are self-contained LaTeX content."
    )
