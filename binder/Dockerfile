FROM jupyternaas/singleuser:latest

ARG NB_USER
ARG NB_UID
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}
ENV NAAS_INSTALL_SUPP 'yes'
ENV JUPYTER_ENABLE_LAB 'yes'
ENV NAAS_INSTALL_BINDER 'yes'

USER root
WORKDIR ${HOME}

# # As of 2020-12-31, force binder to use jupyter-server instead of jupyter-notebook
RUN cd $(dirname $(which jupyter-notebook)) \
    && rm jupyter-notebook \
    && ln -s jupyter-server jupyter-notebook

# Add the entire source tree
COPY . /home/$NB_USER/naas
RUN chown -R $NB_UID  .
RUN rmdir /home/$NB_USER/work

RUN cd /home/$NB_USER/naas && pip install --no-cache-dir -e '.[dev]'

RUN mkdir /etc/naas
COPY scripts /etc/naas/scripts
COPY custom /etc/naas/custom
RUN /etc/naas/scripts/install_supp
RUN /etc/naas/scripts/customize
