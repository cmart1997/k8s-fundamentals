# syntax=docker/dockerfile:1.6
FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8080
ENTRYPOINT ["python", "app.py"]