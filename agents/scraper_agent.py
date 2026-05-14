import os
import requests
import json
from bs4 import BeautifulSoup
from pypdf import PdfReader
from io import BytesIO
from core.logger import log_agent


class ScraperAgent:
    def __init__(self):
        self.raw_data_path = "data/raw"
        os.makedirs(self.raw_data_path, exist_ok=True)

    def scrape_legal_topic(self, url, topic):
        log_agent("ScraperAgent", f"Scraping {topic}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            if url.endswith('.json'):
                data = response.json()
                text = self._clean_legal_json(data)
            elif url.endswith('.pdf'):
                text = self._extract_from_pdf(response.content)
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text(separator=' ')

            if not text or len(text.strip()) < 50:
                return None

            clean_text = " ".join(text.split())
            file_path = os.path.join(self.raw_data_path, f"{topic}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(clean_text)
            return clean_text
        except Exception as e:
            log_agent("ScraperAgent", f"Error on {topic}: {e}")
            return None

    def _clean_legal_json(self, data):
        """Robust extraction for Indian Law JSON datasets."""
        lines = []
        if isinstance(data, list):
            for item in data:
                # Target all possible key variations for section numbers and content
                section = item.get('Section') or item.get('section') or item.get('id', '')
                title = item.get('section_title') or item.get('title', '')
                desc = item.get('section_desc') or item.get('description') or item.get('text', '')

                if section and desc:
                    # Create a human-readable sentence for the RAG to find
                    lines.append(f"SECTION {section}: {title}. {desc}")

        # If standard list parsing fails, fallback to raw string
        if not lines:
            return json.dumps(data)

        return "\n\n".join(lines)

    def _extract_from_pdf(self, content):
        reader = PdfReader(BytesIO(content))
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])