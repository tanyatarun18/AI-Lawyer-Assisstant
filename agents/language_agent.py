from core.logger import log_agent


class LanguageAgent:
    def __init__(self):
        self.hindi_keywords = ['kya', 'kaise', 'hai', 'mein', 'batao', 'namaste', 'shukriya']

    def detect(self, text):
        log_agent("LanguageAgent", "Detecting query language...")
        text_lower = text.lower()

        # Check if any common Hindi/Hinglish keywords exist
        if any(word in text_lower for word in self.hindi_keywords):
            return "Hinglish/Hindi"

        return "English"