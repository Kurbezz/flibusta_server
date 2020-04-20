FROM kurbezz/flibusta_server:latest
RUN apt-get update
RUN apt-get install -y wget gzip mariadb-client
COPY ./source/db_updater.py /usr/src/app/db_updater.py
CMD cd /usr/src/app && python db_updater.py
