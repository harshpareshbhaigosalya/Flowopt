---
title: FlowOpt AI — Workflow Optimization
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
tags:
  - openenv
  - reinforcement-learning
  - workflow-optimization
---

# FlowOpt AI — Workflow Optimization Environment

FlowOpt AI is a production-grade environment that simulates a remote team workflow. Agents must prioritize tasks, assign them to the correct team members based on skills, and manage workloads to avoid bottlenecks.

## Quick Start

The simplest way to use the FlowOpt environment is through the `FlowoptEnv` class:

```python
from client import FlowoptEnv
from models import FlowoptAction

try:
    # Connect to the local server
    env = FlowoptEnv(base_url="http://localhost:8000")

    # Reset with a specific difficulty level ("easy", "medium", "hard")
    result = env.reset() # Defaults to easy
    print(f"Goal: Optimize {result.observation.remaining_tasks} tasks.")

    # Example: Assigning a Backend task to Alice
    action = FlowoptAction(
        priority_order=[1, 2, 3],
        assignments={"Alice": [1]}
    )

    result = env.step(action)
    print(f"Status: {result.observation.status_message}")
    print(f"Reward: {result.reward}")

finally:
    env.close()
```

## Features
- **3 Difficulty Levels**: Training scenarios for different complexity levels.
- **Skill-Based Delegation**: Match Backend, Frontend, and General skills.
- **Bottleneck Analysis**: Penalizes uneven workload distribution.
- **Robust Rewards**: Multi-faceted reward system normalized to `[0, 1]`.

## Building and Running with Docker

Before using the environment with Docker, ensure **Docker Desktop** is running on your machine.

### 1. Build the Image
```bash
# From the project root
docker build -t flowopt-env:latest .
```

### 2. Run the Container
```bash
docker run -p 8000:8000 flowopt-env:latest
```

## Local Development

If you don't want to use Docker, you can run the server directly:

```bash
python -m server.app
```
The server will be available at `http://localhost:8000`.

## Environment Details

### Action
**FlowoptAction**:
- `priority_order` (List[int]) - Ordered task IDs by priority.
- `assignments` (Dict[str, List[int]]) - Mapping of team members to task IDs.

### Observation
**FlowoptObservation**:
- `tasks` (List[Task]) - List of available tasks with metadata.
- `team` (List[TeamMember]) - Status of team members and workloads.
- `status_message` (str) - Feedback from the previous action.
- `reward` (float) - Current step reward.
- `done` (bool) - Whether the episode is complete.
