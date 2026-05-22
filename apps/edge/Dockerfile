FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn httpx aiosqlite
COPY . .
EXPOSE 8001
CMD ["python", "main.py"]
