import os
import json
import re

from core.logger import log_agent


class RAGAgent:

    def __init__(self):

        self.kb_path = "data/processed/kb.json"
        self.raw_data_path = "data/raw"

        self.kb = []

        self.section_index = {}

    # -----------------------------------
    # LOAD KNOWLEDGE BASE
    # -----------------------------------

    def load_knowledge(self):

        if not os.path.exists(self.kb_path):

            log_agent(
                "RAGAgent",
                "Knowledge base not found."
            )

            return

        with open(
            self.kb_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.kb = json.load(f)

        self.section_index = {}

        for chunk in self.kb:

            text_upper = chunk["text"].upper()

            found = re.findall(
                r'(?:SECTION|SEC\.?|^|\s)(\d+[A-Z]?)',
                text_upper
            )

            for sec in found:

                clean_sec = sec.strip().replace(":", "")

                if clean_sec not in self.section_index:

                    self.section_index[clean_sec] = chunk

        log_agent(
            "RAGAgent",
            f"Index built: {len(self.section_index)} sections mapped."
        )

    # -----------------------------------
    # PROCESS RAW DATA
    # -----------------------------------

    def process_raw_data(self):

        log_agent(
            "RAGAgent",
            "Processing raw legal database..."
        )

        all_chunks = []

        if not os.path.exists(self.raw_data_path):

            log_agent(
                "RAGAgent",
                "Raw data folder missing."
            )

            return

        for filename in os.listdir(self.raw_data_path):

            if not filename.endswith(".txt"):

                continue

            topic = filename.replace(".txt", "")

            file_path = os.path.join(
                self.raw_data_path,
                filename
            )

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

                content = content.replace(
                    "\r",
                    "\n"
                )

                # -----------------------------------
                # SPLIT INTO SECTIONS
                # -----------------------------------

                matches = re.split(
                    r'(?=\b(?:SECTION\s*)?\d+[A-Z]?[.:])',
                    content,
                    flags=re.IGNORECASE
                )

                for part in matches:

                    clean_part = part.strip()

                    if len(clean_part) < 40:

                        continue

                    # -----------------------------------
                    # LIMIT CHUNK SIZE
                    # -----------------------------------

                    MAX_CHARS = 1200

                    if len(clean_part) > MAX_CHARS:

                        for i in range(
                            0,
                            len(clean_part),
                            MAX_CHARS
                        ):

                            sub_chunk = clean_part[
                                i:i + MAX_CHARS
                            ]

                            if len(sub_chunk.strip()) > 40:

                                all_chunks.append({

                                    "topic": topic,

                                    "text": sub_chunk.strip()
                                })

                    else:

                        all_chunks.append({

                            "topic": topic,

                            "text": clean_part
                        })

        os.makedirs(
            "data/processed",
            exist_ok=True
        )

        with open(
            self.kb_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                all_chunks,
                f,
                indent=4
            )

        self.kb = all_chunks

        self.load_knowledge()

    # -----------------------------------
    # SEARCH FUNCTION
    # -----------------------------------

    def search(self, query, k=1):

        query_low = query.lower().strip()

        results = []

        # -----------------------------------
        # HINDI NORMALIZATION
        # -----------------------------------

        hindi_map = {

            "chori": "theft",
            "saman": "property",
            "maal": "property",
            "train": "railway",

            "maar": "assault",
            "pitai": "assault",

            "dhokha": "fraud",

            "qatl": "murder",

            "zamanat": "bail",

            "kya karoon": "legal remedy",

            "madad": "help",

            "complaint": "fir",

            "report": "fir"
        }

        normalized_query = query_low

        for h, e in hindi_map.items():

            normalized_query = normalized_query.replace(
                h,
                e
            )

        # -----------------------------------
        # MULTILINGUAL ACT DETECTION
        # -----------------------------------

        target_act = None

        ipc_terms = [
            "ipc",
            "indian penal code",
            "आईपीसी"
        ]

        crpc_terms = [
            "crpc",
            "code of criminal procedure",
            "सीआरपीसी"
        ]

        cpc_terms = [
            "cpc",
            "code of civil procedure",
            "सीपीसी"
        ]

        evidence_terms = [
            "evidence",
            "evidence act",
            "साक्ष्य"
        ]

        if any(
            term in normalized_query
            for term in ipc_terms
        ):

            target_act = "ipc"

        elif any(
            term in normalized_query
            for term in crpc_terms
        ):

            target_act = "crpc"

        elif any(
            term in normalized_query
            for term in cpc_terms
        ):

            target_act = "cpc"

        elif any(
            term in normalized_query
            for term in evidence_terms
        ):

            target_act = "evidence"

        # -----------------------------------
        # EXTRACT SECTION NUMBERS
        # -----------------------------------

        query_sections = re.findall(
            r'\b\d+[A-Z]?\b',
            normalized_query.upper()
        )

        scored = []

        # -----------------------------------
        # SCORE CHUNKS
        # -----------------------------------

        for chunk in self.kb:

            text_low = chunk["text"].lower()

            topic_low = chunk["topic"].lower()

            score = 0

            # -----------------------------------
            # ACT BOOST
            # -----------------------------------

            if target_act:

                if target_act in topic_low:

                    score += 500

                else:

                    score -= 200

            # -----------------------------------
            # STRICT SECTION MATCHING
            # -----------------------------------

            for sec in query_sections:

                # Exact heading match

                heading_match = re.search(
                    rf'^\s*(section\s*)?{re.escape(sec.lower())}[.:]',
                    text_low
                )

                # Mention inside body

                body_match = re.search(
                    rf'\bsection\s+{re.escape(sec.lower())}\b',
                    text_low
                )

                # BEST CASE

                if heading_match:

                    score += 5000

                # WEAKER MATCH

                elif body_match:

                    score += 200

            # -----------------------------------
            # KEYWORD BOOST
            # -----------------------------------

            query_words = [

                w for w in normalized_query.split()

                if len(w) > 2
            ]

            for word in query_words:

                if word in text_low:

                    score += 20

            # -----------------------------------
            # LEGAL INTENT DETECTION
            # -----------------------------------

            theft_words = [

                "theft",
                "stolen",
                "property",
                "railway",
                "train",
                "chori"
            ]

            fir_words = [

                "fir",
                "complaint",
                "police",
                "report"
            ]

            # Theft queries

            if any(
                w in normalized_query
                for w in theft_words
            ):

                if "379" in text_low:

                    score += 500

                if "theft" in text_low:

                    score += 300

                if "stolen property" in text_low:

                    score += 300

                if "railway" in text_low:

                    score += 200

            # FIR queries

            if any(
                w in normalized_query
                for w in fir_words
            ):

                if "154" in text_low:

                    score += 400

                if (
                    "information in cognizable cases"
                    in text_low
                ):

                    score += 300

                if "police" in text_low:

                    score += 200

            # -----------------------------------
            # SAVE RESULTS
            # -----------------------------------

            if score > 0:

                scored.append(
                    (score, chunk)
                )

        # -----------------------------------
        # SORT RESULTS
        # -----------------------------------

        scored.sort(
            key=lambda x: x[0],
            reverse=True
        )

        # -----------------------------------
        # DEBUG OUTPUT
        # -----------------------------------

        print("\nTOP SCORES:\n")

        for s, c in scored[:5]:

            print(
                f"SCORE={s} | TOPIC={c['topic']}"
            )

            print(c["text"][:200])

            print("\n-------------------\n")

        # -----------------------------------
        # FINAL RESULTS
        # -----------------------------------

        MIN_SCORE = 300

        filtered_results = [

            x for x in scored
            if x[0] >= MIN_SCORE
        ]

        top_results = [

            x[1]
            for x in filtered_results[:k]
        ]

        return [

            {
                "text":
                    f"OFFICIAL SOURCE: {r['topic']}\n"
                    f"{r['text'][:1200]}"
            }

            for r in top_results
        ]