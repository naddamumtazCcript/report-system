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

# Run pipeline once (Jessica intake), then start API so Render sees a long-running service
RUN chmod +x scripts/start.sh
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "scripts/start.sh"]