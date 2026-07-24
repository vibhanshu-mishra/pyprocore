#!/usr/bin/env bash
set -euo pipefail

echo "Starting optional PyProcore FastAPI read API starter..."
echo "No Procore writes, MCP execution, or external AI/model calls are included."
python3 -m uvicorn app.main:app --reload
