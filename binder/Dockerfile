FROM jupyternaas/singleuser:latest

ARG NB_USER
ARG NB_UID
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}
ENV NAAS_INSTALL_SUPP 'yes'
ENV JUPYTER_ENABLE_LAB 'yes'

WORKDIR ${HOME}

# # As of 2020-12-31, force binder to use jupyter-server instead of jupyter-notebook
# RUN cd $(dirname $(which jupyter-notebook)) \
#     && rm jupyter-notebook \
#     && ln -s jupyter-server jupyter-notebook

# Add the entire source tree
COPY . /home/$NB_USER/naas
RUN chown -R $NB_UID  .
RUN rmdir /home/$NB_USER/work

RUN cd /home/$NB_USER/naas && pip install --no-cache-dir -e '.[dev]'
RUN /home/$NB_USER/naas/scripts/install_supp

RUN mkdir /etc/naas
COPY custom/* /etc/naas/
COPY custom/overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
COPY custom/jupyter_server_config.py /home/$NB_USER/.jupyter/jupyter_notebook_config.py

# Custom naas design
RUN sed -i 's/JupyterLab/Naas/g' /opt/conda/share/jupyter/lab/static/index.html
COPY custom/naas_logo_n.ico /opt/conda/share/jupyterhub/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/jupyter_server/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/nbdime/webapp/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/jupyter_server/static/favicons/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/base/images/favicon.ico
RUN cat /etc/naas/custom.css >> /opt/conda/share/jupyter/lab/themes/@jupyterlab/theme-light-extension/index.css

