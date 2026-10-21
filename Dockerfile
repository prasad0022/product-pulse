FROM python:3.11-slim

ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app    

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch; GPU/CUDA libraries are unnecessary.
RUN pip install --no-cache-dir \
    --timeout 300 --retries 10 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.7.1

# Install the remaining project dependencies.
RUN pip install --no-cache-dir \
    --timeout 300 --retries 10 \
    -r requirements.txt

COPY scripts ./scripts
COPY api ./api
COPY src ./src
COPY data ./data
COPY docs ./docs
COPY tests ./tests

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
