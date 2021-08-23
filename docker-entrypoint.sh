#!/usr/bin/env sh

[ ! -d "/home/ftp/drivers/.git" ] && (rm -rf /home/ftp/drivers/ || true) && git clone https://github.com/jupyter-naas/drivers.git "/home/ftp/drivers"
[ ! -d "/home/ftp/awesome-notebooks/.git" ] && git clone https://github.com/jupyter-naas/awesome-notebooks.git "/home/ftp/awesome-notebooks"

tini -g -- "start-notebook.sh"