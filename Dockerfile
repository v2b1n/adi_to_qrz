FROM debian:buster-slim

RUN echo "deb http://ftp.de.debian.org/debian buster main contrib non-free \n\
deb http://ftp.de.debian.org/debian-security buster/updates main contrib non-free \n\
deb http://ftp.de.debian.org/debian buster-backports main contrib non-free \n\
deb http://ftp.de.debian.org/debian buster-updates main contrib non-free" > /etc/apt/sources.list

RUN mkdir -p /usr/share/man/man1

#VOLUME /app
WORKDIR /app

RUN export LANG=C; export DEBIAN_FRONTEND=noninteractive; \
  apt-get update; apt-get -y install --no-install-recommends \
  python-requests \
  python-xmltodict \
  python-dateutil \
  flake8 \
  pylint

#RUN cd /app; flake8 *.py
