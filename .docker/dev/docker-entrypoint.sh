#!/usr/bin/env sh

# Git clone naas drivers if it does not exists.
[ ! -d "/home/ftp/drivers/.git" ] && (rm -rf /home/ftp/drivers/ || true) && git clone https://github.com/jupyter-naas/drivers.git "/home/ftp/drivers"

# Git clone awesome-notebooks if it does not exists.
[ ! -d "/home/ftp/awesome-notebooks/.git" ] && git clone https://github.com/jupyter-naas/awesome-notebooks.git "/home/ftp/awesome-notebooks"

# Install naas dependencies.
pip install -e '/home/ftp/naas[dev]'

# Install naas drivers dependencies in background.
pip install -e '/home/ftp/drivers[dev]' &

# Start jupyterlab.
tini -g -- "start-notebook.sh"  