"""
Note templates for AI generation. Each template adds specific formatting
instructions to the prompt sent to the AI.
"""

TEMPLATES = {
    "general": "Write a clear, well-structured note about the topic, with headers and examples where relevant.",
    "meeting": (
        "Write a meeting note with these sections: Date/Context, Attendees, "
        "Topics discussed, Decisions made, and a list of Action items with markdown "
        "checkboxes (- [ ] action)."
    ),
    "research": (
        "Write an in-depth research note: background on the topic, detailed development, "
        "sources or references if known, and a final Open questions section."
    ),
    "idea": (
        "Write a brainstorm/idea note: brief description of the idea, why it matters, "
        "possible variations or directions, and concrete next steps."
    ),
    "daily": (
        "Write a daily journaling/planning note: Priorities for the day section, "
        "Loose notes, and a brief Reflection at the end."
    ),
}

TEMPLATE_NAMES = {
    "general": "General (any topic or concept)",
    "meeting": "Meeting (with action items)",
    "research": "Research (in-depth study)",
    "idea": "Idea (creative brainstorm)",
    "daily": "Daily (journaling/planning)",
}
