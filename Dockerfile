FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir . && \
    pip install --no-cache-dir aiogram[fast]

CMD ["python", "-m", "examples.simple_bot"]
