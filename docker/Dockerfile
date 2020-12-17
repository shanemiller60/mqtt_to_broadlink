FROM python:3.8-slim

WORKDIR /service
ENV PYTHONPATH=/service
ENV PATH=${PATH}:/service

COPY . .
RUN python3 -m pip install -r requirements.txt

USER 65534:65534

ENTRYPOINT [ "python3", "src/main.py" ]

