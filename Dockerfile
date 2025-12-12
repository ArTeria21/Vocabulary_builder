# syntax=docker/dockerfile:1

# ============================================
# Stage 1: Build environment with uv
# ============================================
FROM python:3.12-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# ============================================
# Stage 2: Runtime environment
# ============================================
FROM python:3.12-slim AS runtime

# Create non-root user for security
RUN groupadd --gid 1000 botuser && \
    useradd --uid 1000 --gid 1000 --create-home botuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=botuser:botuser main.py ./
COPY --chown=botuser:botuser src/ ./src/
COPY --chown=botuser:botuser prompts/ ./prompts/

# Create data directory with correct permissions
RUN mkdir -p /app/data && chown -R botuser:botuser /app/data

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER botuser

# Health check (optional, checks if process is running)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python main.py" || exit 1

# Run the bot
CMD ["python", "main.py"]

