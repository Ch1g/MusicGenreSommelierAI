FROM python:3.12-slim

WORKDIR /src

COPY requirements.txt .
COPY app.py .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
