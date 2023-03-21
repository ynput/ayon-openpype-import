FROM python:3.11
ENV PYTHONUNBUFFERED=1

RUN pip install poetry

RUN mkdir /service
COPY . /service
WORKDIR /service

RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

CMD ["python", "-m", "processor"]
