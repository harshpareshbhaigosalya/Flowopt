"""
Inference Script for FlowOpt AI — Workflow Optimization
=======================================================
This script runs the inference loop for the FlowOpt environment.
"""

import asyncio
import os
import json
import textwrap
from typing import List, Optional, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from openai import OpenAI

# Updated imports for the Flowopt environment
from client import FlowoptEnv
from models import FlowoptAction, FlowoptObservation
from dotenv import load_dotenv
load_dotenv()

IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME") or os.getenv("IMAGE_NAME")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
TASK_NAME = os.getenv("TASK", "workflow-optimization")
BENCHMARK = os.getenv("BENCHMARK", "Flowopt")
MAX_STEPS = 5
TEMPERATURE = 0.2
MAX_TOKENS = 500
SUCCESS_SCORE_THRESHOLD = 0.6

# Scoring: Each step maxes at 1.0 reward. Total max for episode is MAX_STEPS.
MAX_TOTAL_REWARD = float(MAX_STEPS)

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert Project Manager AI. You are optimizing a remote team workflow.
    Your goal is to maximize total reward by:
    1. Prioritizing tasks (Urgent + High Impact first).
    2. Delegating to correct team members (Match skills).
    3. Avoiding bottlenecks (Keep workloads balanced).

    Output your decision in EXACT JSON format ONLY:
    {
      "priority_order": [id1, id2, id3],
      "assignments": {
        "MemberName1": [id1, id2],
        "MemberName2": [id3]
      }
    }
    Do not add any text before or after the JSON.
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def build_user_prompt(step: int, obs: FlowoptObservation) -> str:
    tasks_info = "\n".join([f"- ID {t.id}: {t.description} (Deadline: {t.deadline}, Impact: {t.impact}, Skill: {t.required_skill})" for t in obs.tasks])
    team_info = "\n".join([f"- {m.name}: {m.skill} (Current Workload: {m.workload})" for m in obs.team])
    
    return textwrap.dedent(
        f"""
        Step: {step}
        Available Tasks:
        {tasks_info}

        Team Members:
        {team_info}

        Status Message: {obs.status_message}
        
        Provide your next action in JSON.
        """
    ).strip()


def get_model_action(client: OpenAI, step: int, obs: Any) -> Optional[FlowoptAction]:
    user_prompt = build_user_prompt(step, obs)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        # Extract JSON if model added prose
        if "{" in text:
            text = text[text.find("{"):text.rfind("}")+1]
        
        data = json.loads(text)
        return FlowoptAction(**data)
    except Exception as exc:
        print(f"[DEBUG] Model request or parsing failed: {exc}", flush=True)
        return None


async def main() -> None:
    # Initialize OpenAI client
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Use the TASK_ID from environment or default to all 3 for the judge
    configured_task = os.getenv("TASK_ID")
    tasks_to_run = [configured_task] if configured_task and configured_task != "all" else ["easy", "medium", "hard"]

    # Initialize environment with Docker fallback
    env = None
    if IMAGE_NAME:
        try:
            print(f"[DEBUG] Attempting to start environment via Docker: {IMAGE_NAME}")
            env = await FlowoptEnv.from_docker_image(IMAGE_NAME)
        except Exception as e:
            print(f"[DEBUG] Docker initialization failed: {e}. Falling back to local server.")
            env = FlowoptEnv(base_url="http://localhost:8000")
    else:
        env = FlowoptEnv(base_url="http://localhost:8000")

    try:
        for task_id in tasks_to_run:
            rewards = []
            steps_taken = 0
            score = 0.0
            success = False

            log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

            reset_result = await env.reset(task_id=task_id) 
            obs = reset_result.observation

            for step in range(1, MAX_STEPS + 1):
                if reset_result.done:
                    break

                action = get_model_action(client, step, obs)
                
                if action is None:
                    action = FlowoptAction(priority_order=[], assignments={})

                step_result = await env.step(action)
                obs = step_result.observation
                reward = step_result.reward or 0.0
                done = step_result.done

                rewards.append(reward)
                steps_taken = step
                
                log_step(step=step, action=json.dumps(action.dict()), reward=reward, done=done, error=None)

                if done:
                    break

            score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
            score = min(max(score, 0.0), 1.0)
            success = score >= SUCCESS_SCORE_THRESHOLD
            
            log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    except Exception as e:
        print(f"[ERROR] Inference failed: {e}")
    finally:
        try:
            await env.close()
        except Exception as e:
            pass


if __name__ == "__main__":
    asyncio.run(main())