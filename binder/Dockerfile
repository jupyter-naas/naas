FROM jupyternaas/singleuser:latest

ENV JUPYTER_ENABLE_LAB 'yes'

# ENV HOME /home/${NB_USER}

# ARG NB_USER=jovyan
# ARG NB_UID=1000
# ENV USER ${NB_USER}
# ENV NB_UID ${NB_UID}


# USER $NB_USER

ENV NB_UMASK=022
ENV NB_USER=ftp
ENV NB_UID=21
ENV NB_GID=21
ENV NB_GROUP=21

# RUN adduser --disabled-password \
#     --gecos "Default user" \
#     --uid ${NB_UID} \
#     ${NB_USER}

RUN mkdir /home/$NB_USER && \
    fix-permissions /home/$NB_USER

COPY naas /home/$NB_USER/naas
COPY setup.cfg /home/$NB_USER/naas/setup.cfg
COPY setup.py /home/$NB_USER/naas/setup.py
COPY scripts /home/$NB_USER/naas/scripts
COPY README.md /home/$NB_USER/naas/README.md
RUN /home/$NB_USER/naas/scripts/install_supp
RUN cd /home/$NB_USER/naas && pip install -e '.[dev]'

RUN mkdir /etc/naas
COPY custom/* /etc/naas/
COPY custom/overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
COPY custom/jupyter_server_config.py /etc/jupyter/jupyter_notebook_config.py

# Custom naas design
RUN sed -i 's/JupyterLab/Naas/g' /opt/conda/share/jupyter/lab/static/index.html
COPY custom/naas_logo_n.ico /opt/conda/share/jupyterhub/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/jupyter_server/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/nbdime/webapp/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/jupyter_server/static/favicons/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/base/images/favicon.ico
RUN cat /etc/naas/custom.css >> /opt/conda/share/jupyter/lab/themes/@jupyterlab/theme-light-extension/index.css

