FROM python:3.8-slim
ENV APT_PKGS build-essential git libavcodec-dev libavformat-dev libfreetype6-dev libjpeg-dev libswscale-dev unzip zlib1g-dev
ENV OSU_SKIN_PATH /home/bot/skin
ENV OSR2MP4_REV 7aaf33e7b4798634bb4151a8246dbf2d5ef49cf9
ENV PYTHONPATH /home/bot
RUN \
  useradd --create-home --uid 1000 bot && \
  apt-get update && \
  apt-get --yes install ${APT_PKGS} ffmpeg && \
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
COPY assets/skin.osk /tmp/skin.osk
COPY requirements.txt /tmp/requirements.txt
RUN \
  unzip /tmp/skin.osk -d /home/bot/skin && \
  pip install --requirement /tmp/requirements.txt && \
  apt-get --yes remove ${APT_PKGS} && \
  apt-get --yes autoremove && \
  rm --recursive --force /tmp/*
USER bot
COPY src/ /home/bot/src
