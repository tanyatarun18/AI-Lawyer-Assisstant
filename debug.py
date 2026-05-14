import json
import os

with open("data/processed/kb.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total Chunks: {len(data)}")
print("--- Sample Data from Database ---")
for i in range(min(5, len(data))):
    print(f"Chunk {i} (Topic: {data[i]['topic']}): {data[i]['text'][:150]}...")