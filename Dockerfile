FROM python:3.6
RUN useradd -d /home/epmonitor -m -s /bin/bash epmonitor

WORKDIR /home/epmonitor

RUN python -m venv venv
RUN venv/bin/pip install gunicorn

COPY app app
COPY stats stats
COPY checks checks
COPY config.py config.py
COPY migrations migrations
COPY setup.py setup.py
COPY setup.cfg setup.cfg
COPY webapp webapp
COPY MANIFEST.in MANIFEST.in
COPY boot.sh ./

RUN chmod +x boot.sh
RUN venv/bin/pip install --upgrade -e .
RUN chown -R epmonitor:epmonitor .

ENV FLASK_APP app

USER epmonitor

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
