# Usa uma imagem base do Python
FROM python:3.10-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

COPY ./entities/factory2/line/main.py /app
COPY ./shared /app/shared
RUN pip install paho-mqtt
CMD ["python", "-u", "main.py"]