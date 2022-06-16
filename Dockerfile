FROM python:3.10-alpine

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apk update && apk add --update --no-cache g++ gcc libxslt-dev libxml2 libxml2-dev ca-certificates tzdata

RUN mkdir /build

WORKDIR /build

COPY ./requirements.txt ./MANIFEST.in ./VERSION ./project.py ./setup.py ./
COPY drag_parser/ ./drag_parser

RUN python -m venv venv

RUN venv/bin/python setup.py install


EXPOSE 7000
ENTRYPOINT ["venv/bin/uvicorn", "drag_parser.api:app", "--host", "0.0.0.0", "--port", "7000"]
