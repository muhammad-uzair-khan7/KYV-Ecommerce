FROM python:3.11-slim

WORKDIR /app

# FIX: Install uv via standard pip instead of fetching from GitHub Container Registry
RUN pip install --no-cache-dir uv

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install packages from pyproject.toml directly into system
RUN uv pip install --system --no-cache -r pyproject.toml

# Forcefully install FastAPI, Uvicorn, and the correct Google GenAI library
RUN uv pip install --system fastapi uvicorn google-genai

# Copy the rest of the project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the app using uvicorn module
CMD ["python", "-m", "uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]