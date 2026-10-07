FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv==0.11.31
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev && useradd --uid 10001 --create-home agent && mkdir /data && chown agent:agent /data
USER agent
ENV DEEPAGENT_BIND=0.0.0.0 DEEPAGENT_DATABASE=/data/deepagent.sqlite
EXPOSE 8100
CMD ["/app/.venv/bin/python", "-m", "deep_agent"]
