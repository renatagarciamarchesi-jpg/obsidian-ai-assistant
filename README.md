# AI Note Generator for Obsidian

Python script that generates notes with AI (Gemini), lets you pick the vault
folder to save them in, and automatically links key concepts with
`[[wikilinks]]` to existing notes (or creates stub notes if they don't exist yet).

## Installation on Linux Mint 22.2 Cinnamon

1. Make sure you have Python 3 and pip (Mint 22.2 already includes them, but just in case):

```bash
python3 --version
sudo apt update
sudo apt install python3-pip python3-venv -y
```

2. Go into the project folder and create a virtual environment (recommended
   so you don't mix packages with your system Python):

```bash
cd obsidian_ai_notes
python3 -m venv venv
source venv/bin/activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Get a free Gemini API key at https://aistudio.google.com/apikey

5. Create your config file:

```bash
cp config.example.json config.json
nano config.json
```

Fill in:
- `vault_path`: absolute path to your Obsidian vault, e.g. `/home/renata/Documents/MyVault`
- `gemini_api_key`: your API key
- `model`: leave it as `gemini-2.5-flash` (fast and cheap) or change it to another Gemini model
- `language`: the language you want generated notes written in (e.g. `es`, `en`) - independent from the code's language
- `match_threshold`: how strict the concept-matching against existing notes is (0-100, 85 is a good default)

## Usage

```bash
source venv/bin/activate   # if not already active
python3 main.py
```

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

## For not having to activate the venv every time

You can create an alias in your `~/.bashrc`:

```bash
echo 'alias notaia="cd ~/obsidian_ai_notes && source venv/bin/activate && python3 main.py"' >> ~/.bashrc
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

## Ideas for extending later

- Add a "batch" mode that reads a list of topics from a .txt and generates
  several notes at once.
- Keep a log of generated notes with date and topic.
- Add detection of duplicate concepts with different names (e.g. "OOP" vs
  "Object-Oriented Programming") using the frontmatter `aliases`.
