#registry to Actually all the SKill

from core.registry import get_skills

def route(text):
    if not text.strip():
        return "No input provided."
    new_text = text.split(" ")
    skills = get_skills()
    for word in new_text:
        word = word.lower()
        if word in skills:
            return skills[word](text)
    else:
            return f"No skill found for '{word}'."