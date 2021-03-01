FROM jupyternaas/singleuser:latest

ARG NB_USER
ARG NB_UID

COPY naas /home/$NB_USER/naas
COPY setup.cfg /home/$NB_USER/naas/setup.cfg
COPY setup.py /home/$NB_USER/naas/setup.py
COPY scripts /home/$NB_USER/naas/scripts
COPY README.md /home/$NB_USER/naas/README.md
RUN cd /home/$NB_USER/naas && pip install --use-deprecated=legacy-resolver -e '.[dev]'

RUN mkdir /etc/naas
COPY custom/set_workspace.json /etc/naas/set_workspace.json
COPY custom/naas_logo.svg /etc/naas/naas_logo.svg
COPY custom/naas_logo_n.ico /etc/naas/naas_logo_n.ico
COPY custom/naas_fav.svg /etc/naas/naas_fav.svg
COPY custom/custom.css /etc/naas/custom.css
COPY custom/overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/base/images/favicon.ico
RUN cat /etc/naas/custom.css >> /opt/conda/share/jupyter/lab/themes/@jupyterlab/theme-light-extension/index.css
