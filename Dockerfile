# Dockerfile for binder
FROM sagemath/sagemath:9.0-py3
RUN sage -pip install --upgrade ipywidgets jupyterlab sage_combinat_widgets
COPY --chown=sage:sage . ${HOME}/sage-explorer
WORKDIR ${HOME}/sage-explorer
RUN sage -pip install .
