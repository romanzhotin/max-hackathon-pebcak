FROM python:3.14.5

WORKDIR /bot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]