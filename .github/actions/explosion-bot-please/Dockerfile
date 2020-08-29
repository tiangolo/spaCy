FROM python:3.7

RUN pip install httpx PyGithub "pydantic==1.5.1" "typer==0.3.2"

WORKDIR /app

ENV PYTHONPATH=/app

COPY ./app /app/app

CMD ["python", "-m", "app"]
