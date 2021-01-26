FROM jupyternaas/singleuser:latest

# Build-time metadata as defined at http://label-schema.org
ARG BUILD_DATE
ARG VCS_REF
ENV VERSION 0.27.4


LABEL org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name="Naas machine" \
    org.label-schema.description="jupyter machine with naas" \
    org.label-schema.url="https://naas.ai" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/jupyter-naas/naas" \
    org.label-schema.vendor="Cashstory, Inc." \
    org.label-schema.version=$VERSION \
    org.label-schema.schema-version="1.0"


RUN git config --global credential.helper store #Auto save git credentials
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache naas_drivers naas==$VERSION
RUN cp /etc/jupyter/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/base/images/favicon.ico
