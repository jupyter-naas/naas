![Bump version](https://github.com/jupyter-naas/naas/workflows/Bump%20version/badge.svg)
![Upload Python Package](https://github.com/jupyter-naas/naas/workflows/Upload%20Python%20Package/badge.svg)
![Test Python package](https://github.com/jupyter-naas/naas/workflows/Test%20Python%20package/badge.svg)
![codecov](https://codecov.io/gh/jupyter-naas/naas/branch/master/graph/badge.svg?token=UC3SAL8S0U)

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

`pip3 install -e '.[dev]'`

## Run test 

`pytest -x`  

## Test local server

`./test_runner.sh`

open manager :

`localhost:5000/`

## Check lint

`python3 -m black naas` format better
`python3 -m flake8 naas` check if any left error

## Publish

Allow easy deploy by setting password in keyring
`python3 -m keyring set https://upload.pypi.org/legacy/ bobapp`

Then publish
`publish.sh`

# Supporters: 
![Sentry](./images/sentry.svg)
