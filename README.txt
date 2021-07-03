PREREQUISITES:

PIP3    - Usually installed with python on most machines. If not it has to be installed for the project to work.

MongoDB - Can be downloaded from https://www.mongodb.com/try/download/community
	  To be installed with all the default parameters

Instructions:

1) Download the .zip file and extract it into an empty folder.

2) Open cmd (windows) or terminal (linux) and navigate inside the created folder.

3) Sudo pip3 install virtualenv (Linux) pip3 install virtualenv (windows)

4) Create a virtual environment for the project: virtualenv - p python3 env

4) Activate the virtual environment by using:
	source env/bin/activate (Linux)
	env\Scripts\activate (Windows)

5) pip3 install -r requirements.txt

6) set FLASK_APP = app.py
   set FLASK_ENV = development
   flask run


NOTE: TO TURN ON THE TERMINAL DEMO SCROLL DOWN TO THE BOTTOM OF THE app.py FILE AND REMOVE THE COMMENT FROM demo()