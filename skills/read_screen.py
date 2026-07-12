"""
skills/read_screen.py — Infinimation Screen Reading Skill
Extracts all visible text from the current screen via UI Automator dump.
Supports keyword filtering for targeted reading.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.ui_automation import dump_ui, parse_ui


def read_screen(keyword: str = None, partial: bool = True) -> dict:
    """Extract visible text from screen. Optionally filter by keyword."""
    if not dump_ui():
        return {"success": False, "message": "Failed to dump UI hierarchy"}

    elements = parse_ui()
    all_texts = [el["text"] for el in elements if el["text"]]
    all_descs = [el["desc"] for el in elements if el["desc"]]

    # Combine text and content-desc for completeness
    combined = list(dict.fromkeys(all_texts + all_descs))

    if keyword:
        kw = keyword.lower()
        if partial:
            filtered = [t for t in combined if kw in t.lower()]
        else:
            filtered = [t for t in combined if t.lower() == kw]
        return {
            "success": True,
            "message": f"Found {len(filtered)} matches for '{keyword}' out of {len(combined)} total text nodes",
            "data": {
                "matches": filtered,
                "total": len(combined),
            }
        }

    return {
        "success": True,
        "message": f"Read {len(combined)} visible text nodes from screen",
        "data": {
            "texts": combined,
            "total": len(combined),
        }
    }


# ── Skill interface for engine ──
def run(args: dict) -> dict:
    keyword = args.get("keyword") or args.get("text") or args.get("query")
    partial = args.get("partial", True)
    return read_screen(keyword=keyword, partial=partial)


# ── Direct test ──
if __name__ == "__main__":
    print("=== Reading full screen ===")
    result = read_screen()
    print(f"Status: {result['message']}")
    for t in result["data"]["texts"][:10]:
        print(f"  - {t}")

    print("\n=== Filtering for 'time' ===")
    result = read_screen(keyword="time")
    print(f"Status: {result['message']}")
    for t in result["data"]["matches"]:
        print(f"  - {t}")
