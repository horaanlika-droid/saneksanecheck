FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

ENV DATA_DIR=/app/data PORT=8000
VOLUME /app/data
EXPOSE 8000

CMD ["python", "-m", "app.main"]
