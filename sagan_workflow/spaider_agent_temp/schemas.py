from langgraph.graph import MessagesState
from dotenv import load_dotenv
from typing import List, Dict, Union

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
