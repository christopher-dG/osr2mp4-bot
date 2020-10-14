FROM python:3.8-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ENV PYTHONPATH /root
COPY src/ /root/bot
CMD python -m bot
