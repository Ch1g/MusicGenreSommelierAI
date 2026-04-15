FROM python:3.12-slim

WORKDIR /src

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh
RUN chmod +x worker_entrypoint.sh

EXPOSE 8080

CMD ["echo", "Container started. No default command set. Override with `docker run <image> <your-command>`. For custom entrypoint, use `--entrypoint \"/path/to/script.sh\"` at runtime."]
