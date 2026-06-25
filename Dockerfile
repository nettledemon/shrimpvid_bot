FROM python:3.14-slim

# ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# код
COPY src/ ./src/

# команда по умолчанию (запуск бота)
CMD ["python", "src/main.py"]
