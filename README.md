# 🧠 Obsidian AI Assistant

An AI-powered note generator and writing assistant for your **Obsidian vault**, built with Python and Google Gemini (100% free, no credit card needed).

---

## Features

| Feature | What it does |
|---|---|
| **Generate notes from templates** | Picks a template (General, Meeting, Research, Idea, Daily) and generates a complete, structured Markdown note |
| **Improve existing notes** | Reads a note and returns a better-structured, wikilinked, and cleaner version (with auto-backup) |
| **AI chat assistant** | Interactive assistant — optionally grounded in one of your notes — for expansions, Q&A, or rewrites |
| **Auto-tag notes** | Reads a note and appends AI-generated `#tags` at the bottom |

---

## Setup (Step-by-Step)

### 1. Install Python

Download **Python 3.10+** from https://www.python.org/downloads/ and install it.
Make sure to check **"Add Python to PATH"** during installation.

### 2. Get a free Google Gemini API Key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account (Gmail works)
3. Click **"Create API key"**
4. Copy it — it looks like `AIzaSy...`

> No credit card required. The free tier gives you 1,500 requests/day — more than enough for personal use.

### 3. Install dependencies

Open a terminal (Command Prompt or PowerShell on Windows) **inside this folder** and run:

```bash
pip install -r requirements.txt
```

> To open a terminal inside the folder: click the address bar at the top of the folder, type `cmd`, and press Enter.

### 4. Run the script

```bash
python obsidian_ai.py
```

On first run it will ask for:
- Your **Gemini API key** (saved locally in `config.json`)
- The **full path to your Obsidian vault** (e.g. `C:\Users\You\Documents\MyVault`)

Both are saved so you won't be asked again.

---

## File Structure

```
obsidian-ai-assistant/
├── obsidian_ai.py      ← Main script
├── requirements.txt    ← Python dependencies
├── config.json         ← Auto-created on first run (stores vault path + API key)
├── .gitignore          ← Keeps your API key out of GitHub
└── README.md
```

---

## Security Note

Your API key is stored in `config.json` in plain text.
**Do not commit `config.json` to GitHub.** The included `.gitignore` handles this automatically — just don't delete it.

---

## Templates

| Name | Best for |
|---|---|
| `general` | Any topic or concept |
| `meeting` | Meeting notes with action items |
| `research` | Deep dives, study notes |
| `idea` | Brainstorms, creative sparks |
| `daily` | Daily journaling / planning |

---

## 💡 Tips

- Notes are saved directly to the **root of your vault**
- When improving a note, the original is backed up as `filename.bak.md`
- The chat assistant remembers the conversation within a session
- You can change the vault path anytime from the Settings menu (`[5]`)

---

## Model used

This project uses **Google Gemini 2.5 Flash** via the `google-genai` Python SDK.
It is free to use within Google's daily rate limits (1,500 requests/day as of June 2026).

---

## 📜 License

MIT — free to use, modify, and share.
