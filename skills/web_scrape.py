"""
Skill: web_scrape
Scrapes static HTML content from URLs.
"""
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("infinimation")

def run(url: str, *args, raw_text: str = "") -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        logger.info(f"SCRAPING: {url}")
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        if args and args[0]:
            elements = soup.find_all(class_=args[0])
            texts = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
            if texts:
                return f"Found {len(texts)} elements:\n" + "\n".join(texts[:20])
            return f"No elements with class '{args[0]}' found."
        
        title = soup.title.string.strip() if soup.title else "No title"
        first_p = soup.find('p')
        para = first_p.get_text(strip=True)[:300] if first_p else "No paragraph found"
        return f"Title: {title}\nPreview: {para}..."
        
    except requests.RequestException as e:
        logger.error(f"SCRAPE_ERROR: {e}")
        return f"Failed to scrape {url}: {str(e)}"
    except Exception as e:
        logger.error(f"SCRAPE_UNEXPECTED: {e}")
        return f"Unexpected error: {str(e)}"
