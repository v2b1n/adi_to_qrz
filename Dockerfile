FROM python:3.12-slim-bookworm

ADD . /app

RUN mkdir /data && LANG=C pip install -r /app/requirements.txt && chmod 755 /app/*.py

ENV PATH=$PATH:/app

WORKDIR /data

ENTRYPOINT ["/app/adi_to_qrz.py" ]
