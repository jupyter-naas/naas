FROM jupyternaas/singleuser:latest

ARG NB_USER
ARG NB_UID
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}
WORKDIR ${HOME}

# Add project and demo dependencies
RUN apt update \
    && apt install -y -q wamerican procps \
    && pip install --no-cache jupyterlab-quickopen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# As of 2020-12-31, force binder to use jupyter-server instead of jupyter-notebook
RUN cd $(dirname $(which jupyter-notebook)) \
    && rm jupyter-notebook \
    && ln -s jupyter-server jupyter-notebook

# Add the entire source tree
ADD . .
RUN chown -R $NB_UID  .

RUN cd /home/$NB_USER/naas && pip install -e '.[dev]'

RUN mkdir /etc/naas
COPY custom/* /etc/naas/
COPY custom/overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
COPY custom/jupyter_server_config.py /etc/jupyter/jupyter_server_config.py

# Custom naas design
RUN sed -i 's/JupyterLab/Naas/g' /opt/conda/share/jupyter/lab/static/index.html
COPY custom/naas_logo_n.ico /opt/conda/share/jupyterhub/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/jupyter_server/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/nbdime/webapp/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/jupyter_server/static/favicons/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/base/images/favicon.ico
RUN cat /etc/naas/custom.css >> /opt/conda/share/jupyter/lab/themes/@jupyterlab/theme-light-extension/index.css

