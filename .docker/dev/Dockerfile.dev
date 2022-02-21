FROM jupyternaas/singleuser:2.12.0

# Build-time metadata as defined at http://label-schema.org
ARG BUILD_DATE
ARG VCS_REF

ENV NAAS_INSTALL_SUPP 'no'
ENV JUPYTER_ENABLE_LAB 'yes'
ENV NB_USER=ftp

USER root
LABEL org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name="Naas machine" \
    org.label-schema.description="test jupyter machine with naas" \
    org.label-schema.url="https://naas.ai" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/jupyter-naas/naas" \
    org.label-schema.vendor="Cashstory, Inc." \
    org.label-schema.schema-version="1.0"

RUN mkdir /home/$NB_USER \
    && cd $(dirname $(which jupyter-notebook)) \
    && rm jupyter-notebook \
    && ln -s jupyter-server jupyter-notebook

COPY setup.cfg /home/$NB_USER/naas/setup.cfg
COPY setup.py /home/$NB_USER/naas/setup.py
COPY README.md /home/$NB_USER/naas/README.md
RUN cd /home/$NB_USER/naas && pip install --no-cache-dir -e '.[dev]'

COPY . /home/$NB_USER/naas
RUN fix-permissions /home/$NB_USER
ENV PYTHONPATH=/home/$NB_USER/naas:/home/$NB_USER/drivers

RUN mkdir /etc/naas
COPY scripts /etc/naas/scripts
COPY custom /etc/naas/custom
RUN /etc/naas/scripts/install_supp
RUN /etc/naas/scripts/customize

RUN wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip\
    && unzip ngrok-stable-linux-amd64.zip \
    && mkdir -p /opt/conda/lib/python3.8/site-packages/pyngrok/bin/ \
    && mv ngrok /opt/conda/lib/python3.8/site-packages/pyngrok/bin/ \
    && rm ngrok-stable-linux-amd64.zip

ENV PATH="/home/ftp/.local/bin:${PATH}"

ADD .docker/dev/docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]