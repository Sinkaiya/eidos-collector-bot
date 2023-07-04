FROM ubuntu:20.04
RUN apt-get update \
    && apt-get install -y --no-install-recommends pip \
    && pip install mysql-connector-python aiogram aioschedule asyncio
WORKDIR /eidos-collector-bot/
COPY ./config.ini ./main.py /eidos-collector-bot/
CMD /usr/bin/python3 ./main.py
