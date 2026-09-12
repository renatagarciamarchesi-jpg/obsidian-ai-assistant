"""
Functions for interacting with the Obsidian vault:
listing folders, scanning existing notes, creating stubs, saving notes.
"""
import re
from datetime import date
from pathlib import Path

import frontmatter


def list_folders(vault_path: Path) -> list[Path]:
    """Returns all subfolders of the vault (recursive), ignoring .obsidian and hidden ones."""
    folders = [vault_path]
    for p in vault_path.rglob("*"):
        if p.is_dir() and not any(part.startswith(".") for part in p.parts):
            folders.append(p)
    return sorted(set(folders))


def scan_existing_notes(vault_path: Path) -> dict[str, Path]:
    """
    Walks the vault and builds a dict {lowercase_title: absolute_path}.
    The title is the filename without extension.
    If a note has 'aliases' in its frontmatter, those are also added as keys.
    """
    notes = {}
    for file in vault_path.rglob("*.md"):
        if any(part.startswith(".") for part in file.parts):
            continue
        title = file.stem
        notes[title.lower()] = file

        try:
            post = frontmatter.load(file)
            aliases = post.get("aliases", [])
            if isinstance(aliases, str):
                aliases = [aliases]
            for alias in aliases:
                notes[str(alias).lower()] = file
        except Exception:
            # if the file has invalid frontmatter, keep going without breaking
            pass

    return notes


def replace_mentions(content: str, concept: str, real_title: str) -> str:
    """
    Replaces mentions of 'concept' in the text with [[real_title]],
    respecting word boundaries and skipping text already inside [[ ]].
    """
    pattern = re.compile(
        r"(?<!\[\[)\b" + re.escape(concept) + r"\b(?!\]\])",
        re.IGNORECASE,
    )

    def _replace(match):
        original_text = match.group(0)
        if original_text.lower() == real_title.lower():
            return f"[[{real_title}]]"
        return f"[[{real_title}|{original_text}]]"

    # only replace the first occurrence so we don't flood the note with links
    return pattern.sub(_replace, content, count=1)


def create_stub(vault_path: Path, target_folder: Path, title: str) -> Path:
    """Creates an empty stub note for a concept that doesn't exist yet."""
    path = target_folder / f"{title}.md"
    if path.exists():
        return path

    post = frontmatter.Post("")
    post["tags"] = ["stub"]
    post["auto_created"] = True
    post.content = f"# {title}\n\n*Automatically generated stub note. Complete it.*\n"

    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


def find_similar_note(vault_path: Path, topic: str, threshold: int = 80) -> Path | None:
    """
    Checks if a note with a title similar to the requested topic already exists,
    across the WHOLE vault (not just the target folder). Returns the path if a
    good enough match is found, or None if nothing similar exists.
    """
    from rapidfuzz import process, fuzz

    notes = scan_existing_notes(vault_path)
    if not notes:
        return None

    available_titles = list(notes.keys())
    match = process.extractOne(topic.lower(), available_titles, scorer=fuzz.WRatio)

    if match and match[1] >= threshold:
        found_title, _score, _ = match
        return notes[found_title]

    return None


def read_note(path: Path) -> tuple[str, list[str]]:
    """Reads an existing note and returns (content_without_frontmatter, current_tags)."""
    post = frontmatter.load(path)
    tags = post.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    return post.content, tags


def update_note(path: Path, new_content: str, new_tags: list[str]) -> Path:
    """Overwrites an existing note with updated content, preserving its location."""
    post = frontmatter.load(path)
    post.content = new_content

    current_tags = post.get("tags", [])
    if isinstance(current_tags, str):
        current_tags = [current_tags]
    combined_tags = sorted(set(current_tags) | set(new_tags))
    post["tags"] = combined_tags
    post["last_updated"] = str(date.today())

    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


def backup_note(path: Path) -> Path:
    """Creates a backup copy 'file.bak.md' before overwriting a note."""
    backup_path = path.with_suffix(".bak.md")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def add_tags(path: Path, new_tags: list[str]) -> Path:
    """Adds new tags to an existing note's frontmatter, without touching its content."""
    post = frontmatter.load(path)
    current_tags = post.get("tags", [])
    if isinstance(current_tags, str):
        current_tags = [current_tags]
    post["tags"] = sorted(set(current_tags) | set(new_tags))

    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


def choose_existing_note(vault_path: Path) -> Path | None:
    """Lists all notes in the vault with numbers and lets the user pick one. None if cancelled."""
    notes = sorted(vault_path.rglob("*.md"))
    notes = [n for n in notes if not any(p.startswith(".") for p in n.parts)]

    if not notes:
        print("No notes found in the vault yet.")
        return None

    print("\nAvailable notes:")
    for i, n in enumerate(notes, start=1):
        print(f"  {i}. {n.relative_to(vault_path)}")

    choice = input("\nPick a note number (or press Enter to cancel): ").strip()
    if not choice:
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(notes):
        return notes[int(choice) - 1]

    print("Invalid choice.")
    return None


def save_note(target_folder: Path, title: str, content: str, tags: list[str]) -> Path:
    """Saves the final note with frontmatter. If the title already exists, appends a numeric suffix."""
    target_folder.mkdir(parents=True, exist_ok=True)

    path = target_folder / f"{title}.md"
    counter = 2
    while path.exists():
        path = target_folder / f"{title} ({counter}).md"
        counter += 1

    post = frontmatter.Post(content)
    post["tags"] = tags
    post["date"] = str(date.today())

    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path
