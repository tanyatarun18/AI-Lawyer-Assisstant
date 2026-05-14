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
        self.load_knowledge()

    def load_knowledge(self):
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.kb = json.load(f)

            self.section_index = {}
            for chunk in self.kb:
                # Find 'SECTION 121' or 'SECTION 121:' or 'SECTION 121A'
                # Stripping colons/spaces to get a clean '121' key
                found = re.findall(r'SECTION\s*(\d+[A-Z]?)', chunk['text'].upper())
                for n in found:
                    clean_n = n.replace(":", "").strip()
                    if clean_n not in self.section_index:
                        self.section_index[clean_n] = chunk

            log_agent("RAGAgent", f"Index built: {len(self.section_index)} sections mapped.")
        else:
            log_agent("RAGAgent", "Knowledge base not found.")

    def process_raw_data(self):
        log_agent("RAGAgent", "Normalizing wall-of-text database...")
        all_chunks = []
        if not os.path.exists(self.raw_data_path): return

        for filename in os.listdir(self.raw_data_path):
            if filename.endswith(".txt"):
                topic = filename.replace(".txt", "")
                with open(os.path.join(self.raw_data_path, filename), "r", encoding="utf-8") as f:
                    content = f.read()

                    # Force structure into the wall of text
                    # Adds a marker before 'SECTION' but handles cases where it's lowercase or touching words
                    norm = re.sub(r'(\bSECTION\s*\d+[A-Z]?[:\s]*)', r'|||\1', content, flags=re.IGNORECASE)
                    parts = norm.split('|||')

                    for part in parts:
                        clean_part = part.strip()
                        if len(clean_part) > 15:
                            all_chunks.append({"topic": topic, "text": clean_part})

        with open(self.kb_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=4)
        self.kb = all_chunks
        self.load_knowledge()

    def search(self, query, k=3):
        query_nums = re.findall(r'\d+', query)
        query_low = query.lower()
        results = []

        # 1. Direct Sniper Match (Numeric)
        for num in query_nums:
            # Check for '121'
            if num in self.section_index:
                results.append(self.section_index[num])

        # 2. Emergency Direct Scan (If sniper missed due to formatting)
        if not results:
            for chunk in self.kb:
                # If query is 'ipc 121', look for 'SECTION 121' in the text
                for num in query_nums:
                    if f"SECTION {num}" in chunk['text'].upper():
                        results.append(chunk)
                        break

        # 3. Keyword Match Fallback
        query_words = [w for w in query_low.split() if len(w) > 3 and w != 'what']
        scored = []
        for chunk in self.kb:
            score = 0
            text_low = chunk['text'].lower()
            for word in query_words:
                if word in text_low: score += 20

            # Boost matches in the requested Act
            if "ipc" in query_low and "ipc" in chunk['topic'].lower(): score += 50

            if score > 10 and chunk not in results:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results.extend([s[1] for s in scored])

        return [{"text": f"OFFICIAL SOURCE: {res['topic']}\n{res['text']}"} for res in results[:k]]