# Dockerfile for binder
FROM sagemath/sagemath:9.1.rc5
USER root
ENV HOME /root
RUN apt-get update && apt-get -qq install -y curl tar \
    && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - \
    && apt-get install -yq nodejs && npm install npm@latest -g
USER sage
ENV HOME /home/sage
RUN sage -pip install jupyterlab==1.2.11
RUN sage -pip install --upgrade ipywidgets sage_combinat_widgets pyyaml ipyevents
RUN sage -jupyter labextension install --no-build @jupyter-widgets/jupyterlab-manager \
 && sage -jupyter lab build \
 && sage -jupyter lab clean
COPY --chown=sage:sage . ${HOME}/sage-explorer
WORKDIR ${HOME}/sage-explorer
RUN sage -pip install .
