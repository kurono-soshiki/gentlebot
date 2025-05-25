FROM python:3.12

# Install ffmpeg curl
RUN apt-get update && apt-get install -y ffmpeg curl

# Set the working directory
WORKDIR /app

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3
ENV PATH="/root/.local/bin:/root/.poetry/bin:$PATH"

# Poetryを使って依存関係をインストール
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root

# アプリケーションをコピー
COPY src/ /app/src/

# PYTHONPATHを追加
ENV PYTHONPATH=/app/src

# Run the application
CMD ["python3", "src/main.py"]

