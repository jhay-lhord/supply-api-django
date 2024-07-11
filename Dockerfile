FROM python:alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /django-app

COPY requirements.txt /django-app

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["sh", "./run-django.sh"]
