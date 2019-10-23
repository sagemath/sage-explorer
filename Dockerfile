# Dockerfile for binder
FROM registry.gitlab.com/sagemath/sage/sagemath:9.0.beta0-py3
COPY --chown=sage:sage . ${HOME}/sage-explorer
WORKDIR ${HOME}/sage-explorer
RUN sage -pip install jupyterlab
RUN sage -pip install sage_combinat_widgets
RUN sage -pip install .
