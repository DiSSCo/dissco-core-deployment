FROM ubuntu:22.04

RUN adduser -disabled-password -u 1000 usr
COPY --chown=usr:usr doi_server /server/doi_server/
COPY --chown=usr:usr handle-9.3.1/ /server/handle-9.3.1/

EXPOSE 2641/tcp
EXPOSE 2641/udp
EXPOSE 8000/tcp

RUN adduser -D -u 1000 java

# Install OpenJDK-11
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean;

USER 1000

ENTRYPOINT ["/server/handle-9.3.0/bin/hdl-server", "/server/doi_server"]
