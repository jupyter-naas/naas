FROM jupyternaas/naas:latest
ENV NB_USER=joyvan
run mkdir -p binder-demo
run git clone https://github.com/jupyter-naas/starters.git
run cp -r starters/* binder-demo/
run rm -rf starters
run mkdir -p .naas
