FROM python:3.14-alpine3.23

WORKDIR /src

COPY requirements.txt .
COPY app.py .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]