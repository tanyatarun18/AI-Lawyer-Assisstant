from datetime import datetime

def log_agent(agent_name, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{agent_name}] {message}")