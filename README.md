# ASur-2

Détermination de la fenêtre des temps d'arrivée d'une surverse

Installer:

- [git](https://git-scm.com/download/win)
- [tortoise-git](https://tortoisegit.org/download)
- [conda](https://repo.anaconda.com/miniconda) ou [Anaconda](https://repo.continuum.io)

Dans une fenêtre de commande **conda**:

- `conda update --all`
- `conda install cython numpy`
- `conda install wxpython matplotlib pytimeparse gdal pillow pyshp scipy`
- `conda install -c conda-forge mplcursors`

Cloner les logiciels via **tortoise-git** ou par la fenêtre de commande:

- `cd` *repertoire_de_travail*
- `git clone --recursive -v https:/github.com/secretyv/ASur.git`
- `git clone --recursive -v https:/gitlab.com/h2d2/H2D2-tools.git`

Dans une fenêtre de commande **conda**:

- `cd` *repertoire_de_travail*
- `set INRS_DEV=`*repertoire_de_travail*
- `cd Asur`
- `all.bat`
