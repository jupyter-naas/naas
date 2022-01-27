FROM jupyternaas/singleuser:2.11.19

# Build-time metadata as defined at http://label-schema.org
ARG BUILD_DATE
ARG VCS_REF
ENV NAAS_VERSION 2.2.0b0
ENV JUPYTER_ENABLE_LAB 'yes'
ENV NB_UMASK=022
ENV NB_USER=ftp
ENV NB_UID=21
ENV NB_GID=21
ENV NB_GROUP=21

USER root
LABEL org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name="Naas machine" \
    org.label-schema.description="jupyter machine with naas" \
    org.label-schema.url="https://naas.ai" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/jupyter-naas/naas" \
    org.label-schema.vendor="Cashstory, Inc." \
    org.label-schema.version=$NAAS_VERSION \
    org.label-schema.schema-version="1.0"

RUN mkdir /home/$NB_USER && \
    fix-permissions /home/$NB_USER \
    && cd $(dirname $(which jupyter-notebook)) \
    && rm jupyter-notebook \
    && ln -s jupyter-server jupyter-notebook

RUN python3 -m pip install --no-cache-dir --upgrade pip && python3 -m pip --version
RUN python3 -m pip install --no-cache-dir --upgrade --use-deprecated=legacy-resolver naas[full]==$NAAS_VERSION

RUN mkdir /etc/naas
COPY scripts /etc/naas/scripts
COPY custom /etc/naas/custom
RUN /etc/naas/scripts/install_supp
RUN /etc/naas/scripts/customize

COPY ./extensions /tmp/extensions
RUN cd /tmp/extensions/naasai \
    && jlpm build \
    && pip install -ve . \
    && mv naasai/labextension /opt/conda/share/jupyter/labextensions/naasai
RUN jupyter labextension develop --overwrite '/opt/conda/share/jupyter/labextensions/naasai' \
    && rm -rf /tmp/extensions/

RUN fix-permissions /opt/conda/share/jupyter/lab/extensions

ENV PATH="/home/ftp/.local/bin:${PATH}"