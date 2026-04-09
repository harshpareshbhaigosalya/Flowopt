# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the FlowOpt AI Environment.
"""

import os
import sys

# Enable the OpenEnv web interface
os.environ["ENABLE_WEB_INTERFACE"] = "true"

# Ensure current directory is in sys.path for imports
sys.path.append(os.getcwd())

try:
    from openenv.core.env_server.http_server import create_app
except ImportError:
    raise ImportError("openenv-core is required. Run 'pip install openenv-core'.")

try:
    # Handle both server.app and Flowopt.server.app styles
    try:
        from env.models import FlowoptAction, FlowoptObservation
        from .Flowopt_environment import FlowoptEnvironment
    except (ImportError, ModuleNotFoundError):
        from models import FlowoptAction, FlowoptObservation
        from server.Flowopt_environment import FlowoptEnvironment
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback for validation tools
    FlowoptAction = None
    FlowoptObservation = None
    FlowoptEnvironment = None

# Create the app
app = create_app(
    FlowoptEnvironment,
    FlowoptAction,
    FlowoptObservation,
    env_name="Flowopt",
    max_concurrent_envs=4,
)

@app.get("/tasks")
async def get_all_tasks():
    """Explicitly expose tasks for the validator."""
    return FlowoptEnvironment.TASKS

def main():
    """Main entry point."""
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
