"""
skills/planner/engine.py — Infinimation Task Planner
Breaks complex multi-step requests into executable skill sequences.
"""

import re
import sys
import os
from typing import List, Dict, Any

# Add project root to path for engine import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TaskPlan:
    def __init__(self, original_request: str):
        self.original_request = original_request
        self.steps: List[Dict[str, Any]] = []
        self.memory: Dict[str, Any] = {}
        self.current_step = 0
    
    def add_step(self, skill: str, args: dict, description: str = ""):
        self.steps.append({
            "index": len(self.steps),
            "skill": skill,
            "args": args,
            "description": description,
            "result": None,
            "status": "pending"
        })
    
    def get_next_step(self) -> dict | None:
        for step in self.steps:
            if step["status"] == "pending":
                return step
        return None
    
    def mark_done(self, step_index: int, result: Any):
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["result"] = result
            self.steps[step_index]["status"] = "done"
    
    def mark_failed(self, step_index: int, error: str):
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["result"] = {"error": error}
            self.steps[step_index]["status"] = "failed"
    
    def is_complete(self) -> bool:
        return all(s["status"] in ("done", "failed") for s in self.steps)
    
    def to_dict(self) -> dict:
        return {
            "request": self.original_request,
            "steps": self.steps,
            "memory": self.memory,
            "complete": self.is_complete()
        }


class SimplePlanner:
    """
    Rule-based planner for common multi-step patterns.
    Does not use LLM — deterministic, zero-cost, zero-latency.
    """
    
    SEQUENTIAL_PATTERNS = [
        r'(.+?)\s+then\s+(.+)',
        r'(.+?)\s+and\s+then\s+(.+)',
        r'(.+?)\s+after\s+that\s+(.+)',
        r'first\s+(.+?)\s+then\s+(.+)',
    ]
    
    CONDITIONAL_PATTERNS = [
        r'if\s+(.+?)\s+then\s+(.+)',
        r'if\s+(.+?),\s+(.+)',
    ]
    
    def __init__(self, engine_execute_func=None):
        self.execute = engine_execute_func
    
    def _get_engine(self):
        """Lazy import engine to avoid circular dependency."""
        if self.execute is None:
            import engine
            self.execute = engine.execute_command
        return self.execute
    
    def _classify(self, text: str):
        """Lazy import classify_intent."""
        import engine
        return engine.classify_intent(text)
    
    def parse(self, text: str) -> TaskPlan:
        """Parse a multi-step request into a TaskPlan."""
        plan = TaskPlan(text)
        
        # Try conditional patterns first
        for pattern in self.CONDITIONAL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                condition = match.group(1).strip()
                action = match.group(2).strip()
                plan.add_step("evaluate_condition", {
                    "condition": condition,
                    "raw_text": text
                }, f"Check if: {condition}")
                plan.add_step("conditional_action", {
                    "action": action,
                    "depends_on": 0,
                    "raw_text": text
                }, f"If true, do: {action}")
                return plan
        
        # Try sequential patterns
        for pattern in self.SEQUENTIAL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                step1_text = match.group(1).strip()
                step2_text = match.group(2).strip()
                
                skill1, args1 = self._classify(step1_text)
                skill2, args2 = self._classify(step2_text)
                
                if skill1:
                    plan.add_step(skill1, args1, step1_text)
                else:
                    plan.add_step("llm_fallback", {"raw_text": step1_text}, step1_text)
                
                if skill2:
                    plan.add_step(skill2, args2, step2_text)
                else:
                    plan.add_step("llm_fallback", {"raw_text": step2_text}, step2_text)
                
                return plan
        
        # Single step
        skill, args = self._classify(text)
        if skill:
            plan.add_step(skill, args, text)
        else:
            plan.add_step("llm_fallback", {"raw_text": text}, text)
        
        return plan
    
    def execute_plan(self, plan: TaskPlan) -> dict:
        """Execute all steps in a plan sequentially."""
        results = []
        execute = self._get_engine()
        
        while True:
            step = plan.get_next_step()
            if not step:
                break
            
            idx = step["index"]
            skill_name = step["skill"]
            args = step["args"]
            
            # Handle conditional steps
            if skill_name == "conditional_action":
                depends = args.get("depends_on", 0)
                condition_result = plan.steps[depends]["result"] if depends < len(plan.steps) else None
                if condition_result and condition_result.get("success"):
                    action_text = args.get("action", "")
                    skill, skill_args = self._classify(action_text)
                    if skill:
                        result = execute(action_text)
                        plan.mark_done(idx, result)
                        results.append(result)
                    else:
                        plan.mark_failed(idx, "Could not classify conditional action")
                        results.append({"error": "Could not classify conditional action"})
                else:
                    plan.mark_done(idx, {"skipped": True, "reason": "Condition was false"})
                    results.append({"skipped": True})
                continue
            
            # Handle evaluate_condition
            if skill_name == "evaluate_condition":
                plan.mark_done(idx, {"success": True, "evaluated": False, "note": "Condition evaluation not yet implemented"})
                results.append({"note": "Condition evaluation placeholder"})
                continue
            
            # Standard skill execution
            try:
                result = execute(args.get("raw_text", ""))
                plan.mark_done(idx, result)
                results.append(result)
            except Exception as e:
                plan.mark_failed(idx, str(e))
                results.append({"error": str(e)})
        
        return {
            "success": plan.is_complete(),
            "plan": plan.to_dict(),
            "results": results
        }


def run(args: dict) -> dict:
    """Skill interface for the planner."""
    text = args.get("raw_text", "")
    
    planner = SimplePlanner()
    plan = planner.parse(text)
    
    if len(plan.steps) == 1:
        import engine
        return engine.execute_command(text)
    
    return planner.execute_plan(plan)


if __name__ == "__main__":
    tests = [
        "open chrome then read screen",
        "check my battery and then open whatsapp",
        "if battery is low then open settings",
        "scrape https://example.com",
    ]
    
    planner = SimplePlanner()
    for text in tests:
        print(f"\n>>> {text}")
        plan = planner.parse(text)
        print(f"Steps: {len(plan.steps)}")
        for step in plan.steps:
            print(f"  {step['index']}: {step['skill']} | {step['description']}")
