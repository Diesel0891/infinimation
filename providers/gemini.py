import requests
import json
import time

def infer(prompt, config):
    api_key = config.get('api_key', '')
    model = config.get('model', 'gemini-2.5-flash')
    timeout = config.get('timeout', 15)
    retries = config.get('retries', 3)
    
    if not api_key:
        raise ValueError("Gemini API key not configured")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 512,
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }
    
    last_error = ""
    for attempt in range(retries):
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=timeout)
            
            # Handle rate limiting
            if resp.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                last_error = f"Rate limited (429), waiting {wait_time}s"
                time.sleep(wait_time)
                continue
            
            resp.raise_for_status()
            
            result = resp.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                finish_reason = candidate.get('finishReason', 'UNKNOWN')
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    text = candidate['content']['parts'][0].get('text', '')
                    
                    if text and text.strip().startswith('{') and text.strip().endswith('}'):
                        try:
                            json.loads(text)
                            return text
                        except json.JSONDecodeError:
                            last_error = f"Invalid JSON (attempt {attempt+1}): {text[:50]}"
                    else:
                        last_error = f"Not JSON (attempt {attempt+1}, finish={finish_reason}): {text[:50]}"
                else:
                    last_error = f"No content (attempt {attempt+1}, finish={finish_reason})"
            else:
                last_error = f"No candidates (attempt {attempt+1})"
                
        except Exception as e:
            last_error = f"Exception (attempt {attempt+1}): {str(e)}"
    
    return f"[LLM ERROR] Gemini failed after {retries} attempts. Last: {last_error}"
