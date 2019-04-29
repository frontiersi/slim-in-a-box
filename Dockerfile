FROM opendatacube/jupyter

USER root

RUN pip3 install matplotlib click scikit-image pep8 ruamel.yaml

RUN pip3 install ipyleaflet

USER $NB_UID

WORKDIR /notebooks

CMD jupyter notebook --no-browser --ip="0.0.0.0" --NotebookApp.token=$JUPYTER_PASSWORD
