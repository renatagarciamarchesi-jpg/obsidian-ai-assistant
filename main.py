#!/usr/bin/env python3
"""
AI-powered note generator/assistant for Obsidian, with automatic concept linking.

Usage:
    python3 main.py

Configuration:
    Copy config.example.json to config.json and fill in vault_path and gemini_api_key.
"""
import json
import sys
from pathlib import Path

from rapidfuzz import process, fuzz

from ai_generator import (
    generate_note,
    complete_note,
    improve_note,
    generate_tags,
    create_chat,
)
from templates import TEMPLATES, TEMPLATE_NAMES
from vault_utils import (
    list_folders,
    scan_existing_notes,
    replace_mentions,
    create_stub,
    save_note,
    find_similar_note,
    read_note,
    update_note,
    backup_note,
    add_tags,
    choose_existing_note,
)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print("Couldn't find config.json.")
        print("Copy config.example.json to config.json and fill in vault_path and gemini_api_key.")
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def choose_folder(vault_path: Path) -> Path:
    folders = list_folders(vault_path)
    print("\nAvailable folders in the vault:")
    for i, c in enumerate(folders, start=1):
        rel = c.relative_to(vault_path) if c != vault_path else Path(".")
        print(f"  {i}. {rel}")
    print(f"  {len(folders) + 1}. Create a new folder")

    while True:
        choice = input("\nPick the target folder number: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(folders):
                return folders[idx - 1]
            if idx == len(folders) + 1:
                name = input("Name of the new folder: ").strip()
                new_folder = vault_path / name
                new_folder.mkdir(parents=True, exist_ok=True)
                return new_folder
        print("Invalid choice, try again.")


def choose_template() -> str:
    keys = list(TEMPLATES.keys())
    print("\nAvailable templates:")
    for i, k in enumerate(keys, start=1):
        print(f"  {i}. {TEMPLATE_NAMES[k]}")

    while True:
        choice = input("Pick a template (Enter for 'general'): ").strip()
        if not choice:
            return "general"
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            return keys[int(choice) - 1]
        print("Invalid choice, try again.")


def link_concepts(
    content: str,
    concepts: list[str],
    existing_notes: dict[str, Path],
    vault_path: Path,
    target_folder: Path,
    threshold: int,
) -> tuple[str, list[str], list[str]]:
    """
    For each key concept, finds the best match among existing notes.
    If a good enough match is found, replaces the text with a wikilink.
    If not, asks the user whether to create a stub note.
    Returns: (modified_content, links_created, stubs_created)
    """
    links_created = []
    stubs_created = []

    available_titles = list(existing_notes.keys())

    for concept in concepts:
        match = None
        if available_titles:
            match = process.extractOne(concept.lower(), available_titles, scorer=fuzz.WRatio)

        if match and match[1] >= threshold:
            found_title, score, _ = match
            note_path = existing_notes[found_title]
            real_title = note_path.stem
            content = replace_mentions(content, concept, real_title)
            links_created.append(f"{concept} -> {real_title} ({score:.0f}% match)")
        else:
            answer = input(
                f'No note found for "{concept}". Create an empty stub? (y/n): '
            ).strip().lower()
            if answer == "y":
                stub_path = create_stub(vault_path, target_folder, concept)
                content = replace_mentions(content, concept, stub_path.stem)
                stubs_created.append(concept)
                # add it to the existing notes in case the concept repeats
                existing_notes[concept.lower()] = stub_path
                available_titles.append(concept.lower())

    return content, links_created, stubs_created


def flow_generate_or_complete(config: dict, vault_path: Path):
    topic = input("Note topic: ").strip()
    if not topic:
        print("Empty topic, cancelling.")
        return

    print("\nChecking if a similar note already exists in the vault...")
    existing_path = find_similar_note(vault_path, topic, threshold=config.get("match_threshold", 85))

    complete_mode = False
    target_folder = None

    if existing_path:
        print(f'Found a similar note: "{existing_path.stem}" ({existing_path})')
        answer = input("Complete it instead of creating a new one? (y/n): ").strip().lower()
        if answer == "y":
            complete_mode = True
            target_folder = existing_path.parent
        else:
            print("Ok, creating a new note.")

    template_chosen = None
    if not complete_mode:
        target_folder = choose_folder(vault_path)
        template_chosen = choose_template()

    print("\nGenerating with AI...")
    if complete_mode:
        current_content, current_tags = read_note(existing_path)
        data = complete_note(
            api_key=config["gemini_api_key"],
            model=config.get("model", "gemini-2.5-flash"),
            title=existing_path.stem,
            current_content=current_content,
            topic=topic,
            language=config.get("language", "en"),
        )
    else:
        data = generate_note(
            api_key=config["gemini_api_key"],
            model=config.get("model", "gemini-2.5-flash"),
            topic=topic,
            language=config.get("language", "en"),
            template_instructions=TEMPLATES.get(template_chosen, ""),
        )

    print(f'Generated title: "{data["title"]}"')
    print(f'Key concepts detected: {", ".join(data["key_concepts"])}')

    print("\nScanning existing notes in the vault...")
    existing_notes = scan_existing_notes(vault_path)
    if complete_mode:
        # we don't want the note linking to itself
        existing_notes.pop(existing_path.stem.lower(), None)
    print(f"Found {len(existing_notes)} existing notes.")

    final_content, links, stubs = link_concepts(
        content=data["content_markdown"],
        concepts=data["key_concepts"],
        existing_notes=existing_notes,
        vault_path=vault_path,
        target_folder=target_folder,
        threshold=config.get("match_threshold", 85),
    )

    final_path = (
        update_note(existing_path, final_content, data["tags"])
        if complete_mode
        else save_note(
            target_folder=target_folder,
            title=data["title"],
            content=final_content,
            tags=data["tags"],
        )
    )

    action = "updated" if complete_mode else "saved"
    print(f"\nNote {action} at: {final_path}")
    if links:
        print("\nLinks created:")
        for link in links:
            print(f"  - {link}")
    if stubs:
        print("\nStub notes created for new concepts:")
        for stub in stubs:
            print(f"  - {stub}")


def flow_improve_note(config: dict, vault_path: Path):
    path = choose_existing_note(vault_path)
    if not path:
        return

    current_content, _tags = read_note(path)

    print("\nCreating a backup before modifying...")
    backup_path = backup_note(path)
    print(f"Backup saved at: {backup_path}")

    print("Improving the note with AI (without inventing new content)...")
    data = improve_note(
        api_key=config["gemini_api_key"],
        model=config.get("model", "gemini-2.5-flash"),
        current_content=current_content,
        language=config.get("language", "en"),
    )

    existing_notes = scan_existing_notes(vault_path)
    existing_notes.pop(path.stem.lower(), None)

    final_content, links, stubs = link_concepts(
        content=data["content_markdown"],
        concepts=data.get("key_concepts", []),
        existing_notes=existing_notes,
        vault_path=vault_path,
        target_folder=path.parent,
        threshold=config.get("match_threshold", 85),
    )

    update_note(path, final_content, data.get("tags", []))
    print(f"\nNote improved and saved at: {path}")
    if links:
        print("\nLinks created:")
        for link in links:
            print(f"  - {link}")


def flow_autotag(config: dict, vault_path: Path):
    path = choose_existing_note(vault_path)
    if not path:
        return

    current_content, current_tags = read_note(path)
    print(f"Current tags: {current_tags or '(none)'}")

    print("Generating suggested tags with AI...")
    new_tags = generate_tags(
        api_key=config["gemini_api_key"],
        model=config.get("model", "gemini-2.5-flash"),
        content=current_content,
        language=config.get("language", "en"),
    )

    print(f"Suggested tags: {new_tags}")
    answer = input("Add them to the note? (y/n): ").strip().lower()
    if answer == "y":
        add_tags(path, new_tags)
        print(f"Tags updated on: {path}")
    else:
        print("Cancelled, note was not modified.")


def flow_chat(config: dict, vault_path: Path):
    note_context = None
    answer = input("Anchor the chat to an existing note? (y/n): ").strip().lower()
    if answer == "y":
        path = choose_existing_note(vault_path)
        if path:
            note_context, _tags = read_note(path)
            print(f"Chat anchored to: {path.stem}")

    chat = create_chat(
        api_key=config["gemini_api_key"],
        model=config.get("model", "gemini-2.5-flash"),
        note_context=note_context,
        language=config.get("language", "en"),
    )

    if note_context:
        print("\nAI: Got it, I've read your note. How can I help you improve or expand it?\n")

    print("Chat started. Type 'exit' to quit.\n")
    while True:
        message = input("You: ").strip()
        if message.lower() in ("exit", "quit", "salir"):
            print("Chat ended.")
            break
        if not message:
            continue

        ai_response = chat.send_message(message)
        print(f"\nAI: {ai_response.text}\n")


def main():
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser()

    if not vault_path.exists():
        print(f"The configured vault_path doesn't exist: {vault_path}")
        sys.exit(1)

    print("\n=== AI Assistant for Obsidian ===")
    print("  1. Generate a new note / complete an existing one")
    print("  2. Improve an existing note (with automatic backup)")
    print("  3. Chat with AI (optionally anchored to a note)")
    print("  4. Auto-tag an existing note")

    option = input("\nPick an option: ").strip()

    if option == "1":
        flow_generate_or_complete(config, vault_path)
    elif option == "2":
        flow_improve_note(config, vault_path)
    elif option == "3":
        flow_chat(config, vault_path)
    elif option == "4":
        flow_autotag(config, vault_path)
    else:
        print("Invalid option.")


if __name__ == "__main__":
    main()
