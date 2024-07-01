#Python base image
FROM python:3.9-slim

#set environments variable
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

#set the working directory
WORKDIR /django-app

#install python dependencies
COPY requirements.txt /django-app
RUN pip install -r requirements.txt

#copy all files
COPY . /django-backend/

#Expose port 8000
EXPOSE 8000

#run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "SupplyAPI.wsgi:application"]