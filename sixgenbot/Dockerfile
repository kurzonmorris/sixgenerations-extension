FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SIXGENBOT_DATA=/data

WORKDIR /app

COPY sixgenbot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY sixgenbot/ ./sixgenbot/

VOLUME ["/data"]
EXPOSE 8770

HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8770/health', timeout=4).status == 200 else 1)"

CMD ["python", "-m", "sixgenbot", "serve"]
