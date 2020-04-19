FROM python:3.8.2
RUN apt-get update
RUN apt-get install -y wget gzip
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
COPY ./source/ /usr/src/app/
CMD cd /usr/src/app/ && python main.py
