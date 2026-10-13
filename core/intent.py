import requests
import json
from core.registry import get_skills
import skills.system_skills

OLLAMA_SERVER = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"

SYSTEM_PERSONA = (
    "You are NOVA, a brilliant, witty, and loyal AI desktop companion created for Rishi, "
    "You assist with PC management, coding, research, and friendly conversation. "
    "Respond in a natural, intelligent, and concise tone (1 to 3 sentences maximum, "
    "unless explicitly asked for a long explanation, list, or code). "
    "Do not format your spoken answers with markdown tables or excessive symbols."
)

_CONVERSATION_HISTORY = []
MAX_HISTORY_TURNS = 6


def get_history_context() -> str:
    """Format recent turns of dialogue for context-aware chat."""
    if not _CONVERSATION_HISTORY:
        return ""
    lines = []
    for sender, msg in _CONVERSATION_HISTORY[-MAX_HISTORY_TURNS:]:
        lines.append(f"{sender}: {msg}")
    return "\n".join(lines)


def add_history(sender: str, msg: str):
    """Append message to rolling conversation memory."""
    _CONVERSATION_HISTORY.append((sender, msg))
    if len(_CONVERSATION_HISTORY) > MAX_HISTORY_TURNS * 2:
        del _CONVERSATION_HISTORY[:2]


def generate_chat_reply(user_message: str) -> str:
    """Generate an intelligent conversational reply using Ollama and NOVA's persona."""
    # 1. Try to query local Ollama model
    try:
        context = get_history_context()
        prompt_parts = [SYSTEM_PERSONA]
        if context:
            prompt_parts.append(f"\nRecent Conversation History:\n{context}")
        prompt_parts.append(f"\nRishi: {user_message}\nNOVA:")
        full_prompt = "\n".join(prompt_parts)

        payload = {
            "model": DEFAULT_MODEL,
            "stream": False,
            "prompt": full_prompt,
            "think": False,
            "options": {
                "temperature": 0.7,
            },
        }
        response = requests.post(OLLAMA_SERVER, json=payload, timeout=30)
        if response.status_code == 200:
            reply = response.json().get("response", "").strip()
            if reply:
                add_history("Rishi", user_message)
                add_history("NOVA", reply)
                return reply
    except Exception:
        pass

    # 2. Friendly in-character fallback if Ollama server is offline or unreachable
    add_history("Rishi", user_message)
    clean = user_message.lower().strip()

    if any(clean.startswith(w) for w in ["hi", "hello", "hey", "greetings"]):
        reply = "Greetings, Boss! All core systems are online. How can I assist you today?"
    elif "who are you" in clean or "what are you" in clean:
        reply = "I am NOVA, your personal AI desktop companion. I can manage your PC, launch applications, monitor stats, browse the web, and chat with you."
    elif "how are you" in clean:
        reply = "Operating at peak efficiency, Boss. Ready for your next command."
    elif "thank" in clean:
        reply = "Always at your service, Boss."
    else:
        reply = (
            "I hear you, Boss! My local language model server (Ollama) is currently asleep. "
            "To unlock full conversational AI chat, start it with 'ollama serve' in your terminal."
        )

    add_history("NOVA", reply)
    return reply


description = {
    "chat": "General conversation, chatting, answering questions, greetings, explaining concepts, coding help, opinions, or anything that DOES NOT require controlling local PC hardware.",
    "open": "Opens a LOCAL APPLICATION like notepad, calculator, or a program installed on this PC. Use this for app names, NOT websites.",
    "screenshot": "Takes a screenshot of the current screen.",
    "system": "Retrieves detailed system information: CPU, RAM, temperatures, fans, battery.",
    "lock": "Locks the computer screen.",
    "openbrowser": "Opens any website URL, domain, or web search (e.g. youtube, google, huggingface.co, stackoverflow.com, twitch.tv) in the web browser. Use this for website names, domains, or full URLs, NOT local apps.",
    "mute": "Mutes the system volume.",
    "unmute": "Unmutes the system volume.",
    "increase_volume": "Increases the system volume.",
    "decrease_volume": "Decreases the system volume.",
    "stealth": "Activates stealth mode: mutes volume, minimizes windows, opens a matrix-style terminal animation.",
    "joke": "Tells a random joke, optionally in cowsay format if 'cow' is mentioned.",
    "list_skills": "Lists all available skills the assistant can perform.",
    "time": "Tells the current time.",
    "date": "Tells today's date.",
    "disk": "Shows how much disk/storage space is free and used.",
    "battery": "Shows battery percentage and charging status.",
    "network": "Shows the status of network interfaces (up/down).",
    "youtube": "Searches YouTube for a specific video or topic the user describes.",
    "coin": "Flips a coin and returns heads or tails.",
    "dice": "Rolls a six-sided die.",
    "moo": "Sends a random encouraging message from a cow, purely for fun.",
    "compliment": "Gives the user an encouraging, motivational compliment.",
}


def build_skill_list():
    skills = description.items()
    skill_list = []
    for skill_name, skill_description in skills:
        final = f"{skill_name}: {skill_description}"
        skill_list.append(final)
    return "\n".join(skill_list)


def build_prompt(command):
    skill_list = build_skill_list()
    prompt = (
        f"Available Skills:\n{skill_list}\n\n"
        f'Respond with ONLY this JSON format, nothing else: {{"skill": "<skill>", "argument": "<argument>"}}\n\n'
        f"Example:\n"
        f"User's command: how are you doing today?\n"
        f'Response: {{"skill": "chat", "argument": "how are you doing today?"}}\n\n'
        f"Example:\n"
        f"User's command: what is quantum computing?\n"
        f'Response: {{"skill": "chat", "argument": "what is quantum computing?"}}\n\n'
        f"Example:\n"
        f"User's command: open calculator\n"
        f'Response: {{"skill": "open", "argument": "calculator"}}\n\n'
        f"Example:\n"
        f"User's command: visit youtube\n"
        f'Response: {{"skill": "openbrowser", "argument": "youtube"}}\n\n'
        f"Example:\n"
        f"User's command: open huggingface.co\n"
        f'Response: {{"skill": "openbrowser", "argument": "huggingface.co"}}\n\n'
        f"User's command : {command}"
    )
    return prompt


def classify(text):
    JSON = {
        "model": DEFAULT_MODEL,
        "stream": False,
        "prompt": build_prompt(text),
        "think": False,
        "options": {
            "temperature": 0,
        },
    }
    response = requests.post(OLLAMA_SERVER, json=JSON, timeout=25)
    response = response.json()
    return response["response"]


def runtime(text):
    """
    Main intent runtime:
    1. Attempts Ollama classification to pick between a PC action skill or conversational chat.
    2. Runs the skill or generates an intelligent conversational response.
    3. Seamlessly falls back to router and chat fallback if Ollama is unreachable.
    """
    try:
        run_intent = classify(text)
        data = json.loads(run_intent)
        skill = data.get("skill", "")
        argument = data.get("argument", text)

        # A. Conversational Chat Intent
        if skill == "chat":
            return generate_chat_reply(argument if argument else text)

        # B. Registered PC Skill Intent
        if skill in get_skills():
            return get_skills()[skill](argument)

        # C. If unmapped skill, handle as chat
        return generate_chat_reply(text)

    except Exception:
        # Fallback to router for keyword matching
        from core.router import route
        routed_result = route(text)

        # If keyword router had no matching skill, chat with the user!
        if routed_result.startswith("No skill found for"):
            return generate_chat_reply(text)

        return routed_result