FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends chromium fonts-wqy-zenhei ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
RUN useradd --create-home --uid 1000 muse
WORKDIR /app
COPY pyproject.toml uv.lock README.md main.py ./
COPY muse2api/pyproject.toml muse2api/README.md muse2api/LICENSE ./muse2api/
COPY muse2api/src ./muse2api/src
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:$PATH" \
    MUSE2API_HOST=0.0.0.0 \
    MUSE2API_DATA_DIR=/app/data \
    MUSE2API_CHROMIUM_PATH=/usr/bin/chromium
RUN mkdir -p /app/data && chown -R muse:muse /app
USER muse
EXPOSE 18610
CMD ["python", "main.py"]
