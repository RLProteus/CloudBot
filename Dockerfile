FROM python:3.12

WORKDIR /opt/cloudbot
RUN useradd -m cloudbot
RUN chown -R cloudbot:cloudbot /opt/cloudbot
USER cloudbot

COPY requirements.txt /opt/cloudbot
RUN pip install -r requirements.txt
COPY . /opt/cloudbot

ENTRYPOINT [ "python", "-m", "cloudbot" ]