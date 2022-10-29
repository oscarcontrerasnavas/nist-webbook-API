FROM python:3.10.5-alpine
WORKDIR /app
COPY . .
RUN apk add gcc libc-dev libffi-dev
RUN python -m pip install -r requirements.txt
CMD scrapyrt -S nist_scraper.scrapyrt.settings -i 0.0.0.0 -p 8080