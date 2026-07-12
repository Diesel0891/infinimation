"""
Skill: web_scrape
Scrapes static HTML content from URLs.
"""
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("infinimation")

def run(args, *extra_args, raw_text: str = "") -> str:
    # Handle both dict (new engine) and string (old engine)
    if isinstance(args, dict):
        url = args.get("url", "")
        target_class = args.get("target_class", "")
    else:
        url = str(args)
        target_class = extra_args[0] if extra_args else ""

    if not url:
        return "No URL provided."

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        logger.info(f"SCRAPING: {url}")
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        if target_class:
            elements = soup.find_all(class_=target_class)
            texts = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
            if texts:
                return f"Found {len(texts)} elements:\n" + "\n".join(texts[:20])
            return f"No elements with class '{target_class}' found."

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
