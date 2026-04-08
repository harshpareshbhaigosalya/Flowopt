# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# Use the official OpenEnv base image
FROM ghcr.io/meta-pytorch/openenv-base:latest

WORKDIR /app/env

# Ensure git is available
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Copy the environment code
COPY . /app/env

# Install the project and all requirements
# We install it in editable mode or just install the current directory
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Set runtime environment variables
ENV PYTHONPATH="/app/env:$PYTHONPATH"
ENV ENABLE_WEB_INTERFACE=true
ENV PYTHONUNBUFFERED=1

# Expose the application port
EXPOSE 8000

# Health check to ensure the server is responsive
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI server
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port 8000"]
