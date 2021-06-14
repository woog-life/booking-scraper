FROM python:3.9-slim

WORKDIR /app

ENV TZ=Europe/Berlin

ADD requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ADD booking booking

CMD python -B -O -m booking.main
