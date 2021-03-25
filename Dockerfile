FROM jupyternaas/singleuser:2.9.0

# Build-time metadata as defined at http://label-schema.org
ARG BUILD_DATE
ARG VCS_REF
ENV NAAS_VERSION 1.6.3
ENV JUPYTER_ENABLE_LAB 'yes'

ENV NB_UMASK=022
ENV NB_USER=ftp
ENV NB_UID=21
ENV NB_GID=21
ENV NB_GROUP=21

RUN mkdir /home/$NB_USER && \
    fix-permissions /home/$NB_USER

LABEL org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name="Naas machine" \
    org.label-schema.description="jupyter machine with naas" \
    org.label-schema.url="https://naas.ai" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/jupyter-naas/naas" \
    org.label-schema.vendor="Cashstory, Inc." \
    org.label-schema.version=$NAAS_VERSION \
    org.label-schema.schema-version="1.0"


# https://app.naas.ai/user-redirect/naas => redirect to naas

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache naas[full]==$NAAS_VERSION

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
RUN cat /etc/naas/custom.css >> /opt/conda/share/jupyter/lab/themes/@jupyterlab/theme-dark-extension/index.css
