FROM python:3.13.0-alpine3.20

WORKDIR /home/app

COPY main.py /home/app/main.py
COPY utils/functions.py /home/app/utils/functions.py
COPY utils/cli.py /home/app/utils/cli.py
COPY config.yaml /home/app/config.yaml
COPY requirements.txt /home/app/requirements.txt

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "/home/app/main.py"]
