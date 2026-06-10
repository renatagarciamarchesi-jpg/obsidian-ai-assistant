#!/usr/bin/env python3
"""
Obsidian AI Assistant  (Gemini edition — 100% free)
----------------------------------------------------
AI-powered note generator and writing assistant for Obsidian vaults.
Uses Google Gemini 2.5 Flash via the google-genai SDK.
Free tier: 1,500 requests/day, no credit card needed.
Get your API key at: https://aistudio.google.com/app/apikey
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_CONFIG = {
    "vault_path": "",
    "api_key": "",
}

GEMINI_MODEL = "gemini-2.5-flash"

TEMPLATES: dict[str, dict] = {
    "general": {
        "label": "General Note",
        "prompt": (
            "Create a well-structured Obsidian Markdown note about: {topic}\n"
            "Include: a short intro, 3-5 key sections with headers (## level), "
            "bullet points where useful, and a #tags line at the bottom "
            "(only lowercase, hyphen-separated tags like #ai-tools).\n"
            "Return ONLY the Markdown content, no explanation."
        ),
    },
    "meeting": {
        "label": "Meeting Note",
        "prompt": (
            "Create an Obsidian meeting note for: {topic}\n"
            "Sections: Date (today), Attendees, Agenda, Discussion Points, "
            "Action Items, Next Steps.\n"
            "Add relevant #tags at the bottom.\n"
            "Return ONLY the Markdown content."
        ),
    },
    "research": {
        "label": "Research / Deep Dive",
        "prompt": (
            "Create a detailed Obsidian research note about: {topic}\n"
            "Include: Abstract (2-3 sentences), Background, Key Concepts, "
            "Analysis, Open Questions, References (placeholder links), "
            "and #tags at the bottom.\n"
            "Return ONLY the Markdown content."
        ),
    },
    "idea": {
        "label": "Idea / Brainstorm",
        "prompt": (
            "Create an Obsidian idea-capture note for: {topic}\n"
            "Sections: The Idea (1-paragraph hook), Why It Matters, "
            "Possible Approaches (bullet list), Risks & Challenges, "
            "Next Steps, Related Ideas (wikilinks like [[Related Topic]]).\n"
            "Add #tags at the bottom.\n"
            "Return ONLY the Markdown content."
        ),
    },
    "daily": {
        "label": "Daily Note",
        "prompt": (
            "Create an Obsidian daily note template for: {topic}\n"
            "Sections: Morning Intentions, Priorities (numbered), "
            "Schedule (time blocks), Evening Reflection, Gratitude, "
            "and a Mood tracker (emoji scale).\n"
            "Return ONLY the Markdown content."
        ),
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    print("✅ Config saved.")


def get_client(cfg: dict) -> genai.Client:
    key = cfg.get("api_key") or os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        print("\n⚠️  No Gemini API key found.")
        print("   Get one free at: https://aistudio.google.com/app/apikey")
        key = input("   Paste your Gemini API key: ").strip()
        cfg["api_key"] = key
        save_config(cfg)
    return genai.Client(api_key=key)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60]


def resolve_vault(cfg: dict) -> Path:
    vault = cfg.get("vault_path", "").strip()
    if not vault or not Path(vault).is_dir():
        print("\n📁 Vault path not set or not found.")
        vault = input("   Enter the full path to your Obsidian vault: ").strip()
        if not Path(vault).is_dir():
            print(f"   ❌ '{vault}' is not a valid directory.")
            sys.exit(1)
        cfg["vault_path"] = vault
        save_config(cfg)
    return Path(vault)


def gemini_ask(client: genai.Client, system: str, user: str, max_tokens: int = 1500) -> str:
    """Single-turn call to Gemini."""
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=0.7,
        ),
    )
    return response.text


# ── Core features ─────────────────────────────────────────────────────────────

def generate_note(client: genai.Client, topic: str, template_key: str) -> str:
    """Generate a full Markdown note using Gemini."""
    template = TEMPLATES.get(template_key, TEMPLATES["general"])
    system = (
        "You are an expert knowledge-management assistant. "
        "You write clean, well-structured Obsidian Markdown notes. "
        "Always use ## for main sections, bold for key terms, "
        "and [[wikilinks]] when referencing related concepts."
    )
    user = template["prompt"].format(topic=topic)
    print(f"\n🤖 Generating '{template['label']}' note…", end=" ", flush=True)
    result = gemini_ask(client, system, user, max_tokens=1500)
    print("done.")
    return result


def improve_note(client: genai.Client, note_path: Path) -> str:
    """Read an existing note and return an AI-improved version."""
    original = note_path.read_text(encoding="utf-8")
    system = (
        "You are an expert editor for Obsidian knowledge bases. "
        "Improve the note: fix structure, improve clarity, add missing sections, "
        "suggest [[wikilinks]] for key concepts, and ensure tags exist at the bottom. "
        "Return ONLY the improved Markdown — no commentary."
    )
    print(f"\n🔍 Improving '{note_path.name}'…", end=" ", flush=True)
    result = gemini_ask(client, system, original, max_tokens=2000)
    print("done.")
    return result


def chat_with_note(client: genai.Client, note_path: Optional[Path]) -> None:
    """Interactive multi-turn writing assistant."""
    history: list[types.Content] = []

    if note_path:
        context = note_path.read_text(encoding="utf-8")
        print(f"\n💬 Chat assistant — context: {note_path.name}")
        print("   Ask questions, request expansions, or type 'done' to exit.\n")
        # Seed history with the note
        history.append(types.Content(
            role="user",
            parts=[types.Part(text=f"Here is my current note:\n\n{context}")]
        ))
        history.append(types.Content(
            role="model",
            parts=[types.Part(text="Got it! I've read your note. How can I help you improve or expand it?")]
        ))
        print("Assistant: Got it! I've read your note. How can I help you improve or expand it?\n")
    else:
        print("\n💬 General writing assistant. Type 'done' to exit.\n")

    system = (
        "You are a helpful Obsidian writing assistant. "
        "Give concise, actionable answers. "
        "When suggesting Markdown, use proper Obsidian syntax with [[wikilinks]] and #tags."
    )

    chat = client.chats.create(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=1000,
            temperature=0.7,
        ),
        history=history,
    )

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("done", "exit", "quit", ""):
            if user_input.lower() in ("done", "exit", "quit"):
                print("👋 Exiting chat.")
                break
            continue
        response = chat.send_message(user_input)
        print(f"\nAssistant: {response.text}\n")


def auto_tag_note(client: genai.Client, note_path: Path) -> None:
    """Add AI-generated tags to an existing note."""
    original = note_path.read_text(encoding="utf-8")
    system = "You are a precise tagging assistant for Obsidian notes."
    user = (
        f"Read this Obsidian note and return ONLY a space-separated list "
        f"of 4-6 relevant lowercase #tags (e.g. #machine-learning #python). "
        f"No explanation, no punctuation, just the tags.\n\n{original}"
    )
    tags = gemini_ask(client, system, user, max_tokens=60).strip()
    if tags not in original:
        updated = original.rstrip() + f"\n\n{tags}\n"
        note_path.write_text(updated, encoding="utf-8")
        print(f"🏷️  Tags added: {tags}")
    else:
        print("ℹ️  Tags already present — skipped.")


def save_note(vault: Path, title: str, content: str) -> Path:
    filename = f"{slugify(title)}.md"
    dest = vault / filename
    counter = 1
    while dest.exists():
        dest = vault / f"{slugify(title)}-{counter}.md"
        counter += 1
    dest.write_text(content, encoding="utf-8")
    return dest


# ── UI ────────────────────────────────────────────────────────────────────────

def pick_template() -> str:
    print("\n📄 Choose a template:")
    keys = list(TEMPLATES.keys())
    for i, k in enumerate(keys, 1):
        print(f"   {i}. {TEMPLATES[k]['label']}")
    while True:
        choice = input("   Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            return keys[int(choice) - 1]
        print("   ⚠️  Invalid choice.")


def pick_note(vault: Path) -> Optional[Path]:
    notes = sorted(vault.glob("*.md"))
    if not notes:
        print("   ℹ️  No .md files found in vault root.")
        return None
    print("\n📂 Notes in vault root:")
    for i, n in enumerate(notes[:20], 1):
        print(f"   {i:2}. {n.name}")
    if len(notes) > 20:
        print(f"   … and {len(notes)-20} more")
    while True:
        choice = input("   Enter number (or 0 to skip): ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(notes):
            return notes[int(choice) - 1]
        print("   ⚠️  Invalid choice.")


def main_menu(cfg: dict) -> None:
    client = get_client(cfg)
    vault = resolve_vault(cfg)

    banner = r"""
  ___  _         _     _ _              _    ___
 / _ \| |__  ___(_) __| (_) __ _ _ __ / \  |_ _|
