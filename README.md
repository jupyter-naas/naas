# Naas (Notebooks As Automated Services)

Schedule notebooks, to automate all your tasks.

Use the power of scripting in the cloud.
Whenever you need it (even when you sleep).

* Schedule your scripts
* Use Notebooks as API
* Share assets securely

## Install

`pip3 install naas`


# DEVELOPMENT

## Install

`pip3 install -r requirements.txt`

## Run test 

`pytest -x`  

## test local server

`./test_runner.sh`

open manager :

`localhost:5000/`

## deploy

`python3 setup.py sdist`

## publish

`python3 -m twine upload dist/* -u YOUR_USERNAME`