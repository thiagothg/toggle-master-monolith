FROM python:3.9-slim

# Fator X: Dev/Prod Parity - definir variáveis de build
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=app.py

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

COPY app.py .

# Instalar cliente PostgreSQL para health checks
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["sh", "./entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
