#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2016
# --- Institut National de la Recherche Scientifique (INRS)
# ---
# --- Distributed under the GNU Lesser General Public License, Version 3.0.
# --- See accompanying file LICENSE.txt.
#************************************************************************

"""
Modèle de calcul des temps d'arrivée d'une surverse
à la palge de la Baie de Beauport
API statique
"""

__version__ = '1.0.rc2'

from bbclass import BBModel

s_bbModel = None

def init(dataDir):
    """
    La fonction init() doit être appelée avant toute utilisation de
    xeq(...). Elle configure le système.
    """
    s_bbModel = BBModel(dataDir)

def getDataDir():
    """
    La fonction getDataDir() retourne le répertoire des données
    """
    return s_bbModel.getDataDir()

def getInfo():
    """
    La fonction getInfo() retourne l'info sur les données.
    """
    return s_bbModel.getInfo()

def getPointNames():
    """
    La fonction getPointNames() retourne la liste des noms
    des points de surverse.
    """
    return s_bbModel.getPointNames()

def getPointTideNames(name):
    """
    La fonction getPointTideNames() retourne la liste des noms
    des cycles de marée pour le point de surverse de nom 'name'.
    """
    return s_bbModel.getPointTideNames()

def getTideSignal(t_start, t_end, dt):
    """
    La fonction getTideSignal() retourne le signal de marée
    entre t_start et t_end, avec un pas de temps de dt.
    La fonction retourne l'information comme liste de tuples
    (temps, niveau d'eau).
    Tous les temps sont UTC.
    """
    return s_bbModel.getTideSignal(t_start, t_end, dt)

def xeq(t_start, t_end, dt, pts, do_merge):
    """
    La fonction xeq(..) calule les temps d'arrivée pour une surverse. L'interval de surverse
    est donné par [t_start, t_end], le pas de calul est dt. Le calcul est effectué pour
    chacun des points de surverse. La liste pts ccomprend, pour chaque point de surverse,
    son nom et la liste des cycles de marée. Une liste de marée vide implique tous les cycles.
    Par exemple: [ [p1, [c1, c2, c5]], [p2, []] ...].
    La valeur booléenne do_merge contrôle si les différents temps de transit sont agglomérés ou
    gardés séparés.

    La fonction retourne l'information suivante:
    [
        (pnt_de_surverse, [ (t_min, t_max) arrival for each transit time in river] ),
        ...
    ]
    Tous les temps sont UTC.
    """
    return s_bbModel.xeq(t_start, t_end, dt, pts, do_merge)
