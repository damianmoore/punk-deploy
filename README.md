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
  images. This can be provided by Docker Hub, another cloud provider, or you
  can run it yourself on the master server using
  [this docker image](https://hub.docker.com/r/_/registry/).
* An account with a cloud provider supported by Docker Machine (currently
  Digital Ocean and Scaleway are supported out-of-the box but it should be
  simple to add support for others)
* A `docker-compose.yml` file that will define what services you will run. You
  can use the example one we provide if you don’t have one yet.


## Getting started

Clone the project and `cd` into it.

    git clone git@github.com:damianmoore/punk-deploy.git
    cd punk-deploy/

Copy the example settings file and modify it to suit your needs. You will need
to fill in your access credentials for the cloud provider you wish to use if you
want to try out the example.

    cp settings.py.example settings.py

There’s an example Docker Compose file you can copy if you don’t have your
own yet.

    cp docker-compose.yml.example docker-compose.yml

It is recommended you use `pipenv` to create the virtual environment, install
the dependencies and run.

    pipenv install
    pipenv shell
    ./run.py

If you want to use the example Docker Compose file you copied earlier, go
through the following steps in the CLI menu to create a new machine and deploy a
site.

* Create new machine
* Initialize machine
* Initialize/recreate docker containers

If you followed the steps above you should have a Django site running that you
can access in your browser. You can find the IP address for the new machine by
running `./run.py` again and selecting *View machines*.

You can SSH into your new machine with the `docker-machine` command.

    docker-machine ssh MACHINE_NAME

You can link the current terminal to the remote Docker instance so you can use
the `docker` and `docker-compose` commands like you would locally.

    eval $(docker-machine env MACHINE_NAME)
    docker ps
