# This will store and manage the Registry of Skills

_SKILLS = {}
def skill(*trigger_words):
    def decorator(func):
        for words in trigger_words:
            words = words.lower()
            _SKILLS[words] = func
        return func
    return decorator

def get_skills():
    return _SKILLS