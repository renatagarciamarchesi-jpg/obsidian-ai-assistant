# AI Note Generator for Obsidian

Python script that generates notes with AI (Gemini), lets you pick the vault
folder to save them in, and automatically links key concepts with
`[[wikilinks]]` to existing notes (or creates stub notes if they don't exist yet).

Cross-platform: works on Linux, macOS, and Windows, since it's plain Python
with no OS-specific dependencies.

## Requirements

- Python 3.10 or newer
- A free Gemini API key (get one at https://aistudio.google.com/apikey)

## Installation

1. Clone or download this repository, then open a terminal inside the project folder.

2. (Recommended) Create a virtual environment, so dependencies stay isolated
   from your system Python:

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt / PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create your config file:

```bash
cp config.example.json config.json
```

(On Windows: `copy config.example.json config.json`)

Then open `config.json` in any text editor and fill in:
- `vault_path`: absolute path to your Obsidian vault (e.g. `/home/you/Documents/MyVault` on Linux/macOS, or `C:\Users\You\Documents\MyVault` on Windows)
- `gemini_api_key`: your Gemini API key
- `model`: leave it as `gemini-2.5-flash` (fast and cheap) or change it to another Gemini model
- `language`: the language you want generated notes written in (e.g. `es`, `en`) — independent from the code's language
- `match_threshold`: how strict the concept-matching against existing notes is (0-100, 85 is a good default)

## Usage

```bash
python3 main.py
```

(On Windows: `python main.py`)

You'll see a menu with 4 options:

1. **Generate a new note / complete an existing one**: asks for a topic,
   checks if a similar note already exists in the vault (to complete it
   instead of duplicating it), lets you pick a template (general, meeting,
   research, idea, daily) if it's a new note, and automatically links key
   concepts with `[[wikilinks]]`.
2. **Improve an existing note**: rewrites a note so it's better structured,
   without inventing new content. Creates an automatic backup
   (`file.bak.md`) before touching anything.
3. **Chat with AI**: interactive conversation, optionally anchored to an
   existing note's content as context. Type `exit` to quit.
4. **Auto-tag an existing note**: the AI suggests tags based on the content,
   and you confirm whether to add them.

## Optional: a shortcut to launch it faster

**Linux / macOS**, add an alias to your shell config (`~/.bashrc` or `~/.zshrc`):

```bash
echo 'alias notaia="cd /path/to/obsidian_ai_notes && source venv/bin/activate && python3 main.py"' >> ~/.bashrc
source ~/.bashrc
```

Then, from anywhere in the terminal, just type `notaia`.

## How the linking works

1. Along with the content, the model returns a list of "key concepts"
   mentioned in the note.
2. The script scans your whole vault and builds an index of titles (and
   aliases, if you use `aliases:` in your notes' frontmatter).
3. For each concept, it uses fuzzy matching (`rapidfuzz`) against that index.
   If a match is found above `match_threshold`, it replaces the mention in
   the text with `[[Real note title]]`.
4. If there's no match, it asks whether you want to create an empty stub
   note for that concept (so the link isn't broken, and you fill it in later).

## Security note

Your API key is stored in `config.json` in plain text. **Do not commit
`config.json` to GitHub.** The included `.gitignore` handles this
automatically — just don't delete it.

## Ideas for extending later

- Add a "batch" mode that reads a list of topics from a .txt and generates
  several notes at once.
- Keep a log of generated notes with date and topic.
- Add detection of duplicate concepts with different names (e.g. "OOP" vs
  "Object-Oriented Programming") using the frontmatter `aliases`.
