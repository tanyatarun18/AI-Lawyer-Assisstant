import os

from groq import Groq

from core.logger import log_agent


class ReasoningAgent:

    def __init__(self):

        self.api_key = os.getenv("GROQ_API_KEY")

        self.client = Groq(
            api_key=self.api_key
        )

        self.model = "llama-3.3-70b-versatile"

    # -----------------------------------
    # LOCAL RAG ANSWERING
    # -----------------------------------

    def generate_local(self, query, context):

        log_agent(
            "ReasoningAgent",
            "STRICT DATABASE MODE ACTIVE..."
        )

        if not context or len(str(context)) < 20:

            return (
                "I could not find a relevant law in the local database."
            )

        query_low = query.lower()

        # -----------------------------------
        # LEGAL QUERY TYPE DETECTION
        # -----------------------------------

        legal_help_prompt = ""

        theft_words = [
            "theft",
            "stolen",
            "chori",
            "saman",
            "phone",
            "wallet",
            "train"
        ]

        fir_words = [
            "fir",
            "complaint",
            "report",
            "police"
        ]

        fraud_words = [
            "fraud",
            "scam",
            "dhokha",
            "cheating"
        ]

        assault_words = [
            "maar",
            "fight",
            "assault",
            "pitai"
        ]

        landlord_words = [
            "landlord",
            "rent",
            "kiraya",
            "ghar",
            "tenant",
            "eviction"
        ]

        # -----------------------------------
        # THEFT GUIDANCE
        # -----------------------------------

        if any(w in query_low for w in theft_words):

            legal_help_prompt = """
            The user is asking about theft or stolen property.

            Explain:
            1. Relevant legal section
            2. What the law says
            3. Practical next steps
            4. FIR/police reporting guidance
            5. Keep response simple and practical
            """

        # -----------------------------------
        # FIR GUIDANCE
        # -----------------------------------

        elif any(w in query_low for w in fir_words):

            legal_help_prompt = """
            The user needs FIR/legal complaint guidance.

            Explain:
            1. Relevant legal section
            2. How to file FIR
            3. What documents/details may be needed
            4. Keep response practical and simple
            """

        # -----------------------------------
        # FRAUD GUIDANCE
        # -----------------------------------

        elif any(w in query_low for w in fraud_words):

            legal_help_prompt = """
            The user is asking regarding fraud or cheating.

            Explain:
            1. Relevant law
            2. Immediate actions
            3. Cybercrime/police reporting guidance
            4. Keep answer practical and easy
            """

        # -----------------------------------
        # ASSAULT GUIDANCE
        # -----------------------------------

        elif any(w in query_low for w in assault_words):

            legal_help_prompt = """
            The user is asking regarding assault/fight.

            Explain:
            1. Relevant law
            2. Medical/police steps
            3. FIR guidance
            4. Keep answer simple
            """

        # -----------------------------------
        # LANDLORD / RENT ISSUES
        # -----------------------------------

        elif any(w in query_low for w in landlord_words):

            legal_help_prompt = """
            The user is asking regarding landlord or rent issues.

            Explain:
            1. Tenant rights
            2. Practical legal steps
            3. Police/court/legal notice guidance
            4. Keep response simple
            """

        # -----------------------------------
        # DEFAULT
        # -----------------------------------

        else:

            legal_help_prompt = """
            Answer ONLY using the provided legal context.

            Explain in simple language.
            """

        # -----------------------------------
        # FINAL PROMPT
        # -----------------------------------

        prompt = f"""
        STRICT RULES:

        1. ONLY use PROVIDED_CONTEXT
        2. Do NOT hallucinate laws
        3. If answer not present, say:
           "This law is not in my local database."
        4. Explain in simple language
        5. Give practical legal guidance if possible

        USER_QUERY:
        {query}

        PROVIDED_CONTEXT:
        {context}

        EXTRA_INSTRUCTIONS:
        {legal_help_prompt}
        """

        try:

            completion = self.client.chat.completions.create(

                model=self.model,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2
            )

            return completion.choices[0].message.content

        except Exception as e:

            return f"System Error: {str(e)}"

    # -----------------------------------
    # CLOUD FALLBACK
    # -----------------------------------

    def generate_cloud_fallback(self, query):

        log_agent(
            "ReasoningAgent",
            "CLOUD FALLBACK MODE ACTIVE..."
        )

        prompt = f"""
        The user asked a legal question.

        Provide a helpful and simple explanation.

        USER QUERY:
        {query}

        IMPORTANT:
        - Explain in simple language
        - Give practical guidance
        - Mention this is general legal information
        """

        try:

            completion = self.client.chat.completions.create(

                model=self.model,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.3
            )

            return completion.choices[0].message.content

        except Exception as e:

            return f"System Error: {str(e)}"