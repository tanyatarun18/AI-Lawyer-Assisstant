import os
from groq import Groq
from core.logger import log_agent
from dotenv import load_dotenv

load_dotenv()


class ReasoningAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    def generate_local(self, query, context):
        log_agent("ReasoningAgent", "STRICT DATABASE MODE ACTIVE...")

        # If context is empty, we force a failure so you can see the DB isn't working
        if not context or len(str(context)) < 20:
            return "[DB_EMPTY_ERROR]: No relevant law found in the 675 mapped sections."

        # We tell the AI it MUST NOT use its own knowledge
        prompt = f"""
        STRICT RULES:
        1. You are a summarizer for a LOCAL DATABASE.
        2. ONLY use the 'PROVIDED_CONTEXT' below to answer.
        3. If the answer is not in 'PROVIDED_CONTEXT', say: 'This law is not in my local database.'

        USER_QUERY: {query}

        PROVIDED_CONTEXT:
        {context}
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0  # Forced zero-creativity
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"System Error: {str(e)}"