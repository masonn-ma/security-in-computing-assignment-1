FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY . .
ENV PYTHONPATH=/workspace/src
CMD ["python", "-m", "crypto_bench", "preflight"]
