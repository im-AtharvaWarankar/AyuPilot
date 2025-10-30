FROM python:3.12.2
ENV ENV=prod
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install "drf-yasg[validation]"
RUN pip install git+https://github.com/atomic-loops/atomicloops-django-logger
WORKDIR /opt/
