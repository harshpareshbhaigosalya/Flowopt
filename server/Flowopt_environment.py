# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FlowOpt AI — Workflow Optimization Environment Implementation.

This environment evaluates an RL agent's ability to prioritize tasks,
delegate effectively to team members, and manage workflow bottlenecks.
"""

from uuid import uuid4
from typing import Dict, List, Set, Any
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from env.models import FlowoptAction, FlowoptObservation, Task, TeamMember
except ImportError:
    from models import FlowoptAction, FlowoptObservation, Task, TeamMember


class FlowoptEnvironment(Environment):
    """
    A production-grade environment for workflow optimization.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    TASKS = [
        {"id": "easy", "name": "Easy Workflow Triage"},
        {"id": "medium", "name": "Medium Priority Scheduling"},
        {"id": "hard", "name": "Hard Resource Desert"},
    ]

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Returns the list of available tasks for this environment."""
        return self.TASKS

    def __init__(self):
        """Initialize the Flowopt environment."""
        self._reset_state()

    def _reset_state(self):
        """Internal helper to reset environment state."""
        self._episode_id = str(uuid4())
        self._step_count = 0
        self._cumulative_score = 0.0
        self._history = []
        self._tasks: List[Task] = []
        self._team: List[TeamMember] = []
        self._completed_tasks: Set[int] = set()

    def reset(self, task_id: str = "easy") -> FlowoptObservation:
        """
        Reset the environment with a specific scenario.
        
        Args:
            task_id: Scenario identifier ("easy", "medium", "hard")
        
        Returns:
            FlowoptObservation: The initial state of the environment.
        """
        self._reset_state()
        self._load_scenario(task_id)

        return self._get_observation("Environment initialized.")

    def _load_scenario(self, task_id: str):
        """Loads task scenarios for different difficulty levels."""
        if task_id == "easy" or task_id is None:
            # FOCUS: Simple 1:1 expert matching
            self._tasks = [
                Task(id=1, description="Critical Backend Crash", deadline=2, impact=5, required_skill="Backend"),
                Task(id=2, description="UI Button Alignment", deadline=5, impact=2, required_skill="Frontend"),
                Task(id=3, description="Weekly Documentation", deadline=10, impact=1, required_skill="General"),
            ]
            self._team = [
                TeamMember(name="Alice", skill="Backend", workload=0),
                TeamMember(name="Bob", skill="Frontend", workload=0),
                TeamMember(name="Charlie", skill="General", workload=0),
            ]
        elif task_id == "medium":
            # FOCUS: Strategic Triage (Urgency vs Impact)
            self._tasks = [
                Task(id=1, description="API OAuth Fix", deadline=3, impact=4, required_skill="Backend"),
                Task(id=2, description="Slow DB Query", deadline=3, impact=5, required_skill="Backend"), # Higher impact, same deadline
                Task(id=3, description="Mobile Responsive Fix", deadline=4, impact=3, required_skill="Frontend"),
                Task(id=4, description="Onboarding Draft", deadline=5, impact=2, required_skill="General"),
                Task(id=5, description="Readme Update", deadline=5, impact=1, required_skill="General"), # Lower impact, same deadline
            ]
            self._team = [
                TeamMember(name="James", skill="Backend", workload=0),
                TeamMember(name="Sarah", skill="Frontend", workload=0),
                TeamMember(name="Alex", skill="General", workload=0),
            ]
        elif task_id == "hard":
            # FOCUS: Executive Crisis (The Resource Desert)
            # 7 Tasks but only 2 team members. The agent MUST ignore low impact tasks to succeed.
            self._tasks = [
                Task(id=1, description="Core DB Migration", deadline=1, impact=5, required_skill="Backend"),
                Task(id=2, description="Security Breach Patch", deadline=2, impact=5, required_skill="Backend"),
                Task(id=3, description="Main Landing Page Down", deadline=2, impact=5, required_skill="Frontend"),
                Task(id=4, description="Docker Registry Fix", deadline=3, impact=4, required_skill="Backend"),
                Task(id=5, description="Client Support Tickets", deadline=6, impact=2, required_skill="General"),
                Task(id=6, description="Newsletter Draft", deadline=10, impact=1, required_skill="General"),
                Task(id=7, description="Internal Tool Maintenance", deadline=12, impact=1, required_skill="General"),
            ]
            self._team = [
                TeamMember(name="Expert_A", skill="Backend", workload=0),
                TeamMember(name="Expert_B", skill="Frontend", workload=0),
            ]
        else:
            self._load_scenario("easy")

    def step(self, action: FlowoptAction) -> FlowoptObservation:  # type: ignore[override]
        """
        Execute an optimization step.
        """
        self._step_count += 1
        
        # 1. EVALUATE PRIORITIZATION
        p_score, p_msg = self.evaluate_priority(action.priority_order)
        
        # 2. EVALUATE DELEGATION
        d_score, d_msg = self.evaluate_assignment(action.assignments)
        
        # 3. EVALUATE BOTTLENECK
        b_score, b_msg = self.evaluate_bottleneck(action.assignments)
        
        # Calculate raw step reward
        step_reward = p_score + d_score + b_score
        
        # 4. PROGRESS BONUS / LOOP PENALTY
        p_bonus = 0.0
        if len(self._history) > 0:
            if step_reward > self._history[-1]["reward"]:
                p_bonus = 1.0
            elif action.model_dump() == self._history[-1]["action"]:
                p_bonus = -1.0
        
        total_step_reward = step_reward + p_bonus
        
        # Normalize reward from [min_possible, max_possible] to [0, 1]
        # Max: 3 (priority) + 2 (delegation) + 3 (bottleneck) + 1 (bonus) = 9
        # Min: -3 (priority) - 2 (delegation) - 3 (bottleneck) - 1 (penalty) = -9
        normalized_reward = (total_step_reward + 9) / 18
        
        self._cumulative_score += normalized_reward
        
        # Record history
        self._history.append({
            "step": self._step_count,
            "action": action.model_dump(),
            "reward": normalized_reward,
            "breakdown": {
                "priority": p_score,
                "delegation": d_score,
                "bottleneck": b_score,
                "bonus": p_bonus
            }
        })
        
        # Mark tasks as completed if assigned correctly (simulated progress)
        for _, task_ids in action.assignments.items():
            for tid in task_ids:
                if tid in action.priority_order[:2]: # Only first 2 prioritized tasks get completed
                    self._completed_tasks.add(tid)
        
        # Update team workload for next observation
        for tm in self._team:
            tm.workload = len(action.assignments.get(tm.name, []))

        status_msg = f"{p_msg} {d_msg} {b_msg}".strip()
        done = len(self._completed_tasks) >= len(self._tasks) or self._step_count >= 5
        
        return self._get_observation(status_msg, normalized_reward, done)

    def evaluate_priority(self, priority_order: List[int]) -> (float, str):
        """
        Urgency (deadline) and Impact (impact) should come first.
        """
        # Calculate ideal priority (simplified: deadline asc, impact desc)
        sorted_tasks = sorted(
            [t for t in self._tasks if t.id not in self._completed_tasks],
            key=lambda t: (t.deadline, -t.impact)
        )
        ideal_ids = [t.id for t in sorted_tasks]

        if not ideal_ids:
            return 3.0, "No tasks remaining to prioritize."
        
        if not priority_order:
            return -3.0, "No priority order provided."
        
        match_count = sum(1 for i, tid in enumerate(priority_order) if i < len(ideal_ids) and tid == ideal_ids[i])
        
        if match_count == len(ideal_ids):
            return 3.0, "Perfect prioritization."
        elif match_count >= len(ideal_ids) // 2:
            return 1.0, "Partially correct prioritization."
        else:
            return -3.0, "Inefficient prioritization."

    def evaluate_assignment(self, assignments: Dict[str, List[int]]) -> (float, str):
        """
        Match required skills with team member skills.
        """
        mismatches = 0
        total_assigned = 0
        
        team_map = {tm.name: tm for tm in self._team}
        task_map = {t.id: t for t in self._tasks}
        
        # Count remaining tasks
        rem_tasks = [t for t in self._tasks if t.id not in self._completed_tasks]
        if not rem_tasks:
            return 2.0, "No tasks remaining to delegate."

        for name, tids in assignments.items():
            member = team_map.get(name)
            if not member: continue
            
            for tid in tids:
                task = task_map.get(tid)
                if not task: continue
                total_assigned += 1
                if task.required_skill != member.skill and task.required_skill != "General":
                    mismatches += 1
        
        if total_assigned == 0:
            return -2.0, "No tasks assigned."
        if mismatches == 0:
            return 2.0, "Perfect task delegation."
        else:
            return -2.0, f"Found {mismatches} skill-task mismatches."

    def evaluate_bottleneck(self, assignments: Dict[str, List[int]]) -> (float, str):
        """
        Check if any team member is overloaded while others are idle.
        """
        workloads = [len(tids) for tids in assignments.values()]
        if not workloads:
            return -3.0, "No work distributed."
            
        max_wl = max(workloads)
        min_wl = min(workloads) if len(workloads) == len(self._team) else 0
        
        if (max_wl - min_wl) <= 1:
            return 3.0, "Balanced workload across the team."
        else:
            return -3.0, "High bottleneck risk — workload is unevenly distributed."

    def _get_observation(self, msg: str, reward: float = 0.0, done: bool = False) -> FlowoptObservation:
        """Helper to construct FlowoptObservation."""
        active_tasks = [t for t in self._tasks if t.id not in self._completed_tasks]
        
        # Get last breakdown if exists
        last_breakdown = self._history[-1]["breakdown"] if self._history else None
        
        return FlowoptObservation(
            tasks=active_tasks,
            team=self._team,
            current_step=self._step_count,
            remaining_tasks=len(active_tasks),
            status_message=msg,
            reward=reward,
            done=done,
            score_breakdown=last_breakdown
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state for OpenEnv.
        """
        return State(
            episode_id=self._episode_id,
            step_count=self._step_count,
            metadata={
                "cumulative_score": self._cumulative_score,
                "history": self._history,
                "completed_tasks": list(self._completed_tasks),
                "is_optimized": len(self._completed_tasks) >= len(self._tasks)
            }
        )

    @staticmethod
    def grader(final_score: float, max_steps: int = 5) -> float:
        """
        Normalize final cumulative score to [0,1].
        Since each step reward is already [0,1], max score = max_steps.
        """
        normalized = final_score / max_steps
        return min(max(normalized, 0.0), 1.0)
