import requests

def chat_phi3(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "phi3", "prompt": prompt, "stream": False},
    )
    return response.json()["response"]

print(chat_phi3("Explain what crew fatigue risk means in aviation."))
