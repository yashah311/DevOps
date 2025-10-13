FROM jenkins/jenkins:lts

LABEL maintainer="Yash Shah <https://github.com/yashah311>"
USER root

# Install Docker CLI using official script
RUN apt-get update && \
    apt-get install -y \
      ca-certificates \
      curl \
      gnupg2 \
      lsb-release && \
    curl -fsSL https://get.docker.com | sh

RUN usermod -aG docker jenkins

USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV JENKINS_USER=jenuser
ENV JENKINS_PASS=myP@ss12

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
COPY default-user.groovy /usr/share/jenkins/ref/init.groovy.d/
