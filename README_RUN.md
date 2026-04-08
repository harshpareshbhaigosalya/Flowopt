# FlowOpt AI — Workflow Optimization Environment

This project is a production-grade OpenEnv environment for simulating and optimizing remote team workflows.

## Features
- **3 Difficulty Levels**: Easy, Medium, and Hard scenarios.
- **Dynamic Reward System**: Evaluates prioritization, delegation, and bottleneck management.
- **RL-Ready**: Fully compatible with OpenEnv validation and inference scripts.
- **Structured Observations**: Detailed feedback on tasks and team status.

## Project Structure
- `models.py`: Pydantic models for Tasks, Team members, Actions, and Observations.
- `server/Flowopt_environment.py`: Core environment logic and evaluation functions.
- `server/app.py`: FastAPI server entry point.
- `client.py`: OpenEnv client implementation.
- `inference.py`: End-to-end inference script using OpenAI/HuggingFace API.
- `.env`: Environment variables (API keys, model names).

## Prerequisites
- Python 3.10+
- Dependencies: `fastapi`, `uvicorn`, `pydantic`, `openai`, `httpx`, `python-dotenv`, `openenv-core`

Install dependencies:
```bash
pip install fastapi uvicorn pydantic openai httpx python-dotenv openenv-core
```

## How to Run

### 1. Configure Environment
Update the `.env` file with your API key:
```env
HF_TOKEN=your_token_here
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

### 2. Start the Environment Server
Run the following command to start the FastAPI server:
```bash
python -m server.app
```
The server will start at `http://localhost:8000`.

### 3. Run Inference
In a separate terminal, run the inference script to test the agent:
```bash
# Ensure LOCAL_IMAGE_NAME is empty if running against local server
python inference.py
```

## Reward System Breakdown
- **Prioritization**: Max +3 / Min -3 based on urgency and impact.
- **Delegation**: Max +2 / Min -2 based on skill matching.
- **Bottleneck Detection**: Max +3 / Min -3 based on workload balance.
- **Progress Bonus**: +1 for improvement across steps.
- **Loop Penalty**: -1 for repeated identical actions.
- **Final Score**: Normalized to `[0, 1]`.

## Validation
The environment follows the mandatory stdout format for OpenEnv:
- `[START] task=<task> env=<env> model=<model>`
- `[STEP] step=<n> action=<action> reward=<r> done=<d> error=<e>`
- `[END] success=<s> steps=<n> score=<score> rewards=<r1,r2...>`
