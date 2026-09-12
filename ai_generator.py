"""
Calls the Gemini API and asks for a structured JSON response:
title, markdown content, suggested tags, and key concepts to link.
"""
import json

from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are an assistant that writes notes for an Obsidian vault.
You respond ONLY with valid JSON, no extra text, no markdown backticks.

The JSON must have exactly this shape:
{{
  "title": "Short, clear title for the note",
  "content_markdown": "Full note content in Markdown, with headers, lists, etc. Do NOT include [[wikilinks]], those are added automatically afterwards.",
  "tags": ["tag1", "tag2"],
  "key_concepts": ["Concept A", "Concept B", "Concept C"]
}}

"key_concepts" should be a list of 3 to 8 important terms or proper nouns mentioned
in content_markdown that could be topics of other notes in the vault (e.g. theory names,
technologies, people, related concepts). Use exactly the same form they appear in
within content_markdown.

Note language: {language}
Topic requested by the user: {topic}
"""


COMPLETE_PROMPT = """You are an assistant that edits notes in an Obsidian vault.
You respond ONLY with valid JSON, no extra text, no markdown backticks.

A note about this topic already exists. Your job is to COMPLETE it, not rewrite it from scratch:
- Keep all existing content that is correct and relevant, as it is.
- Add new information, examples, or missing sections relevant to the user's request.
- Do NOT delete or summarize existing content. If it's already well explained, leave it as is.
- If the user's request is already fully covered by the existing note, return the content
  as it was, with at most small wording improvements.

The JSON must have exactly this shape:
{{
  "title": "The same note title (do not change it)",
  "content_markdown": "FULL note content (old + newly added), in Markdown, without [[wikilinks]] (those are added automatically afterwards).",
  "tags": ["tag1", "tag2"],
  "key_concepts": ["Concept A", "Concept B"]
}}

"key_concepts" should list important terms mentioned that could be topics of OTHER notes
in the vault (proper nouns, technologies, related theories), using exactly the form they
appear in within content_markdown.

Note language: {language}
Title of the existing note: {title}

--- CURRENT NOTE CONTENT ---
{current_content}
--- END OF CURRENT CONTENT ---

What the user is asking for now about this topic: {topic}
"""


def complete_note(
    api_key: str, model: str, title: str, current_content: str, topic: str, language: str = "en"
) -> dict:
    client = genai.Client(api_key=api_key)

    prompt = COMPLETE_PROMPT.format(
        language=language, title=title, current_content=current_content, topic=topic
    )
    response = client.models.generate_content(model=model, contents=prompt)

    text = response.text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"The AI did not return valid JSON. Response received:\n{text}") from e

    expected_keys = {"title", "content_markdown", "tags", "key_concepts"}
    if not expected_keys.issubset(data.keys()):
        raise ValueError(f"The JSON is missing keys. Received: {list(data.keys())}")

    return data


def generate_note(
    api_key: str, model: str, topic: str, language: str = "en", template_instructions: str = ""
) -> dict:
    client = genai.Client(api_key=api_key)

    prompt = SYSTEM_PROMPT.format(language=language, topic=topic)
    if template_instructions:
        prompt += f"\n\nAdditional formatting instructions: {template_instructions}"

    response = client.models.generate_content(model=model, contents=prompt)

    text = response.text.strip()
    # in case the model adds markdown backticks, strip them
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"The AI did not return valid JSON. Response received:\n{text}") from e

    expected_keys = {"title", "content_markdown", "tags", "key_concepts"}
    if not expected_keys.issubset(data.keys()):
        raise ValueError(f"The JSON is missing keys. Received: {list(data.keys())}")

    return data


IMPROVE_PROMPT = """You are an assistant that improves notes in an Obsidian vault.
You respond ONLY with valid JSON, no extra text, no markdown backticks.

Your job is to rewrite this note so it is better structured and clearer:
- Improve the headers, section order, and wording.
- Do NOT invent new information that isn't in the original note.
- Preserve all the original meaning and data, only improve the form.

The JSON must have exactly this shape:
{{
  "content_markdown": "Improved version of the note in Markdown, without [[wikilinks]] (those are added afterwards).",
  "tags": ["tag1", "tag2"],
  "key_concepts": ["Concept A", "Concept B"]
}}

Note language: {language}

--- ORIGINAL CONTENT ---
{current_content}
--- END OF ORIGINAL CONTENT ---
"""


def improve_note(api_key: str, model: str, current_content: str, language: str = "en") -> dict:
    """Rewrites a note so it is better structured, without inventing new content."""
    client = genai.Client(api_key=api_key)

    prompt = IMPROVE_PROMPT.format(language=language, current_content=current_content)
    response = client.models.generate_content(model=model, contents=prompt)

    text = response.text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"The AI did not return valid JSON. Response received:\n{text}") from e

    expected_keys = {"content_markdown", "tags", "key_concepts"}
    if not expected_keys.issubset(data.keys()):
        raise ValueError(f"The JSON is missing keys. Received: {list(data.keys())}")

    return data


AUTOTAG_PROMPT = """You are an assistant that tags notes in an Obsidian vault.
You respond ONLY with valid JSON of exactly this shape, no extra text:
{{
  "tags": ["tag1", "tag2", "tag3"]
}}

Read the note and suggest between 3 and 6 short tags (one or two words, lowercase,
no spaces, use underscores if needed) that represent the note's main topics well.

Note language: {language}

--- NOTE CONTENT ---
{content}
--- END OF CONTENT ---
"""


def generate_tags(api_key: str, model: str, content: str, language: str = "en") -> list[str]:
    """Suggests tags for an existing note, without modifying its content."""
    client = genai.Client(api_key=api_key)

    prompt = AUTOTAG_PROMPT.format(language=language, content=content)
    response = client.models.generate_content(model=model, contents=prompt)

    text = response.text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"The AI did not return valid JSON. Response received:\n{text}") from e

    return data.get("tags", [])


def create_chat(api_key: str, model: str, note_context: str | None = None, language: str = "en"):
    """
    Creates a real multi-turn chat object using the SDK (client.chats.create).
    Returns the chat object: call chat.send_message(text) for each user message.
    """
    client = genai.Client(api_key=api_key)

    system = (
        "You are a helpful writing assistant for an Obsidian vault, concise and useful. "
        "When suggesting markdown, use proper Obsidian syntax with [[wikilinks]] and #tags. "
        f"Always respond in {language}."
    )

    history = []
    if note_context:
        history.append(
            types.Content(
                role="user",
                parts=[types.Part(text=f"Here is my current note:\n\n{note_context}")],
            )
        )
        history.append(
            types.Content(
                role="model",
                parts=[types.Part(text="Got it, I've read it. How can I help you improve or expand it?")],
            )
        )

    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=1000,
            temperature=0.7,
        ),
        history=history,
    )
    return chat
