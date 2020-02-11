# Dockerfile for binder
FROM sagemath/sagemath:9.0-py3
USER root
ENV HOME /root
RUN apt-get update && apt-get -qq install -y curl tar \
    && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - \
    && apt-get install -yq nodejs && npm install npm@latest -g
USER sage
ENV HOME /home/sage
RUN sage -pip install --upgrade jupyterlab ipywidgets sage_combinat_widgets
COPY --chown=sage:sage . ${HOME}/sage-explorer
WORKDIR ${HOME}/sage-explorer
RUN sage -pip install .
