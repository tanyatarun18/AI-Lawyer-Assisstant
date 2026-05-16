import os
import re

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



        self.rag_agent.process_raw_data()

        self.rag_agent.load_knowledge()


    def run(self, user_query):



        self.lang_agent.detect(user_query)

        query_low = user_query.lower()


        has_section = re.search(
            r'\bsection\s+\d+[a-z]?\b',
            query_low
        )

        known_acts = [

            "ipc",
            "crpc",
            "cpc",
            "evidence",
            "motor",
            "mva"
        ]

        mentions_act = any(
            act in query_low
            for act in known_acts
        )

        if has_section and not mentions_act:

            print(
                "\n[System]\n"
                "Please specify the law.\n\n"
                "Examples:\n"
                "- IPC Section 17\n"
                "- CrPC Section 17\n"
                "- CPC Section 17\n"
                "- Evidence Act Section 17\n"
            )

            return


        context_chunks = self.rag_agent.search(
            user_query,
            k=1
        )



        # print("\nTOP SCORES:\n")
        #
        # for s, c in scored[:5]:
        #     print(f"SCORE={s} | TOPIC={c['topic']}")
        #     print(c['text'][:200])




        if context_chunks:

            source = "Local Law Database"

            formatted_context = "\n---\n".join(
                [c["text"] for c in context_chunks]
            )


            #
            # print("\n DEBUG CONTEXT\n")
            #
            # print(formatted_context[:3000])



            final_answer = self.reasoning_agent.generate_local(
                user_query,
                formatted_context
            )



        else:

            source = "Groq Cloud Fallback"

            final_answer = self.reasoning_agent.generate_cloud_fallback(
                user_query
            )


        print(f"\n[{source}]\n{final_answer}\n")




if __name__ == "__main__":

    bot = LawBotOrchestrator()

    while True:

        query = input("Ask a legal question: ")

        if query.lower() in ["exit", "quit"]:

            print("\nExiting Legal Assistant...\n")

            break

        bot.run(query)