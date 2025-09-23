# BASE:
FROM nexus.crowncastle.com:8843/base-image-python-3-12-alpine-3-20:latest AS base
WORKDIR /
COPY requirements.txt requirements.txt
COPY ./src ./src
RUN pip install --no-cache-dir --upgrade --target /package -r requirements.txt \
  && apk add --update --no-cache zip

# TEST:
FROM base AS test
COPY ./requirements.dev.txt requirements.dev.txt
RUN pip install --no-cache-dir --upgrade -r requirements.dev.txt \
  && pip install --no-cache-dir --upgrade -r requirements.txt
RUN ["chmod", "+x", "src/test.sh"]
CMD ["sh", "src/test.sh"]

# ARTIFACT:
FROM base AS artifact
RUN find . -name '*_test.py' -delete
COPY ./copy-artifact.sh copy-artifact.sh
RUN chmod +x copy-artifact.sh
CMD ["/bin/sh", "copy-artifact.sh"]

# DOC:
FROM base AS doc
COPY ./pdoc.sh pdoc.sh
COPY ./requirements.txt requirements.txt
COPY ./requirements.dev.txt requirements.dev.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt \
  && pip3 install --no-cache-dir --upgrade -r requirements.dev.txt \
  && chmod +x pdoc.sh
CMD ["/bin/sh", "pdoc.sh"]