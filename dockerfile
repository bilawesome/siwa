# FROM python:3.10.5-alpine3.16 as prod
FROM arm64v8/python:latest

RUN mkdir /app/
WORKDIR /app/

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY ./ /app/

EXPOSE 5000

ENV FLASK_APP=endpoint.py
# CMD flask run -h 0.0.0 -p 5000
CMD python setup.py
CMD python siwa.py --datafeeds mcap1000
