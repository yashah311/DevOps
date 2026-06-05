FROM jenkins/jenkins:2.567

LABEL maintainer="Yash Shah <https://github.com/yashah311>"

# -----------------------------
# ROOT: install Docker CLI
# -----------------------------
USER root

RUN apt-get update && \
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg2 \
        lsb-release && \
    curl -fsSL https://get.docker.com | sh && \
    apt-get clean

RUN usermod -aG docker jenkins

# -----------------------------
# SWITCH BACK TO JENKINS USER
# -----------------------------
USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

# -----------------------------
# Install plugins
# -----------------------------
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

RUN jenkins-plugin-cli \
    --plugin-file /usr/share/jenkins/ref/plugins.txt \
    --verbose

# -----------------------------
# Init script (create user)
# -----------------------------
COPY default-user.groovy /usr/share/jenkins/ref/init.groovy.d/
