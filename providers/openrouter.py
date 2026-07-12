import requests

def infer(prompt, config):
    api_key = config.get('api_key', '')
    model = config.get('model', 'qwen/qwen-2.5-7b-instruct')
    timeout = config.get('timeout', 15)
    
    if not api_key:
        raise ValueError("OpenRouter API key not configured")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Diesel0891/infinimation",
        "X-Title": "Infinimation"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.1
    }
    
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']
