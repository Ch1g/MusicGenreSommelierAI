FROM python:3.12-slim

WORKDIR /src

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 3000

ENTRYPOINT ["./entrypoint.sh"]
