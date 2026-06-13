FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --default-timeout=10000 --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
