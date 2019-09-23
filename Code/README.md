# Django webapp

## Local Ubuntu setup

If you want to run it on your local Ubuntu machine follow these steps.
 
`sudo apt-get install mysql-server`

Set root password als you like. 

`sudo apt-get install libmysqlclient-dev`

Install memcached

`sudo apt-get install memcached`


Connect to database as you root user.

```mysql
CREATE USER 'mpuser' IDENTIFIED BY 'asdf1234';
CREATE DATABASE masterproject CHARACTER SET utf8;
GRANT ALL PRIVILEGES ON masterproject.* TO 'mpuser';
```

Create a venv and activate it.

```commandline
python3 -m venv /path/to/new/virtual/environment
. /path/to/new/virtual/environment/bin/activate
```

`cd` into the checked out repo/code. 

```commandline
pip install -r requirements.txt
cd MasterProject
python3.5 manage.py migrate
python3.5 manage.py createsuperuser
```
set up redis and celery on your machine by following the steps given below.
Setup redis on your machine. You can find instructions in the following link
https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-redis-on-ubuntu-16-04

In a separate terminal, `cd` into the project folder (.../SciPRecommender/Code/MasterProject) and
```commandline
celery worker -A MasterProject -Q PaperManagerQueue --concurrency=4 --loglevel=debug
```

Now start the server on your local machine with the following

```commandline
python3.5 manage.py runserver
```

## Deployment
#### Prerequisites
- fabric
- python2.7, python-jinja2 (`pip2.7 install fabric jinja2`)
- python3.5
- access to SciPRecommender git repository

A fabric script has beed provided for deployment to production server. You do not need to install anything(apart from prerequisites to run the script) as the fabric script takes care of required packages and configurations.



#### Fabric tasks

* `fab prod init:<branch>` installs and configures everything, starts the webapp with branch `<branch>`on deployment machine.
* `fab prod update:<branch>` to update the deployed version `<branch>`.

### First time set up

1. Clone the repository into any folder. A git account with access to the
    repo is required.
2. cd into ScipRecommender/Code folder
3. Open fabfile.py and edit the variable value of
     UNIXUSER to a username in sudoers's list (this user needs to install packages
     so it needs to be a sudo user.)

4. Run the following command `fab prod init`
   It will install all dependencies and start the server at
   hobbes.informatik.uni-freiburg.de:8080. The server logfiles will be
created at home/UNIXUSER/SciPRecommender/logs/gunicorn_supervisor.log

### Update
1. Follow the first three steps from the previous subsection (you do not need to perform them again if already done)
2. Run the following command `fab prod update`

### Mantainance

#### Stoping webapp

```commandline
sudo supervisorctl stop MasterProject
sudo supervisorctl stop redis_fastqueue 
```

#### Restarting webapp

```commandline
sudo supervisorctl restart MasterProject
sudo supervisorctl restart redis_fastqueue 
```