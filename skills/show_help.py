"""
Skill: show_help
Dynamically lists all available skills and their capabilities.
"""
import os
from pathlib import Path

SKILLS_DIR = Path(__file__).parent

def run(*args, raw_text: str = "") -> str:
    lines = ["🤖 *Infinimation Skills*\n"]
    
    for skill_file in sorted(SKILLS_DIR.glob("*.py")):
        if skill_file.name.startswith("_"):
            continue
        name = skill_file.stem
        # Try to extract a one-line description from the module docstring
        desc = "Automation skill."
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '"""' in content:
                    doc = content.split('"""')[1].strip()
                    first_line = doc.split('\n')[0].strip()
                    if first_line:
                        desc = first_line
        except Exception:
            pass
        lines.append(f"• *{name}* — {desc}")
    
    lines.append("\n_Send any command in plain text and I'll route it to the right skill._")
    return "\n".join(lines)
