FROM python:alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /django-app

COPY requirements.txt /django-app

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
