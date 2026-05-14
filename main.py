import os
from dotenv import load_dotenv
from agents.language_agent import LanguageAgent
from agents.rag_agent import RAGAgent
from agents.reasoning_agent import ReasoningAgent
from core.logger import log_agent

load_dotenv()


class LawBotOrchestrator:
    def __init__(self):
        self.lang_agent = LanguageAgent()
        self.rag_agent = RAGAgent()
        self.reasoning_agent = ReasoningAgent()
        self.rag_agent.load_knowledge()

    def run(self, user_query):
        self.lang_agent.detect(user_query)
        context_chunks = self.rag_agent.search(user_query, k=3)

        if context_chunks:
            source = "Local Law Database"
            formatted_context = "\n---\n".join([c['text'] for c in context_chunks])
            final_answer = self.reasoning_agent.generate_local(user_query, formatted_context)
        else:
            source = "Gemini Cloud (Internet Backup)"
            final_answer = self.reasoning_agent.generate_cloud_fallback(user_query)

        print(f"\n[{source}]\n{final_answer}\n")


if __name__ == "__main__":
    bot = LawBotOrchestrator()
    while True:
        query = input("Ask a legal question: ")
        if query.lower() in ['exit', 'quit']: break
        bot.run(query)