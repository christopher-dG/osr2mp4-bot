FROM python:3.8-slim
ENV APT_PKGS build-essential git libavcodec-dev libavformat-dev libfreetype6-dev libjpeg-dev libswscale-dev zlib1g-dev
ENV OSR2MP4_REV 16c6920883cf7d60a853f2b38ed55a06633bab2c
RUN \
  useradd --create-home --uid 1000 bot && \
  apt-get update && \
  apt-get --yes install $APT_PKGS ffmpeg && \
  rm --recursive --force /var/lib/apt/lists && \
  pip install pillow-simd && \
  git clone https://github.com/uyitroa/osr2mp4-core /tmp/osr2mp4-core && \
  cd /tmp/osr2mp4-core/osr2mp4 && \
  git checkout $OSR2MP4_REV && \
  python install.py && \
  cd ImageProcess/Curves/libcurves && \
  python setup.py build_ext --inplace && \
  cd ../../../VideoProcess/FFmpegWriter && \
  python setup.py build_ext --inplace && \
  mv /tmp/osr2mp4-core/osr2mp4 /home/bot/osr2mp4 && \
  chown --recursive bot /home/bot/osr2mp4
COPY requirements.txt /tmp/requirements.txt
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ENV AWS_ACCESS_KEY_ID $AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY $AWS_SECRET_ACCESS_KEY
ENV AWS_DEFAULT_REGION us-east-1
RUN \
  test -n $AWS_ACCESS_KEY_ID && \
  test -n $AWS_SECRET_ACCESS_KEY && \
  pip install --no-cache-dir --requirement /tmp/requirements.txt && \
  apt-get --yes remove $APT_PKGS && \
  apt-get --yes autoremove && \
  rm --recursive --force /tmp/*
USER bot
COPY src/ /home/bot/src
ENV PYTHONPATH /home/bot
CMD python -m src
