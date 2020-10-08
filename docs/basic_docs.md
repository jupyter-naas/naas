<img width="25%" alt="Naas" src="https://raw.githubusercontent.com/jupyter-naas/naas/master/images/naas_logo.svg"/>

# Welcome to nass

## Table of Contents
1. [Why Nass exist](#Why-nass-xist)
2. [How to install](#How-to-install)
3. [Scheduler](#Sheduler)
4. [Notebook as API](#Notebook-as-API)
5. [Asset](#Asset)
6. [Dependency](#Dependency)
7. [Notification](#Notification)
7. [Secret](#Secret)




## Why nass exist
Notebooks are awesome, but use them in production is messy, so we created our own module to allow any jupyter server to becode a save production server !

## How to install
First :
`!pip install nass`

Check if you have the minimum env vars set:

- `JUPYTER_SERVER_ROOT` => Should be set as your home folder
- `JUPYTERHUB_USER` => Should be set as your machine user, not root
- `JUPYTERHUB_API_TOKEN` => should be auto set by your hub

Optionally:
- `NAAS_RUNNER_PORT` to change the port of the naas runner
- `PUBLIC_PROXY_API` if you want the api and assets features your should run the naas proxy machine and provide his hostname here
- `JUPYTERHUB_URL` the web url of your hub for api and assets features.
- `SINGLEUSER_PATH` if you deploy on kubernet and your singleusers have specific hostname end
- `NOTIFICATIONS_API` if you want the notification feature your should run the naas notification machine and provide his hostname here
- `NAAS_SENTRY_DSN` If you need to catch error made by your users, configure it.


Start the server in your jupyter singleuser machine:
`python -m naas.runner &`


Then in your notebook :
`import naas`




```python
import naas
```

---
## Scheduler
Copy in production this notebook and run it, every day at 9:00
`nass.scheduler.add(recurrence="0 9 * * *")`


```python
naas.scheduler.add(recurrence="0 9 * * *")
```

---
## Notebook as API
Copy in production this notebook and allow to run it by calling the returned url
`naas.api.add()`


```python
naas.api.add()
```


```python
naas.api.respond_notebook()
```

---
## Asset
Copy in production this asset ( file ) and allow to get it by calling the returned url
`naas.asset.add()`



```python
naas.assets.add()
```

---
## Dependency
Copy in production this notebook as dependency and allow other Api or Scheduler to use it.
`naas.dependency.add()`


```python
naas.dependency.add()
```

---
## Notification
Send and email to anyone withing your notebook runs.
`naas.notifications.send(email="elon@musk.com", subject="The tesla action is going up", "check in the link the new chart data maide with naas from fresh dataset : [LINK]")`



```python
naas.notifications.send(email="elon@musk.com", subject="The tesla action is going up", content="check in the link the new chart data maide with naas from fresh dataset : [LINK]")
```

---
## Secret
Copy in production your secret and allow other Api or Scheduler to use it. They are encoded in a secure manner.
`naas.secret.add(name="MY_FIRST_SECRET", secret="SUPER_SECRET_STRING")`


```python
naas.secret.add(name="MY_FIRST_SECRET", secret="SUPER_SECRET_STRING")
```
