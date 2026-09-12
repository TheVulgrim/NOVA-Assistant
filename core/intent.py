import requests
import json
from core.registry import get_skills
import skills.system_skills

OLLAMA_SERVER = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"

description = {
    "open": "Opens a LOCAL APPLICATION like notepad, calculator, or a program installed on this PC. Use this for app names, NOT websites.",
    "screenshot": "Takes a screenshot of the current screen.",
    "system": "Retrieves detailed system information: CPU, RAM, temperatures, fans, battery.",
    "lock": "Locks the computer screen.",
    "openbrowser": "Opens a WEBSITE URL like youtube, google, or github in a browser. Use this for website names, NOT local apps.",
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
        f"User's command: open calculator\n"
        f'Response: {{"skill": "open", "argument": "calculator"}}\n\n'
        f"Example:\n"
        f"User's command: open notepad\n"
        f'Response: {{"skill": "open", "argument": "notepad"}}\n\n'
        f"Example:\n"
        f"User's command: visit youtube\n"
        f'Response: {{"skill": "openbrowser", "argument": "youtube"}}\n\n'
        f"User's command : {command}"
    )
    return prompt

def classify(text):
    JSON = {
        "model":DEFAULT_MODEL,
        "stream":False,
        "prompt" : build_prompt(text),
        "think": False,
        "options" : {
            "temperature" : 0
        }
    }
    response = requests.post(OLLAMA_SERVER,json=JSON, timeout=60)
    response = response.json()
    return response["response"]


def runtime(text):
    try:
        runIntent = classify(text)
        data = json.loads(runIntent)
        skill = data["skill"]
        argument = data["argument"]
        if skill in get_skills():
            return get_skills()[skill](argument)
        else:
            return f"No such skills in Skill list"
    except Exception as e:
        from core.router import route
        return route(text)
        
    