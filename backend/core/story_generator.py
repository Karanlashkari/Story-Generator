from sqlalchemy.orm import Session

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM

import os


class StoryGenerator:

    MAX_RETRIES = 3

    @classmethod
    def _get_llm(cls):
        endpoint = HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            task="conversational",
            max_new_tokens=600,
            temperature=0.6,
            top_p=0.9,
            repetition_penalty=1.1,
        )
        return ChatHuggingFace(llm=endpoint)

    @classmethod
    def generate_story(
        cls,
        db: Session,
        session_id: str,
        theme: str = "fantasy"
    ) -> Story:

        llm = cls._get_llm()
        parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)
        format_instructions = parser.get_format_instructions()
        
        full_system_prompt = f"{STORY_PROMPT}\n\nOutput your story in this exact JSON format:\n{format_instructions}"

        last_error = None

        for attempt in range(cls.MAX_RETRIES):
            messages = [
                SystemMessage(content=full_system_prompt),
                HumanMessage(content=f"Create the story with this theme: {theme}")
            ]
            raw_response = llm.invoke(messages)
            response_text = raw_response.content if hasattr(raw_response, "content") else raw_response

            try:
                story_structure = parser.parse(response_text)
                # Validate that the root node and its required fields exist
                try:
                    root_node_check = story_structure.rootNode
                    if isinstance(root_node_check, dict):
                        StoryNodeLLM.model_validate(root_node_check)
                except Exception as ve:
                    last_error = ve

                    # If validation failed, ask the LLM to repair the JSON specifically
                    repair_prompt = f"""{STORY_PROMPT}

The previous JSON was INVALID.
Validation errors:
{str(ve)}

Here is the JSON you returned:
{response_text}

Fix ALL errors and ensure every node includes the required `content`, `isEnding`, `isWinningEnding`, and `options` fields.
Concise output constraints (RE-ENFORCE):
- Each node `content` MUST be 1-3 short sentences and no more than 200 characters.
- Each `option.text` MUST be concise and no more than 50 characters.
- Do NOT include any text outside of the required JSON structure.

Output your story in this exact JSON format:
{format_instructions}"""

                    messages = [
                        SystemMessage(content=repair_prompt),
                        HumanMessage(content="Fix the JSON and return it.")
                    ]

                    raw_response = llm.invoke(messages)
                    response_text = raw_response.content if hasattr(raw_response, "content") else raw_response

                    try:
                        story_structure = parser.parse(response_text)
                        # validate again; if still invalid, continue to retry loop
                        root_node_check = story_structure.rootNode
                        if isinstance(root_node_check, dict):
                            StoryNodeLLM.model_validate(root_node_check)
                        break
                    except Exception as e2:
                        last_error = e2
                        continue

                # If validation passed, break out of generation loop
                break

            except Exception as e:
                last_error = e

                # 🔁 Repair instruction
                repair_prompt = f"""{STORY_PROMPT}

The previous JSON was INVALID.
Errors:
{str(e)}

Fix ALL errors.
Rules:
- nextNode MUST NEVER be null
- Every option MUST contain a complete nextNode
- Return the FULL corrected JSON ONLY.

Concise output constraints (RE-ENFORCE):
- Each node `content` MUST be 1-3 short sentences and no more than 200 characters.
- Each `option.text` MUST be concise and no more than 50 characters.
- Do NOT include any text outside of the required JSON structure.

Output your story in this exact JSON format:
{format_instructions}"""

                messages = [
                    SystemMessage(content=repair_prompt),
                    HumanMessage(content="Fix the JSON and return it.")
                ]
                
                # Reset raw_response for retry
                raw_response = llm.invoke(messages)
                response_text = raw_response.content if hasattr(raw_response, "content") else raw_response

        else:
            raise OutputParserException(
                f"Failed to generate valid story after {cls.MAX_RETRIES} attempts",
                last_error
            )

        # =========================
        # Persist to database
        # =========================

        story_db = Story(
            title=story_structure.title,
            session_id=session_id
        )
        db.add(story_db)
        db.flush()

        root_node = story_structure.rootNode
        if isinstance(root_node, dict):
            root_node = StoryNodeLLM.model_validate(root_node)

        cls._process_story_node(
            db=db,
            story_id=story_db.id,
            node_data=root_node,
            is_root=True
        )

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(
        cls,
        db: Session,
        story_id: int,
        node_data: StoryNodeLLM,
        is_root: bool = False
    ) -> StoryNode:

        node = StoryNode(
            story_id=story_id,
            content=node_data.content,
            is_root=is_root,
            is_ending=node_data.isEnding,
            is_winning_ending=node_data.isWinningEnding,
            options=[]
        )

        db.add(node)
        db.flush()

        if not node.is_ending:
            options_payload = []

            for option in node_data.options:
                next_node_data = option.nextNode

                if isinstance(next_node_data, dict):
                    try:
                        next_node_data = StoryNodeLLM.model_validate(next_node_data)
                    except Exception:
                        # Attempt to repair the invalid node JSON by asking the LLM
                        node_parser = PydanticOutputParser(pydantic_object=StoryNodeLLM)
                        node_format = node_parser.get_format_instructions()

                        repair_prompt = f"""{STORY_PROMPT}

The following node JSON is INVALID or missing required fields:
{next_node_data}

Fix ALL errors and return ONLY the corrected node JSON in this exact format:
{node_format}

Concise output constraints (RE-ENFORCE):
- `content`: 1-3 short sentences, max 200 characters.
- `option.text`: max 50 characters.
- Do not include any extra text outside the JSON.
"""

                        llm = cls._get_llm()
                        repair_messages = [
                            SystemMessage(content=repair_prompt),
                            HumanMessage(content="Fix the node JSON and return it.")
                        ]
                        raw_repair = llm.invoke(repair_messages)
                        repair_text = raw_repair.content if hasattr(raw_repair, "content") else raw_repair

                        try:
                            next_node_data = node_parser.parse(repair_text)
                        except Exception as repair_exc:
                            raise OutputParserException(
                                "Failed to repair invalid node JSON",
                                repair_exc
                            )

                child_node = cls._process_story_node(
                    db=db,
                    story_id=story_id,
                    node_data=next_node_data,
                    is_root=False
                )

                options_payload.append({
                    "text": option.text,
                    "node_id": child_node.id
                })

            node.options = options_payload

        db.flush()
        return node
