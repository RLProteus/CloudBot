FROM python:3.12-alpine3.20

WORKDIR /opt/cloudbot
RUN adduser -D cloudbot
RUN chown -R cloudbot:cloudbot /opt/cloudbot
RUN apk update && apk add python3-dev \
                      gcc \
                      libc-dev \
                      libffi-dev
USER cloudbot

COPY requirements.txt /opt/cloudbot
RUN pip install -r requirements.txt
COPY . /opt/cloudbot

ENTRYPOINT [ "python", "-m", "cloudbot" ]
