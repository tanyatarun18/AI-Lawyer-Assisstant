import os
import shutil
from agents.scraper_agent import ScraperAgent
from agents.rag_agent import RAGAgent
from core.logger import log_agent


def initialize():
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    if os.path.exists(raw_dir): shutil.rmtree(raw_dir)
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    scraper = ScraperAgent()
    rag = RAGAgent()

    # VERIFIED LINKS - Mixing JSON for speed and verified Markdown for newer laws
    legal_sources = {
        # Core Statutes (Working JSON)
        "IPC_Full": "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main/ipc.json",
        "CrPC_Full": "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main/crpc.json",
        "Evidence_Act": "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main/iea.json",
        "CPC_Civil": "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main/cpc.json",

        # New & Additional Acts
        "HMA_Marriage": "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main/hma.json",
        "MVA_Motor_Vehicles": "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/main/MVA.json",

        # Fixed BNS & Women Rights (Using a more stable mirror)
        "BNS_2023_Guide": "https://raw.githubusercontent.com/nyayasahayak/Nyaysahayak/main/data/bns_data.json",
        "Domestic_Violence_Explained": "https://nyaaya.org/legal-explainer/domestic-violence/"
    }

    log_agent("System", "Starting Clean Scrape with Verified Links...")
    for topic, url in legal_sources.items():
        scraper.scrape_legal_topic(url, topic)

    log_agent("System", "Indexing...")
    rag.process_raw_data()
    print("\n" + "=" * 50)
    print("Check your chunk count now. It should be significantly higher.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    initialize()