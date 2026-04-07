"""Grader for RedTeam PentestLab Environment."""

import sys
import re
from typing import Dict, List, Tuple


def parse_inference_output(output: str) -> Dict:
    """Parse inference.py output to extract results."""
    data = {
        "task": None,
        "env": None,
        "model": None,
        "success": False,
        "steps": 0,
        "rewards": [],
        "step_details": [],
    }

    for line in output.split("\n"):
        line = line.strip()

        # Parse [START] line
        if line.startswith("[START]"):
            match = re.search(r"task=(\S+)\s+env=(\S+)\s+model=(\S+)", line)
            if match:
                data["task"] = match.group(1)
                data["env"] = match.group(2)
                data["model"] = match.group(3)

        # Parse [STEP] lines
        elif line.startswith("[STEP]"):
            match = re.search(
                r"step=(\d+)\s+action=(\w+)\s+reward=([\d.-]+)\s+done=(\w+)\s+error=(\w+)",
                line
            )
            if match:
                data["step_details"].append({
                    "step": int(match.group(1)),
                    "action": match.group(2),
                    "reward": float(match.group(3)),
                    "done": match.group(4) == "true",
                    "error": None if match.group(5) == "null" else match.group(5),
                })

        # Parse [END] line
        elif line.startswith("[END]"):
            match = re.search(
                r"success=(\w+)\s+steps=(\d+)\s+rewards=([\d.,\s-]+)",
                line
            )
            if match:
                data["success"] = match.group(1) == "true"
                data["steps"] = int(match.group(2))
                rewards_str = match.group(3)
                data["rewards"] = [float(r.strip()) for r in rewards_str.split(",") if r.strip()]

    return data


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

    # Base score from success
    if data["success"]:
        score = 0.7
    else:
        score = 0.0

    # Reward bonus (up to 0.3)
    total_reward = sum(data["rewards"])
    max_possible = 3.80  # As defined in inference.py
    reward_ratio = min(total_reward / max_possible, 1.0) if max_possible > 0 else 0
    score += reward_ratio * 0.3

    # Check for violations
    for step_detail in data["step_details"]:
        if step_detail["reward"] < 0:
            details["penalties"] += 1
            details["violations"].append(f"Step {step_detail['step']}: {step_detail['action']}")

    # Penalty for violations (-0.05 per violation, max -0.15)
    violation_penalty = min(details["penalties"] * 0.05, 0.15)
    score -= violation_penalty

    # Ensure score is in [0, 1]
    score = max(0.0, min(1.0, score))

    details["final_score"] = round(score, 3)

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
    data = parse_inference_output(output)

    # Grade
    score, details = grade_task(data)

    # Print results
    print(f"{'='*60}")
    print(f"GRADING RESULTS")
    print(f"{'='*60}")
    print(f"Task: {data['task']}")
    print(f"Environment: {data['env']}")
    print(f"Model: {data['model']}")
    print(f"")
    print(f"Success: {details['success']}")
    print(f"Steps Taken: {details['steps_taken']}")
    print(f"Total Reward: {details['total_reward']:.2f}")
    print(f"Penalties: {details['penalties']}")

    if details['violations']:
        print(f"Violations:")
        for v in details['violations']:
            print(f"  - {v}")

    print(f"")
    print(f"FINAL SCORE: {details['final_score']:.3f} / 1.000")
    print(f"{'='*60}")

    # Return score as exit code (0-100)
    sys.exit(int(score * 100))


if __name__ == "__main__":
    main()
