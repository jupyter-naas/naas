#!/usr/bin/env sh

# Git clone naas drivers if it does not exists.
[ ! -d "/home/ftp/drivers/.git" ] && (rm -rf /home/ftp/drivers/ || true) && git clone https://github.com/jupyter-naas/drivers.git "/home/ftp/drivers"

# Git clone awesome-notebooks if it does not exists.
[ ! -d "/home/ftp/awesome-notebooks/.git" ] && git clone https://github.com/jupyter-naas/awesome-notebooks.git "/home/ftp/awesome-notebooks"

# Install naas dependencies.
pip install -e '/home/ftp/naas[dev]'

# Install naas drivers dependencies in background.
pip install -e '/home/ftp/drivers[dev]' &

cd '/home/ftp/naas/extensions/naasai' && jlpm install && jlpm run build

pip install -ve '/home/ftp/naas/extensions/naasai'

jupyter labextension develop --overwrite '/home/ftp/naas/extensions/naasai'

cd /home/ftp/

# Start jupyterlab.
tini -g -- "start-notebook.sh"  