FROM python:3.10-slim
WORKDIR /app
COPY main.py /app
RUN pip install paho-mqtt
CMD ["python", "main.py"]
