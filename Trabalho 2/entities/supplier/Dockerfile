FROM python:3.10-slim
WORKDIR /app
COPY ./entities/supplier/main.py /app
COPY ./shared /app/shared
RUN pip install paho-mqtt
CMD ["python", "main.py"]
