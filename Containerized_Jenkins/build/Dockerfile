FROM jenkins/jenkins:lts
MAINTAINER Yash Shah <https://github.com/yashah311> 
USER root

RUN apt-get update && \
    apt-get -y install apt-transport-https \
      ca-certificates \
      curl \
      gnupg2 \
      software-properties-common && \
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg > /tmp/dkey; apt-key add /tmp/dkey && \
    add-apt-repository \
      "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
      $(lsb_release -cs) \
      stable" && \
   apt-get update && \
   apt-get -y install docker-ce

RUN usermod -a -G docker jenkins

USER jenkins

# Allows to skip Jenkins setup wizard
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

# Update the username and password
ENV JENKINS_USER jenuser
ENV JENKINS_PASS myP@ss12

# Copying files for custom plugin installation
COPY plugins.txt /usr/share/jenkins/ref/

# Jenkins runs all grovy files from init.groovy.d dir; Using this for creating default admin user
COPY default-user.groovy /usr/share/jenkins/ref/init.groovy.d/

# Installing all the plugins as per plugins.txt
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt

