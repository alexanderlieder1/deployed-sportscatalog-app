# Deployment of Sportscatalog Web Application via AWS
I take a baseline installation of a Linux distribution (Ubuntu) on a virtual machine and prepare it to host the [sportscatalog web app](https://github.com/alexanderlieder1/sportscatalog-web-application). The scope of the project is to configure the Linux machine to secure it against a number of attack vectors. In a second step I will setup a database and web server, which will run the sportscatalog web app.

The application can be accessed via:\
IP - 35.158.194.250\
URL - http://ec2-35-158-194-250.compute-1.amazonaws.com/

### Pre-requisite: Setting up a VM with AWS Lightsail
1) Get Amazon Lightsail:
- Visit https://aws.amazon.com and create a new AWS account.
- Choose Lightsail as a product and ‘Create Instance’ in the Lightsail dashboard
- Choose Ubuntu 16.04 LTS and the lowest tier instance

2) SSH login to AWS machine:
- Go to Account and download the default ssh key.
- Save the key as amazon_udacity_key.rsa and place it in your .ssh folder on your local machine
- Set the right permissions in your local terminal:\
`chmod 600 ~/.ssh/amazon_udacity_key.rsa`
- Now you can connect from your local terminal via:\
`ssh ubuntu@35.158.194.250 -i ~/.ssh/amazon_udacity_key.rsa`

### Secure Linux server
1) Applications update:\
`sudo apt-get update`\
`Sudo apt-get upgrade`

2) Changing SSH port from default (22) to (2200):\
`sudo nano /etc/ssh/sshd_config`\
(Line 5 indicates the SSH port, which is changed to 2200)\
Restart with new setup:\
`sudo service ssh restart`

3) Setting up firewall:\
`sudo ufw status`\
`sudo ufw default deny incoming`\
`sudo ufw default allow outgoing`\
`sudo ufw allow 2200/tcp`\
`sudo ufw allow www`\
`sudo ufw allow 123/udp`\
`sudo ufw enable`\
`sudo ufw status`

In your Amazon Lightsail dashboard you can change the network settings:
- Allow ports 2200 (TCP), 80 (TCP), and 123 (UDP)\
- Delete the SSH (Port 22) entry\
- Reboot the system in the Lightsail dashboard.

4) Disable password login:\
`sudo nano /etc/ssh/sshd_config`\
Set PasswordAuthentication set to no by default, no change needed!

### User Management:
1) Create user ‘grader’:\
`sudo adduser grader`\
Give sudo access by modifying:\
`sudo nano /etc/sudoers.d/90-cloud-init-users`\
Add entry for grader:\
`# User rules for grader`\
`Grader ALL=(ALL) NOPASSWD:ALL`

2) Generate SSH key pair:\
`ssh-keygen -f ~/.ssh/udacity_grader_key.rsa`

- Copy the content from udacity_grader_key.rsa.pub on your local machine
- From the Lightsail terminal (ubuntu user) create an .ssh folder for grader:\
`sudo mkdir ./.ssh`
- And now create an authorized key file:\
`sudo touch /home/grader/.ssh/authorized_keys`\
`sudo nano  ./.ssh/authorized_keys`
- Now paste the content from the pub key to this newly created authorized_keys file.

Now you can access the machine as grader via:\
`ssh grader@35.158.194.250 -p 2200 -i ~/.ssh/udacity_grader_key.rsa`

3) Test sudo access of grader:\
`sudo nano /etc/sudoers.d/90-cloud-init-users`

### Web Application
1) Installing Apache and wsgi:
- As grader in the aws machine run:\
`sudo apt-get install apache2`
- Test 35.158.194.250 in your browser
-	Run the following commands:\
`sudo apt-get install libapache2-mod-wsgi-py3`\
`sudo a2enmod wsgi`\
`sudo service apache2 start`

2) Install git to clone sportscatalog web app:
- As grader in the aws machine run:\
`sudo apt-get install git`
- Clone project to aws machine:\
`sudo mkdir /var/www/catalog`\
`cd /var/www/catalog`\
`sudo git clone https://github.com/alexanderlieder1/sportscatalog-web-application.git catalog`\
`cd /var/www`\
`sudo chown -R grader:grader catalog/`\
`cd /var/www/catalog/catalog`\
`mv application.py __init__.py`\
`nano __init__.py`

