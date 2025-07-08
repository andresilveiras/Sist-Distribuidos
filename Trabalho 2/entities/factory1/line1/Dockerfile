FROM python:3.10-slim
WORKDIR /app
COPY ./entities/factory1/line1/main.py /app
COPY ./shared /app/shared
RUN pip install paho-mqtt
CMD ["python", "main.py"]
