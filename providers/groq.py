import requests

def infer(prompt, config):
    api_key = config.get('api_key', '')
    model = config.get('model', 'qwen-2.5-32b')
    timeout = config.get('timeout', 10)
    
    if not api_key:
        raise ValueError("Groq API key not configured")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.1
    }
    
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']