Here I adapted the code to work with PostgreSQL:
- Modifying connection from sqlite to PostgreSQL
- Run:
`sudo nano /var/www/catalog/catalog.wsgi`
- Adding the following lines will enable to run the apache web server running the python application script (now **__init__.py**):\

`activate_this = "/var/www/catalog/catalog/venv3/bin/activate_this.py"`\

`with open(activate_this) as file_:`\
`exec(file_.read(), dict(__file__=activate_this))`

`#!/usr/bin/python`\
`import sys`\
`import logging`\
`logging.basicConfig(stream=sys.stderr)`\
`sys.path.insert(0, "/var/www/catalog/catalog/")`\
`sys.path.insert(1, "/var/www/catalog/")`

`from catalog import app as application`\
`application.secret_key = 'project2'`

3) Installing virtual environment\
As grader in the aws machine run\
`sudo apt-get install python3-pip`\
`sudo apt-get install python-pip`\
`sudo pip install virtualenv`\
`cd /var/www/catalog/catalog`\
`virtualenv -p python3 venv3`\
`sudo chown -R grader:grader venv3/`\
`. venv3/bin/activate`

4) Install necessary software:\
As grader in the aws machine run\
`pip install Flask`\
`pip install httplib2`\
`pip install requests`\
`pip install --upgrade oauth2client`\
`pip install sqlalchemy`\
`sudo apt-get install libpq-dev`\
`pip install psycopg2`\
`deactivate`

5) Configure new virtual host:\
As grader in the aws machine run\
`sudo nano /etc/apache2/mods-enabled/wsgi.conf`

Add a Python Path:\
`WSGIPythonPath /var/www/catalog/catalog/venv3/lib/python3.5/site-packages`

Run:\
`sudo nano /etc/apache2/sites-available/catalog.conf`

Paste the following code:\
`<VirtualHost *:80>`\
    `ServerName 35.158.194.250`\
  `ServerAlias ec2-35-158-194-250.eu-central-1.compute.amazonaws.com`\
    `WSGIScriptAlias / /var/www/catalog/catalog.wsgi`\
    `<Directory /var/www/catalog/catalog/>`\
    	`Order allow,deny`\
  	  `Allow from all`\
    `</Directory>`\
    `Alias /static /var/www/catalog/catalog/static`\
    `<Directory /var/www/catalog/catalog/static/>`\
  	  `Order allow,deny`\
  	  `Allow from all`\
    `</Directory>`\
    `ErrorLog ${APACHE_LOG_DIR}/error.log`\
    `LogLevel warn`\
    `CustomLog ${APACHE_LOG_DIR}/access.log combined`\
`</VirtualHost>`

Reload Apache via:\
`sudo a2ensite catalog`\
`sudo service apache2 reload`

6) Configuring PostgreSQL:
As grader in the aws machine run\
`sudo apt-get install libpq-dev python-dev`\
`sudo apt-get install postgresql postgresql-contrib`\
`sudo su - postgres`\
`psql`\
`CREATE USER catalog WITH PASSWORD 'catalog';`\
`ALTER USER catalog CREATEDB;`\
`CREATE DATABASE catalog WITH OWNER catalog;`\
`\c catalog`\
`REVOKE ALL ON SCHEMA public FROM public;`\
`GRANT ALL ON SCHEMA public TO catalog;`\
`\q`\
`exit`\
`. venv3/bin/activate`\
`python /var/www/catalog/catalog/sportscatalog_db_setup.py`\
`python /var/www/catalog/catalog/database_inital_entries.py`\
`sudo nano /etc/postgresql/9.5/main/pg_hba.conf`\
`deactivate`

Modify the config with the following code:\
`| local | all | postgres | peer |`\
`| local | all | all      | peer |`\
`| host  | all | all      | 127.0.0.1/32 | md5 |`\
`| host  | all | all      | ::1/128      | md5 |`

Restart Apache and access the app via your browser:\
`sudo service apache2 restart`

### Resources used
1) Udacity learning materials\
2) Big thanks to [kcalata](https://github.com/kcalata/Linux-Server-Configuration) for his detailed description\
3) [Apache wsgi Flask setup](https://www.bogotobogo.com/python/Flask/Python_Flask_HelloWorld_App_with_Apache_WSGI_Ubuntu14.php)
