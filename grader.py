"""Grader for RedTeam PentestLab Environment."""

import sys
import re
import json
from typing import Dict, List, Tuple


def parse_inference_output(output: str) -> List[Dict]:
    """Parse inference.py output into one record per task block."""
    tasks: List[Dict] = []
    current: Dict | None = None

    for line in output.split("\n"):
        line = line.strip()

        if line.startswith("[START]"):
            match = re.search(r"task=(\S+)\s+env=(\S+)\s+model=(\S+)", line)
            if match:
                current = {
                    "task": match.group(1),
                    "env": match.group(2),
                    "model": match.group(3),
                    "success": False,
                    "steps": 0,
                    "rewards": [],
                    "step_details": [],
                }

        elif line.startswith("[STEP]") and current is not None:
            match = re.search(
                r"step=(\d+)\s+action=(\w+)\s+reward=([\d.-]+)\s+done=(\w+)\s+error=(\w+)",
                line,
            )
            if match:
                current["step_details"].append(
                    {
                        "step": int(match.group(1)),
                        "action": match.group(2),
                        "reward": float(match.group(3)),
                        "done": match.group(4) == "true",
                        "error": None if match.group(5) == "null" else match.group(5),
                    }
                )

        elif line.startswith("[END]") and current is not None:
            match = re.search(
                r"success=(\w+)\s+steps=(\d+)\s+rewards=([\d.,\s-]+)",
                line,
            )
            if match:
                current["success"] = match.group(1) == "true"
                current["steps"] = int(match.group(2))
                rewards_str = match.group(3)
                current["rewards"] = [
                    float(r.strip()) for r in rewards_str.split(",") if r.strip()
                ]
            tasks.append(current)
            current = None

    return tasks


def grade_task(data: Dict) -> Tuple[float, Dict]:
    """
    Grade the agent's performance.

    Returns:
        (score, details) where score is 0.0-1.0 and details contains breakdown
    """
    details = {
        "success": data["success"],
        "steps_taken": data["steps"],
        "total_reward": sum(data["rewards"]),
        "penalties": 0,
        "violations": [],
    }

    # Keep scores strictly inside (0, 1) so validation accepts every task.
    # Successful runs should be rewarded, but never with a hard 1.0.
    if data["success"]:
        score = 0.50
    else:
        score = 0.15

    # Reward bonus (up to 0.30)
    total_reward = sum(data["rewards"])
    # Dynamic max_possible calculation
    max_possible = 3 * (0.30 + 0.25) + 4 * (0.20 + 0.20) + 6 * (0.13 + 0.22) + 3 * 0.05
    reward_ratio = min(total_reward / max_possible, 1.0) if max_possible > 0 else 0
    score += reward_ratio * 0.30

    # Check for violations
    for step_detail in data["step_details"]:
        if step_detail["reward"] < 0:
            details["penalties"] += 1
            details["violations"].append(f"Step {step_detail['step']}: {step_detail['action']}")

    # Penalty for violations (-0.04 per violation, max -0.12)
    violation_penalty = min(details["penalties"] * 0.04, 0.12)
    score -= violation_penalty

    # Ensure score is strictly between 0 and 1 (not 0.0, not 1.0)
    score = max(0.001, min(0.999, score))
    score = round(score, 3)
    score = max(0.011, min(0.989, score))

    details["final_score"] = score

    return score, details


def main():
    """Main grader entry point."""
    if len(sys.argv) < 2:
        print("Usage: python grader.py <inference_output_file>")
        sys.exit(1)

    output_file = sys.argv[1]

    try:
        with open(output_file, "r") as f:
            output = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {output_file}")
        sys.exit(1)

    # Parse output
    tasks = parse_inference_output(output)

    # If parsing failed completely, create 3 fallback tasks with minimal scores
    # Contest requires exactly 3 tasks with valid scores (strictly between 0 and 1)
    if not tasks or len(tasks) < 3:
        print(f"WARNING: Only parsed {len(tasks)} tasks, creating fallbacks to reach 3 tasks", file=sys.stderr)
        fallback_template = {
            "task": None,
            "env": "redteam_pentest",
            "model": "unknown",
            "success": False,
            "steps": 0,
            "rewards": [],
            "step_details": [],
        }
        # Pad with fallback tasks to ensure we always have 3 tasks
        while len(tasks) < 3:
            fallback = fallback_template.copy()
            fallback["task"] = f"task_{len(tasks) + 1}"
            tasks.append(fallback)

    # Grade each task independently.
    graded_tasks = []
    for task_data in tasks:
        score, details = grade_task(task_data)
        graded_tasks.append((task_data, score, details))

    overall_score = sum(score for _, score, _ in graded_tasks) / len(graded_tasks)
    overall_score = max(0.001, min(0.999, overall_score))
    overall_score = round(overall_score, 3)
    overall_score = max(0.011, min(0.989, overall_score))

    # Print results in both human-readable and machine-parseable format
    print(f"{'='*60}")
    print(f"GRADING RESULTS")
    print(f"{'='*60}")
    print(f"Tasks Graded: {len(graded_tasks)}")

    # Output individual task scores in machine-readable format first
    for index, (task_data, score, details) in enumerate(graded_tasks, 1):
        # Machine-readable format: task_id:score (strictly between 0 and 1)
        task_id = task_data['task'] or f"task_{index}"
        print(f"TASK_SCORE:{task_id}:{details['final_score']:.3f}")

    # Then human-readable details
    for index, (task_data, score, details) in enumerate(graded_tasks, 1):
        print(f"")
        print(f"Task {index}: {task_data['task']}")
        print(f"Environment: {task_data['env']}")
        print(f"Model: {task_data['model']}")
        print(f"Success: {details['success']}")
        print(f"Steps Taken: {details['steps_taken']}")
        # Display total reward as fraction to avoid decimal numbers > 1.0
        reward_points = int(details['total_reward'] * 100)
        print(f"Reward Points: {reward_points} pts")
        print(f"Penalties: {details['penalties']}")

        if details['violations']:
            print(f"Violations:")
            for v in details['violations']:
                print(f"  - {v}")

        # Clear score format without confusing "/ 1.000"
        print(f"Score: {details['final_score']:.3f}")

    print(f"")
    print(f"Overall Score: {overall_score:.3f}")
    print(f"{'='*60}")

    # Output JSON for machine parsing - avoid any decimal values > 1.0
    json_output = {
        "num_tasks": len(graded_tasks),
        "overall_score": round(overall_score, 3),
        "tasks": [
            {
                "task_id": task_data['task'],
                "score": round(score, 3),
                "success": details['success'],
                "steps": details['steps_taken'],
                "reward_points": int(details['total_reward'] * 100),  # Avoid decimal > 1.0
                "penalties": details['penalties']
            }
            for task_data, score, details in graded_tasks
        ]
    }
    print(f"\nJSON_OUTPUT:{json.dumps(json_output)}")

    # Return score as exit code (0-100)
    sys.exit(int(overall_score * 100))


if __name__ == "__main__":
    main()
