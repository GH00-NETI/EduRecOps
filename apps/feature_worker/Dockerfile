FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY packages ./packages
RUN pip install --no-cache-dir .
COPY apps/feature_worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/feature_worker/worker.py ./worker.py
COPY apps/feature_worker/processing.py ./processing.py
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
CMD ["python", "worker.py"]
