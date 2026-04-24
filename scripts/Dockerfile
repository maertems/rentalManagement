FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pymysql requests
COPY reset_database.py generate_receipt.py ./
