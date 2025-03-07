FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir
 
COPY ./bot .

CMD ["python", "bot.py"]