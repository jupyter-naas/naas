![GitHub license](https://img.shields.io/github/license/jupyter-naas/drivers)
![Bump version](https://github.com/jupyter-naas/naas/workflows/Bump%20version/badge.svg)
![Upload Python Package](https://github.com/jupyter-naas/naas/workflows/Upload%20Python%20Package/badge.svg)
![codecov](https://codecov.io/gh/jupyter-naas/naas/branch/main/graph/badge.svg?token=UC3SAL8S0U)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=jupyter-naas_naas&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=jupyter-naas_naas)
<a href="#badge">
  <img alt="semantic-release" src="https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg">
</a>
<a href="http://commitizen.github.io/cz-cli/"><img alt="Commitizen friendly" src="https://img.shields.io/badge/commitizen-friendly-brightgreen.svg"></a>
![PyPI](https://img.shields.io/pypi/v/naas)

# Naas: Notebooks-as-a-service

Schedule notebooks, to automate all your tasks.

Use the power of scripting in the cloud.
Whenever you need it (even when you sleep).

* Schedule your scripts
* Use Notebooks as API
* Share assets securely
* Send emails

# Documentation 

<p>
  <a href="https://naas.gitbook.io/naas/" title="Redirect to Documentation">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/gitbook.svg" alt="Gitbooks naas" />
  </a>
 </p>

# Issue

If you found a bug or need a new feature go there :
https://naas.canny.io/

## Try Naas
Using Binder
You can try out some of Naas features using the My Binder service.

Click on a link below to try Naas, on a sandbox environment, without having to install anything.
Test it in binder (WIP)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jupyter-naas/naas/main?urlpath=lab)

## Install

`pip3 install naas`

### Install with drivers

`pip3 install 'naas[full]'`

---

# DEVELOPMENT

## Install

it will create and install all dependency in docker machine

`./install`

## Test local server

`./install -ro`
it will run your docker machine only.

if you want to rebuild docker too `./install -r`


Then open your browser at the url:
`http://localhost:8888`

enter `naas` as password

if you want other password `./install.sh -t=mypassword`

### Api documentation

We have a WIP documentation in swagger.

`http://127.0.0.1:5000/swagger/`

### Livereload 

If you do change in naas code, the server will live reload.

If you use naas in a notebook restart the kernel to get the changes.

### isolated Manager
open manager outsite of jupyter context :

`http://localhost:5000/naas`

## Run test 

Open Jupyterlab
click on `+` to open Launcher
Open Shell
Go the right directory `cd naas`
Run it in the shell `pytest -x`  to test your code

Each Change you do from your IDE or from jupyter in the Naas folder is live reloaded
If you test naas feature inside a notebook reload your kernel between changes.
Same for the manager page you have to reload the Page to see the changes.
To go faster you can use `isolated Manager` to reload only manager and not full jupyterlab

## Check lint

`python -m black naas` format better
`python -m flake8 naas` check if any left error

## Publish

You can commit from jupyter or from your local IDE, code of Naas is sync between docker machine and your computer

this auto publish by github action on main branch

# Supporters: 
<p>
  <a href="http://sentry.com" title="Redirect to Sentry">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/sentry.svg" alt="Sentry" />
  </a>
  <a href="https://gitbook.com" title="Redirect to Gitbook">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/gitbook.svg" alt="Gitbooks" />
  </a>
  <a href="https://canny.io" title="Redirect to Canny">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/canny.svg" alt="Canny" />
  </a>
</p>

### Authors:
* [Martin donadieu](https://github.com/riderx)
