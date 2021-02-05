FROM jupyternaas/singleuser:latest

ARG NB_USER
ARG NB_UID

RUN git config --global credential.helper store #Auto save git credentials
RUN cp /etc/jupyter/naas_logo_n.ico /opt/conda/lib/python3.8/site-packages/notebook/static/base/images/favicon.ico
RUN git clone https://github.com/jupyter-naas/starters.git /home/$NB_USER/starters
COPY naas /home/$NB_USER/naas
COPY setup.cfg /home/$NB_USER/naas/setup.cfg
COPY setup.py /home/$NB_USER/naas/setup.py
COPY scripts /home/$NB_USER/naas/scripts
COPY README.md /home/$NB_USER/naas/README.md
RUN cd /home/$NB_USER/naas && pip install -e '.[dev]' && pre-commit install
RUN (echo ""; echo "os.system('python -m naas.runner &')"; echo "") >> /etc/jupyter/jupyter_notebook_config.py
