FROM python:3.8-slim
COPY requirements.txt /tmp/requirements.txt
RUN \
  useradd --create-home bot && \
  pip install --no-cache-dir --requirement /tmp/requirements.txt && \
  rm /tmp/requirements.txt
USER bot
COPY src/ /home/bot/src
ENV PYTHONPATH /home/bot
