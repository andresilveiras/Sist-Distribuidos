# Usa uma imagem base do Python
FROM python:3.9-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

COPY ./entities/sales_center/main.py /app
COPY ./shared /app/shared
RUN pip install paho-mqtt
CMD ["python", "-u", "main.py"]