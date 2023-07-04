FROM ubuntu:20.04
RUN apt-get update \
    && apt-get install -y --no-install-recommends pip
RUN pip install mysql-connector-python aiogram aioschedule asyncio
WORKDIR /eidos-collector-bot/
COPY config.ini main.py /eidos-collector-bot/
CMD python main.py
