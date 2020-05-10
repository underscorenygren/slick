FROM python:3

WORKDIR /opt

RUN apt-get -qq update && \
    apt-get -q -y upgrade && \
    apt-get install -y locales

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8

# https://stackoverflow.com/questions/28405902/how-to-set-the-locale-inside-a-debian-ubuntu-docker-container
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MYSQL_HOST=localhost
ENV MYSQL_USER=root
ENV MYSQL_PORT=3306
ENV MYSQL_DB=scraping
ENV MYSQL_PASSWORD=password
ENV AWS_ACCESS_KEY_ID=
ENV AWS_SECRET_ACCESS_KEY=

ENTRYPOINT [ "python" ]
CMD ["main.py", "--forum", "--tags", "--email", "--concurrent_players"]
