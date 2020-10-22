FROM python:3.8-slim
ENV APT_PKGS build-essential git libfreetype6-dev libjpeg-dev unzip zlib1g-dev
ENV OSU_SKIN_PATH /home/bot/skin
ENV PYTHONPATH /home/bot
RUN \
  useradd -m -u 1000 bot && \
  apt-get update && \
  apt-get -y install ${APT_PKGS} ffmpeg && \
  pip install pillow-simd && \
  git clone https://github.com/uyitroa/osr2mp4-core /tmp/osr2mp4-core && \
  cd /tmp/osr2mp4-core/osr2mp4 && \
  python install.py && \
  cd ImageProcess/Curves/libcurves && \
  python setup.py build_ext --inplace && \
  mv /tmp/osr2mp4-core/osr2mp4 /home/bot/osr2mp4 && \
  chown -R bot:root /home/bot/osr2mp4
COPY assets/skin.osk /tmp/skin.osk
COPY requirements.txt /tmp/requirements.txt
RUN \
  unzip /tmp/skin.osk -d /home/bot/skin && \
  pip install -r /tmp/requirements.txt && \
  apt-get -y remove ${APT_PKGS} && \
  apt-get -y autoremove && \
  rm -rf /tmp/*
USER bot
COPY src/ /home/bot/bot
