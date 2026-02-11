FROM python:3.12

# Install ffmpeg curl
RUN apt-get update && apt-get install -y ffmpeg curl

# Set the working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 依存関係をインストール
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

# アプリケーションをコピー
COPY src/ /app/src/

# PYTHONPATHを追加
ENV PYTHONPATH=/app/src

# Run the application
CMD ["uv", "run", "python3", "src/main.py"]
