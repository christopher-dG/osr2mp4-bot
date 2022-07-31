FROM python:3.8-slim
ENV PYTHONPATH /home/bot
RUN useradd --create-home --uid 1000 bot
COPY requirements.txt /tmp/requirements.txt
RUN \
  pip install --requirement /tmp/requirements.txt && \
  rm --recursive --force /tmp/*
USER bot
COPY src/ /home/bot/src
CMD [ "tail", "-f", "/dev/null" ]
