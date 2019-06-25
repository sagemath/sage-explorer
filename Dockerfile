# Dockerfile for binder
FROM sagemath/sagemath:8.6
COPY --chown=sage:sage . ${HOME}/new-sage-explorer
WORKDIR ${HOME}/new-sage-explorer
RUN sage -pip install sage_combinat_widgets
RUN sage -pip install .
