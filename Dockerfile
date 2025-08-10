# Base image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY src ./src

EXPOSE 8080

CMD ["uvicorn", "src.webapp.app:app", "--host", "0.0.0.0", "--port", "8080"]

