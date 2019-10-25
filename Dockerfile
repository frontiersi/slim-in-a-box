FROM opendatacube/datacube-core

# Get dependencies for Jupyter
RUN pip3 install \
    jupyter matplotlib folium \
    && rm -rf $HOME/.cache/pip

# Copy some components of configuration of Jupyter from https://github.com/jupyter/docker-stacks/
# Configure environment
ENV NB_USER=jovyan \
    NB_UID=1000 \
    NB_GID=100
ENV HOME=/notebooks
ENV SHELL="bash"
RUN mkdir $HOME

ADD https://raw.githubusercontent.com/jupyter/docker-stacks/master/base-notebook/fix-permissions /usr/local/bin/fix-permissions
RUN chmod +x /usr/local/bin/fix-permissions 
# Create user with UID=1000 and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    chmod g+w /etc/passwd /etc/group && \
    fix-permissions $HOME

RUN pip3 install matplotlib click scikit-image pep8 ruamel.yaml ipyleaflet

# Adds CRS from WKT support to pyproj
RUN pip3 install 'pyproj==2.4.0' --force-reinstall
RUN pip3 install 'rasterio==1.1.0' --force-reinstall

USER $NB_UID

WORKDIR /notebooks

CMD jupyter notebook --no-browser --ip="0.0.0.0" --NotebookApp.token=$JUPYTER_PASSWORD
