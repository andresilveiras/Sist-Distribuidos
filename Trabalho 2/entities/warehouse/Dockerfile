FROM python:3.10-slim
WORKDIR /app
COPY ../../shared /app/shared
COPY main.py /app
RUN pip install paho-mqtt
CMD ["python", "main.py"]
