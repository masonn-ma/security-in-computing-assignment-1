FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY . .
RUN git config --system --add safe.directory /workspace \
    && mkdir -p /usr/local/lib \
    && gcc -shared -fPIC -O2 \
       -I/workspace/vendor/ascon-c/crypto_aead/asconaead128/opt64 \
       -I/workspace/vendor/ascon-c/tests \
       /workspace/vendor/ascon-c/crypto_aead/asconaead128/opt64/aead.c \
       -o /usr/local/lib/libascon_aead.so \
    && gcc -shared -fPIC -O2 \
       -I/workspace/vendor/ascon-c/crypto_hash/asconhash256/opt64 \
       -I/workspace/vendor/ascon-c/tests \
       /workspace/vendor/ascon-c/crypto_hash/asconhash256/opt64/hash.c \
       -o /usr/local/lib/libascon_hash.so
ENV PYTHONPATH=/workspace/src
ENV ASCON_LIBRARY_DIR=/usr/local/lib
CMD ["python", "-m", "crypto_bench", "preflight"]
