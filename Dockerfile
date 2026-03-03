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

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy all project files
COPY . .

# Run FastAPI (not CLI). PYTHONPATH so "api.app" resolves; cwd stays /app for templates/data.
ENV PYTHONPATH=/app/src
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]