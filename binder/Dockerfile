FROM jupyternaas/naas:latest
ARG NB_USER
ARG NB_UID
ENV NB_USER=$NB_USER
ENV NB_UID=$NB_UID
run mkdir -p binder-demo
run git clone https://github.com/jupyter-naas/starters.git
run cp -r starters/* binder-demo/
run rm -rf starters
run mkdir -p .naas
