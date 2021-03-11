FROM jupyternaas/singleuser:latest

# ARG NB_USER
# ARG NB_UID

# ENV USER ${NB_USER}
# ENV HOME /home/${NB_USER}

# RUN adduser --disabled-password \
#     --gecos "Default user" \
#     --uid ${NB_UID} \
#     ${NB_USER}
# WORKDIR ${HOME}

COPY naas /home/$NB_USER/naas
COPY setup.cfg /home/$NB_USER/naas/setup.cfg
COPY setup.py /home/$NB_USER/naas/setup.py
COPY scripts /home/$NB_USER/naas/scripts
COPY README.md /home/$NB_USER/naas/README.md
RUN cd /home/$NB_USER/naas && pip install --use-deprecated=legacy-resolver -e '.[dev]'

RUN mkdir /etc/naas
COPY custom/* /etc/naas/
COPY custom/overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
COPY custom/jupyter_server_config.py /etc/jupyter/jupyter_server_config.py

RUN sed -i 's/JupyterLab/Naas/g' /opt/conda/share/jupyter/lab/static/index.html
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/jupyter_server/static/favicons/favicon.ico

RUN cat /etc/naas/custom.css >> /opt/conda/share/jupyter/lab/themes/@jupyterlab/theme-light-extension/index.css
