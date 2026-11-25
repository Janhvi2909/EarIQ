# EarIQ API + web app (CPU build; on a Mac, running natively uses the GPU and is ~2x faster)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    EARIQ_DEVICE=cpu EARIQ_COMPUTE_TYPE=int8 \
    HF_HOME=/models
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 && rm -rf /var/lib/apt/lists/*
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

COPY eariq/ eariq/
COPY app/ app/
COPY models/ models/
COPY results/*.json results/

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s \
  CMD python -c "import urllib.request,json,sys; sys.exit(0 if json.load(urllib.request.urlopen('http://localhost:8000/api/v1/health'))['status']=='ok' else 1)"
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
