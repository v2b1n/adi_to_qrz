FROM debian:bullseye-slim

RUN echo "deb http://ftp.de.debian.org/debian bullseye main contrib non-free \n\
deb http://ftp.de.debian.org/debian-security bullseye/updates main contrib non-free \n\
deb http://ftp.de.debian.org/debian bullseye-proposed-updates main contrib non-free \n\
deb http://ftp.de.debian.org/debian bullseye-updates main contrib non-free" > /etc/apt/sources.list

RUN mkdir -p /usr/share/man/man1

RUN export LANG=C; export DEBIAN_FRONTEND=noninteractive; \
  apt-get update; apt-get -y install --no-install-recommends \
  python3-requests \
  python3-xmltodict \
  python3-dateutil \
  flake8 \
  pylint

ADD . /app
ENV PATH=$PATH:/app

WORKDIR /app
