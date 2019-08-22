# Dockerfile for binder
FROM sagemath/sagemath:8.6
COPY --chown=sage:sage . ${HOME}/sage-explorer
WORKDIR ${HOME}/sage-explorer
RUN sage -pip install sage_combinat_widgets
RUN sage -pip install .
