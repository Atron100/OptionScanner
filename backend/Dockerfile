FROM python:3.13-slim

WORKDIR /app

COPY backend /app/backend
COPY data /app/data
RUN pip install --no-cache-dir /app/backend

EXPOSE 8000
