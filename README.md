# RCS Gugulethu Athletics Club Database

This is a Flask App for the RCS Gugulethu running club. It allows you to 

* Search for all races completed by a runner
* Find the top 10 runners in the club for a race
* Predict race times for a runner

The app is hosted on Heroku https://gugs-db.herokuapp.com/

## Table of Contents 
  * [Setup](#setup)
    + [Docker](#docker)
      - [Docker Compose](#docker-compose)
  * [Data](#data)
  * [Prediction](#prediction)
  * [Running the tests](#running-the-tests)
    + [Break down into end to end tests](#break-down-into-end-to-end-tests)
    + [And coding style tests](#and-coding-style-tests)
  * [Deployment](#deployment)
    + [Heroku Postgres](#heroku-postgres)


## Setup
The app was created with Python 3.7.5, but Python 3.5 or later should probably work. Make a virtual environment in your project directory like so:
```
virtualenv -p python3.7 .venv
```
Activate the environment with 
```
source .venv/bin/activate
```
To install the necessary packages in your virtualenv, use 
```
pip install -r requirements.txt
```

### Docker
The Flask app and associated database live inside Docker containers. Docker installation instructions can be found [here](https://docs.docker.com/install/). Note that if you are using an older version of Windows or Windows 10 Home, you will need to install [Docker Toolbox](https://docs.docker.com/toolbox/toolbox_install_windows/). A helpful guide to get this working with Windows Subsystem for Linux is [here](https://nickjanetakis.com/blog/setting-up-docker-for-windows-and-wsl-to-work-flawlessly).

Once installation is done, create your Docker machine
```
docker-machine create --driver virtualbox <name>
```
and set the environment variables
```
eval $(docker-machine env <name>)
```
. Or add the output of `docker-machine env <name>` to your `.bashrc`. 

To start your machine, run 
```
docker-machine start <name>
```

#### Docker Compose

Make a `docker-compose.yml` file that will create Flask and Postgres containers. Here is a snippet for the Flask container.
```dockerfile
version: '3.7' 

services:
  web:
    container_name: flask_sqlalchemy
    build: 
      context: .
    # Useful for debugging
    entrypoint: ["sh", "-c", "sleep 2073600"]
    ports:
      - "5000:5000"
    volumes:
      - ./gugs_db:/code/
    environment: 
      - FLASK_ENV=$FLASK_ENV
    depends_on:
      - database  
    ...
```
You can define multiple services under the `services` block such as `web` or `database`. You can also have services depend on each other under the `depends_on` configuration. The environment variable `FLASK_ENV` will be set to `development` or `production` from the terminal, determining the config to be used.

The `docker-compose.yml` file references a Dockerfile that will pull a base image to work from. It can also include a `requirements.txt` file that will list the packages to be installed into the container. The Dockerfile should be in the same directory as the `docker-compose.yml` file. Generally, it will look for the Dockerfile at the location under the `build` heading and `context` subheading. Some examples of how to write Dockerfiles can be found [here](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

Once you're ready with your Dockerfile and `docker-compose.yml`, do
```
docker-compose up --build -d
```
This will build your images and run the containers in detached mode. You can view the status of your containers using 

```docker
docker ps
```
and your images with 

```docker
docker images
```

To run the flask application in the container, run
```docker
docker exec -it <name_of_flask_container> python <name_of_app_script>.py
```
In my case 
```docker
docker exec -it flask_sqlalchemy python wsgi.py
```
If you prefer to have the app start after container creation, simply comment out the `entrypoint` configuration option. 

The app should be running on localhost at the specified port. If you are using `Docker Toolbox`, this may not actually be accessible on localhost. You will have to get the IP of your docker machine with `docker-machine ip` and then type that into your browser with the appropriate port, for example `192.168.99.100:5000`.

## Data 
The data is taken from the [Western Province Athletics (WPA)](http://www.wpa.org.za/calendar/dynamicevents.aspx) results page. The script `data/wpa_scrape.py` uses `selenium` to download the road race results and save them into the `data/` directory. Those files are then added to the database with `data/load_data.py`, which uses `pandas` and `sqlalchemy` to add records to the `race` table in the database. The table definitions can be found in `app/models.py`. 

Any changes made to the schema are handled using [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/). After creating the `migrations/` folder with `flask db init`, you can migrate changes using `flask db migrate -m "<some message>"` and `flask db upgrade`. It is good to first check that the migration script is correct by looking under `migrations/versions` before upgrading.

## Prediction
The race predictions are made using an ARIMA time series model. Since it is still early in the season (April 2020), there have not been many races yet. In cases where a runner has not run many races, the model collapses to an ARMA model with the differencing term `d = 0`. I have not done extensive validation and testing of the model because most of those techniques do not work well when the data is small. Once there are more races per runner, there will be a chance for better model selection and validation. For now, the parameters for the ARIMA model are set automatically with the `auto_arima` function in the `pmdarima` package.

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

The app is deployed on Heroku. The Heroku CLI installation instructions can be found [here](https://devcenter.heroku.com/articles/heroku-cli).

Start by logging in using `heroku login`. If you are deploying with Docker, you may also need to use `heroku container:login`. Your Docker containers can be pushed to Heroku with the `heroku container:push --app <name>` command. Afterwards, you can release this container with `heroku container:release --app <name>`. In my push command, I had to set the environment variable `FLASK_ENV` to `production` from the terminal and use `heroku container:push web --app <name> --arg FLASK_ENV_ARG=$FLASK_ENV`. This will get picked up by the Dockerfile so that the proper config settings are used. An alternative would be to have separate Dockerfiles for development and production. 

For deployment without Docker, see these [instructions](https://devcenter.heroku.com/categories/deployment).

### Heroku Postgres
You will also need to provision a [Heroku Postgres](https://devcenter.heroku.com/articles/heroku-postgresql) instance with 
```
heroku addons:create heroku-postgresql:<PLAN-NAME>
```
I used the free `hobby-dev` plan.

To load data to the Heroku Postgres instance, first make a backup of your local Postgres data 
```
docker exec <name_of_postgres_container> pg_dump -U <username> -d <dbname> > backup.sql
```

Then add it to the Heroku Postgres instance with 
```
heroku pg:psql --app <name> < backup.sql
```

There are probably better ways to do this, but I have not explored them yet. 