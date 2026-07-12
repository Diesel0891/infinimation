#!/usr/bin/env python3
"""
bin/cron_runner.py — Cron wrapper for Infinimation skills
Runs a skill by name with JSON args and logs output.
"""

import sys
import os
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import execute_command

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bin/cron_runner.py <skill_name> [json_args]")
        sys.exit(1)

    skill_name = sys.argv[1]
    args = {}
    if len(sys.argv) >= 3:
        try:
            args = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print(f"Invalid JSON args: {sys.argv[2]}")
            sys.exit(1)

    command = f"cron run {skill_name}"
    if args:
        command += f" with {json.dumps(args)}"

    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] Running: {command}")

    try:
        result = execute_command(command)
        print(f"[{timestamp}] Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"[{timestamp}] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
