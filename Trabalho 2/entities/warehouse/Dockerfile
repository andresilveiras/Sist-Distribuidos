FROM python:3.10-slim
WORKDIR /app
COPY ./shared /app/shared
COPY ./entities/warehouse/main.py /app
RUN pip install paho-mqtt
CMD ["python", "-u", "main.py"]
