FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ESCANEO3D_DATA=/data \
    QT_QPA_PLATFORM=offscreen

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip colmap \
    libgl1 libglib2.0-0 libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements-web.txt ./
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements-web.txt

COPY . .
RUN mkdir -p /data && chown -R 10001:10001 /app /data
USER 10001:10001

EXPOSE 8000
CMD ["/opt/venv/bin/python", "-m", "uvicorn", "tools.servidor_web:app", "--host", "0.0.0.0", "--port", "8000"]
