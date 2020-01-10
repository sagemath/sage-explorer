# Dockerfile for binder
FROM sagemath/sagemath:9.0-py3
RUN sudo apt-get update && sudo apt-get -yq dist-upgrade \
 && sudo apt-get -yq install apt-utils git npm nodejs
COPY --chown=sage:sage . ${HOME}/sage-explorer
WORKDIR ${HOME}/sage-explorer
RUN sage -pip install jupyterlab
RUN sage -pip install sage-combinat-widgets
RUN sage -pip install .
