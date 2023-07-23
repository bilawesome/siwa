# FROM python:3.10.5-alpine3.16 as prod
FROM python:3.11
# FROM arm64v8/python:latest

RUN mkdir /app/
WORKDIR /app/

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY ./ /app/

# solved.... goto => site-packages/parsimonious/expressions.py and change import line to say..... from inspect import getfullargspec
# /usr/local/lib/python3.11/site-packages
# /usr/local/lib/python3.11/site-packages/parsimonious/expressions.py

EXPOSE 5000

ENV FLASK_APP=endpoint.py
# CMD flask run -h 0.0.0 -p 5000
# CMD python setup.py
CMD python siwa.py --datafeeds mcap1000
