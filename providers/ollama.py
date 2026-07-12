import requests

def infer(prompt, config):
    host = config.get('host', 'http://localhost:11434')
    model = config.get('model', 'qwen2.5:1.5b')
    timeout = config.get('timeout', 30)
    
    resp = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
        timeout=timeout
    )
    resp.raise_for_status()
    return resp.json().get('response', '')
