# Use Python 3.11 slim as base
FROM python:3.11-slim

# Install build essentials & curl for Rust
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY requirements.txt .

# Create and use virtual environment
RUN python -m venv /app/venv \
    && . /app/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Ensure venv is used for all subsequent RUN/CMD
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy all project files
COPY . .

# Expose app port
ENV PORT=8000
EXPOSE 8000

# Run the FastAPI app equivalent to:
#   source venv/bin/activate
#   cd src
#   python3 -m uvicorn api.app:app --reload
WORKDIR /app/src
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]