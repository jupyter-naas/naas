FROM jupyternaas/singleuser:latest

# Build-time metadata as defined at http://label-schema.org
ARG BUILD_DATE
ARG VCS_REF
ENV VERSION 1.0.0


LABEL org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name="Naas machine" \
    org.label-schema.description="jupyter machine with naas" \
    org.label-schema.url="https://naas.ai" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/jupyter-naas/naas" \
    org.label-schema.vendor="Cashstory, Inc." \
    org.label-schema.version=$VERSION \
    org.label-schema.schema-version="1.0"


# https://app.naas.ai/user-redirect/naas => redirect to naas

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --use-deprecated=legacy-resolver --no-cache naas_drivers naas==$VERSION

RUN mkdir /etc/naas
COPY binder/jupyter_notebook_config.py /etc/naas/jupyter_notebook_config.py
COPY binder/jupyter_notebook_config.py /etc/jupyter/jupyter_notebook_config.py
COPY custom/set_workspace.json /etc/naas/set_workspace.json
COPY custom/naas_logo.svg /etc/naas/naas_logo.svg
COPY custom/naas_logo_n.ico /etc/naas/naas_logo_n.ico
COPY custom/naas_fav.svg /etc/naas/naas_fav.svg
COPY custom/custom.css /etc/naas/custom.css
COPY custom/overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
# https://github.com/jupyterlab/jupyterlab/issues/5502 for the custom sidebar order
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/favicon.ico
COPY custom/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/base/images/favicon.ico
RUN cat /etc/naas/custom.css >> /opt/conda/share/jupyter/lab/themes/@jupyterlab/theme-light-extension/index.css
