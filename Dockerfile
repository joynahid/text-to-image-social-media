FROM python:3.12-slim

WORKDIR /app

# Copy project files first
COPY pyproject.toml .
COPY main.py .
COPY fonts ./fonts

# Install uv and dependencies
RUN pip install uv
RUN uv pip install --system fastapi playwright uvicorn

# Install Playwright browsers and dependencies
RUN playwright install --with-deps chromium

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
