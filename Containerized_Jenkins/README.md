# My-Jenkins
This is an open project to customize and build docker image for jenkins custom plugins installation

### Pre-requisites: Installing latest docker and docker-compose on the instance

## Step 0: Clone the repository onto the instance
```
$ cd /opt/workspace
$ git clone <url.git>
```
## Step 1: Build the docker image 
```
$ cd /opt/workspace/Containerized_Jenkins/build
$ docker build -t my-jenkins:v1.0 .
```
## Step 2: Start the custom jenkins container using docker-compose
```
$ cd /opt/workspace/Containerized_Jenkins
$ docker-compose up -d
```
## Step 2: Start the custom jenkins container without using docker-compose
```
$ cd /opt/workspace/Containerized_Jenkins
$ docker run -d -it --network host --name newjenkins -p 8080:8080 -p 50000:50000 my-jenkins:v1.0
```