| | | | '_ \/ __| |/ _` | |/ _` | '_ / _ \  | |
| |_| | |_) \__ \ | (_| | | (_| | | / ___ \ | |
 \___/|_.__/|___/_|\__,_|_|\__,_|_/_/   \_\___|
         Powered by Google Gemini  (free!)
    """
    print(banner)
    print(f"  Vault: {vault}\n")

    options = {
        "1": "✨ Generate a new note from template",
        "2": "🔧 Improve an existing note",
        "3": "💬 AI chat assistant (with or without a note)",
        "4": "🏷️  Auto-tag an existing note",
        "5": "⚙️  Settings",
        "0": "🚪 Exit",
    }

    while True:
        print("\n─── Main Menu ───────────────────────────────")
        for k, v in options.items():
            print(f"  [{k}] {v}")
        choice = input("\n> ").strip()

        if choice == "1":
            topic = input("   Topic / title: ").strip()
            if not topic:
                continue
            tpl = pick_template()
            content = generate_note(client, topic, tpl)
            dest = save_note(vault, topic, content)
            print(f"\n✅ Note saved: {dest}")

        elif choice == "2":
            note = pick_note(vault)
            if not note:
                continue
            improved = improve_note(client, note)
            backup = note.with_suffix(".bak.md")
            backup.write_text(note.read_text(encoding="utf-8"), encoding="utf-8")
            note.write_text(improved, encoding="utf-8")
            print(f"✅ Improved '{note.name}' (backup: {backup.name})")

        elif choice == "3":
            print("   Load a note as context? (y/n)")
            use_note = input("   > ").strip().lower() == "y"
            note = pick_note(vault) if use_note else None
            chat_with_note(client, note)

        elif choice == "4":
            note = pick_note(vault)
            if note:
                auto_tag_note(client, note)

        elif choice == "5":
            print(f"\n⚙️  Current vault: {vault}")
            print("   Press Enter to keep, or type a new path:")
            new_vault = input("   > ").strip()
            if new_vault and Path(new_vault).is_dir():
                cfg["vault_path"] = new_vault
                vault = Path(new_vault)
                save_config(cfg)

        elif choice == "0":
            print("\n👋 Goodbye!\n")
            break
        else:
            print("   ⚠️  Unknown option.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cfg = load_config()
    main_menu(cfg)
