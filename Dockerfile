# Dockerfile for binder
FROM registry.gitlab.com/sagemath/sage/sagemath:9.0.beta0-py3
RUN sudo apt-get update && sudo apt-get -yq dist-upgrade \
 && sudo apt-get -yq install apt-utils git npm nodejs
COPY --chown=sage:sage . ${HOME}/sage-explorer
WORKDIR ${HOME}/sage-explorer
RUN sage -pip install jupyterlab
RUN sage -pip install git+https://github.com/sagemath/sage-combinat-widgets.git
RUN sage -pip install .
