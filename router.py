import time
import logging
from pathlib import Path
import yaml

logger = logging.getLogger("infinimation.router")

CONFIG_PATH = Path(__file__).parent / "config" / "engine.yaml"

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = {}
        self.last_failure_time = {}
    
    def is_open(self, provider_name):
        if provider_name not in self.failures:
            return False
        if self.failures[provider_name] < self.failure_threshold:
            return False
        if time.time() - self.last_failure_time.get(provider_name, 0) > self.recovery_timeout:
            self.failures[provider_name] = 0
            return False
        return True
    
    def record_success(self, provider_name):
        self.failures[provider_name] = 0
    
    def record_failure(self, provider_name):
        self.failures[provider_name] = self.failures.get(provider_name, 0) + 1
        self.last_failure_time[provider_name] = time.time()

_circuit_breaker = CircuitBreaker()

def route_inference(prompt, max_tokens=256):
    config = load_config()
    llm_config = config.get('llm', {})
    priority = llm_config.get('priority', ['gemini', 'groq', 'openrouter'])
    
    for provider_name in priority:
        if not llm_config.get(provider_name, {}).get('enabled', True):
            continue
        
        if _circuit_breaker.is_open(provider_name):
            logger.warning(f"CIRCUIT_OPEN: {provider_name}")
            continue
        
        try:
            logger.info(f"ROUTING: Trying {provider_name}")
            
            if provider_name == 'gemini':
                from providers import gemini
                response = gemini.infer(prompt, llm_config['gemini'])
            elif provider_name == 'groq':
                from providers import groq
                response = groq.infer(prompt, llm_config['groq'])
            elif provider_name == 'openrouter':
                from providers import openrouter
                response = openrouter.infer(prompt, llm_config['openrouter'])
            elif provider_name == 'ollama':
                from providers import ollama
                response = ollama.infer(prompt, llm_config['ollama'])
            else:
                continue
            
            if response and not response.startswith('[LLM ERROR]'):
                _circuit_breaker.record_success(provider_name)
                logger.info(f"SUCCESS: {provider_name}")
                return response
            
        except Exception as e:
            logger.error(f"PROVIDER_FAIL: {provider_name} | {str(e)}")
            _circuit_breaker.record_failure(provider_name)
    
    logger.error("ALL_PROVIDERS_FAILED")
    return ""
