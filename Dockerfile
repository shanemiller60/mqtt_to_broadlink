FROM python:3.10 AS build

COPY . .
# The install needs a full python image with gcc, crypto libs/headers etc
# redirect output to /install so it can be copied later in the main image
RUN python3 -m pip install --prefix=/install -r requirements.txt

# Start the final output image
FROM python:3.10-slim

WORKDIR /service
ENV PYTHONUNBUFFERED true
COPY . .

# Copy wheels/packages build in build image
COPY --from=build /install /usr/local

USER 65534:65534

ENTRYPOINT [ "/service/scripts/run.sh" ]

