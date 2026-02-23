from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StoryOptionLLM(BaseModel):
    text: str = Field(description="the text of the option shown to the user")
    nextNode: Any = Field(default_factory=dict, description="the next node content and its options")


class StoryNodeLLM(BaseModel):
    content: str = Field(description="The main content of the story node")
    isEnding: bool = Field(default=False, description="Whether this node is an ending node")
    isWinningEnding: bool = Field(default=False, description="Whether this node is a winning ending node")
    options: List[StoryOptionLLM] = Field(default_factory=list, description="The options for this node")


class StoryLLMResponse(BaseModel):
    title: str = Field(description="The title of the story")
    rootNode: StoryNodeLLM = Field(description="The root node of the story")
