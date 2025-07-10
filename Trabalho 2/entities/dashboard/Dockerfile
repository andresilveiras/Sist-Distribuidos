FROM python:3.10-slim
WORKDIR /app
COPY ./entities/dashboard/ /app
COPY ./shared /app/shared
RUN pip install flask flask-socketio paho-mqtt gunicorn eventlet
EXPOSE 5000
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "main:app"]