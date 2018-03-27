# Punk Deploy

## Are you feeling lucky…?

This is a light-weight tool for building, deploying, backing-up and moving
server environments based on **Docker Compose**. It also integrates with
**Docker Machine** to create, initialize and migrate server nodes across most
cloud providers.


## Prerequisites

* You will need a master server running that will store the volume backups. It
  must have SSH server setup so you can access it with just your public key.
  Also it must have it’s own SSH keypair for logging into the new node machines.
* You will need access to a container registry where you can push your Docker
  images. This can be provided by docker.com, another cloud provider, or you
  can run it yourself on the master server using
  [this docker image](https://hub.docker.com/r/_/registry/).
* An account with a cloud provider supported by Docker Machine (currently
  Digital Ocean and Scaleway are supported out-of-the box but it should be
  simple to add support for others)
* A `docker-compose.yml` file that will define what services you will run. You
  can use the example one we provide if you don’t have one yet.


## Getting started

Copy `settings.py.example` to `settings.py` and modify it to suit your needs.

There’s an example Docker Compose file if you want to copy
`docker-compose.yml.example` to `docker-compose.yml`.

It’s best if you have a virtualenv/pipenv and install the Python requirements

    ./run.py
