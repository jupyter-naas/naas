<img width="25%" alt="Naas" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/naas_logo.svg"/>

![Bump version](https://github.com/jupyter-naas/naas/workflows/Bump%20version/badge.svg)
![Upload Python Package](https://github.com/jupyter-naas/naas/workflows/Upload%20Python%20Package/badge.svg)
![codecov](https://codecov.io/gh/jupyter-naas/naas/branch/master/graph/badge.svg?token=UC3SAL8S0U)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=jupyter-naas_naas&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=jupyter-naas_naas)
<a href="#badge">
  <img alt="semantic-release" src="https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg">
</a>
 <a href="http://commitizen.github.io/cz-cli/"><img alt="Commitizen friendly" src="https://img.shields.io/badge/commitizen-friendly-brightgreen.svg"></a>
# Naas (Notebooks As Automated Services)

Schedule notebooks, to automate all your tasks.

Use the power of scripting in the cloud.
Whenever you need it (even when you sleep).

* Schedule your scripts
* Use Notebooks as API
* Share assets securely

## Try Naas
Using Binder
You can try out some of Naas features using the My Binder service.

Click on a link below to try Naas, on a sandbox environment, without having to install anything.
Test it in binder (WIP)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jupyter-naas/naas/main)

## Install

`pip3 install naas`

---

# DEVELOPMENT

## Install

`pip3 install -e '.[dev]'`

## Run test 

`pytest -x`  

## Test local server

`./test_runner.sh`

open manager :

`localhost:5000/`

## Publish

this auto publish by github action on main branch

## Check lint

`python3 -m black naas` format better
`python3 -m flake8 naas` check if any left error

# Supporters: 
<p>
  <a href="http://sentry.com" title="Redirect to Sentry">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/sentry.svg" alt="Sentry" />
  </a>
  <a href="https://gitbook.com" title="Redirect to Gitbook">
    <img width="200px" src="https://raw.githubusercontent.com/jupyter-naas/naas/main/images/gitbook.svg" alt="Gitbooks" />
  </a>
</p>

### Authors:
* [Martin donadieu](https://github.com/riderx)
