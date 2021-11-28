# RCS Gugulethu Athletics Club Database

This is a Flask App for the RCS Gugulethu running club. It allows you to 

* Search for all races completed by a runner
* Find the top 10 runners in the club for a race
* Predict race times for a runner

The app is hosted on Heroku https://gugs-db.herokuapp.com/

## Table of Contents

  - [Setup](#setup)
    - [Docker](#docker)
    - [Docker Compose](#docker-compose)
    - [Installing pg_trgm Postgres extension](#installing-pg_trgm-postgres-extension)
  - [Data](#data)
  - [Prediction](#prediction)
  - [Running the tests](#running-the-tests)
    - [Database tests](#database-tests)
    - [View function tests](#view-function-tests)
  - [Deployment](#deployment)
    - [Heroku Postgres](#heroku-postgres)


## Setup

The app was created with Python 3.7.5, but Python 3.5 or later should probably work. Make a virtual environment in your project directory like so:
```bash
virtualenv -p python3.7 .venv
```
Activate the environment with 
```bash
source .venv/bin/activate
```
To install the necessary packages in your virtualenv, use 
```bash
pip install -r requirements.txt
```

### Docker

The Flask app and associated database live inside Docker containers. Docker installation instructions can be found [here](https://docs.docker.com/install/). Note that if you are using an older version of Windows or Windows 10 Home, you will need to install [Docker Toolbox](https://docs.docker.com/toolbox/toolbox_install_windows/). A helpful guide to get this working with Windows Subsystem for Linux is [here](https://nickjanetakis.com/blog/setting-up-docker-for-windows-and-wsl-to-work-flawlessly).

Once installation is done, create your Docker machine
```bash
docker-machine create --driver virtualbox <name>
```
and set the environment variables
```bash
eval $(docker-machine env <name>)
```
. Or add the output of `docker-machine env <name>` to your `.bashrc`. 

To start your machine, run 
```bash
docker-machine start <name>
```

### Docker Compose

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

The `docker-compose.yml` file references a Dockerfile that will pull a base image to work from. It includes a `requirements.txt` file that lists the packages to be installed into the container. The Dockerfile should be in the same directory as the `docker-compose.yml` file. Generally, it will look for the Dockerfile at the location under the `build` heading and `context` subheading. Some examples of how to write Dockerfiles can be found [here](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

Once the Dockerfile and `docker-compose.yml` are ready, run
```bash
docker-compose up --build -d
```
This will build your images and run the containers in detached mode. The status of your containers can be viewed using 

```bash
docker ps
```
and your images with 

```bash
docker images
```

To run the flask application in the container, run

```bash
docker exec -it <name_of_flask_container> python <name_of_app_script>.py
```

In my case 
```bash
docker exec -it flask_sqlalchemy python wsgi.py
```

If you prefer to have the app start after container creation, simply comment out the `entrypoint` configuration option. 

The app should be running on localhost at the specified port. If you are using `Docker Toolbox`, this may not be accessible on localhost. You will have to get the IP of your docker machine with `docker-machine ip`, and then type the resulting IP into your browser with the appropriate port, for example `192.168.99.100:5000`.

### Installing pg_trgm Postgres extension

Note that the function `similarity` requires the extension `pg_trgm` to be installed in Postgres. When the postgres container is running, run
```
docker exec -it postgres_sqlalchemy psql -d <db_name> -U <user> -c 'CREATE EXTENSION pg_trgm;'
``` 
After running this command, the `similarity` function should now work. Test this by searching for a runner or race.

The `CREATE EXTENSION pg_trgm;` command could be added to the `docker-compose.yml` as an entrypoint or cmd for the container. This would be worth exploring.

## Data 

The data is taken from the [Western Province Athletics (WPA)](http://wpa.myactiveweb.co.za/calendar/dynamicevents.aspx) results page. The script `data/wpa_scrape.py` uses `selenium` to download the road race results and save them into the `data/` directory. Selenium requires a [webdriver](https://www.selenium.dev/documentation/getting_started/installing_browser_drivers/) to be installed; this project uses the [chrome webdriver](https://chromedriver.chromium.org/downloads). Download the appropriate version and place it in the `/opt` directory. The location can be changed by modifying the `executable_path` argument in `HiddenChromeDriver` in `data/wpa_scrape.py`. Alternatively, the location can be changed by adding the path of the downloaded driver to the `PATH` variable:

```
export PATH=$PATH:/path/to/chromedriver
```

After being downloaded, the files are added to the database with `data/load_data.py`, using `pandas` and `sqlalchemy` to add records to the `Race` table in the database. The table definitions can be found in `app/models.py`. 

Any changes made to the schema are handled with [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/). After creating the `migrations/` folder with `flask db init`, you can migrate changes using `flask db migrate -m "<some message>"` and `flask db upgrade`. It is good to first check that the migration script is correct by looking in `migrations/versions` before upgrading.

## Prediction

The race predictions are made using an ARIMA time series model. Since it is still early in the season (April 2020), there have not been many races yet. In cases where a runner has not run many races, the model collapses to an ARMA model with the differencing term `d = 0`. I have not done extensive validation and testing of the model because most of those techniques do not work well when the time series is short. Once there are more races per runner, there will be a better opportunity for model selection and validation. For now, the parameters for the ARIMA model are set automatically with the `auto_arima` function in the `pmdarima` package.

## Running the tests

Set `FLASK_ENV` to `testing`. You will also need to make sure the testing database is up in a docker container. To do this, run `docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d`. After the containers are running, use `pytest -v`. The `--disable-warnings` flag can be added to suppress warnings output.

### Database tests

The tests found in `tests/test_db.py` test whether a new user can be successfully added to the database

To run these tests only, use
```bash
pytest -v tests/test_db.py
```

### View function tests

The tests in `tests/test_wsgi.py` test the view functions in `routes.py`. They test the following:

- Proper loading of Home Page
- Login and Logout for Admin Users
- Race search by runner
- Top 10 runners by race
- Race prediction by runner

Each test checks that the response code is 200 and that the correct output is returned.

To run these tests, use
```
pytest -v tests/test_wsgi.py
```

## Deployment

The app is deployed on Heroku. The Heroku CLI installation instructions can be found [here](https://devcenter.heroku.com/articles/heroku-cli).

Start by logging in using `heroku login`. If you are deploying with Docker, you may also need to log in with `heroku container:login`. Your Docker containers can be pushed to Heroku with the `heroku container:push <web-service-name-in-docker-compose.yml> --app <name>` command. Afterwards, you can release this container with `heroku container:release <web-service-name-in-docker-compose.yml> --app <name>`. In my push command I set `FLASK_ENV` to `production` and run `heroku container:push web --app <name> --arg FLASK_ENV_ARG=$FLASK_ENV`, where `web` is the name of the frontend service in `docker-compose.yml`. This will get picked up by the Dockerfile so that the proper config settings are used. An alternative would be to have separate Dockerfiles for development and production. 

For deployment without Docker, see these [instructions](https://devcenter.heroku.com/categories/deployment).

### Heroku Postgres

You will also need to provision a [Heroku Postgres](https://devcenter.heroku.com/articles/heroku-postgresql) instance with 

```bash
heroku addons:create heroku-postgresql:<PLAN-NAME>
```
I used the free `hobby-dev` plan.

To load data to the Heroku Postgres instance, first make a backup of your local Postgres data 

```bash
docker exec <name_of_postgres_container> pg_dump -U <username> -d <dbname> > backup.sql
```

Then add it to the Heroku Postgres instance with 
```bash
heroku pg:psql --app <name> < backup.sql
```

There are probably better ways to do this, but I have not explored them yet.
