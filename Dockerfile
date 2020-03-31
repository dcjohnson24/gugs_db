FROM python:3.8-slim-buster
RUN apt-get update -y && apt-get install -y libpq-dev build-essential 
ENV PORT=5000
ARG FLASK_ENV_ARG
ENV FLASK_ENV=${FLASK_ENV_ARG}
COPY . /
WORKDIR /
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -r requirements-ts.txt
RUN useradd gugs
USER gugs
CMD gunicorn -b 0.0.0.0:$PORT wsgi:app