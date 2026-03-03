#!/bin/sh
set -e
cd /app
export PYTHONPATH=/app/src

# Run pipeline with Jessica intake once (if PDF exists), then start API so the service stays up
if [ -f data/jessica_intake.pdf ]; then
  echo "Running pipeline for data/jessica_intake.pdf..."
  python src/main.py data/jessica_intake.pdf || true
fi

echo "Starting API server on port ${PORT:-8000}..."
exec python -m uvicorn api.app:app --host 0.0.0.0 --port "${PORT:-8000}"
