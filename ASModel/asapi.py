#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2016
# --- Institut National de la Recherche Scientifique (INRS)
# ---
# --- Licensed under the Apache License, Version 2.0 (the "License");
# --- you may not use this file except in compliance with the License.
# --- You may obtain a copy of the License at
# ---
# ---     http://www.apache.org/licenses/LICENSE-2.0
# ---
# --- Unless required by applicable law or agreed to in writing, software
# --- distributed under the License is distributed on an "AS IS" BASIS,
# --- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# --- See the License for the specific language governing permissions and
# --- limitations under the License.
#************************************************************************

"""
Modèle de calcul des temps d'arrivée d'une surverse
API statique
"""

from .asclass import ASModel

s_asModel = None

def init(dataDir):
    """
    La fonction init() doit être appelée avant toute utilisation de
    xeq(...). Elle configure le système.
    """
    global s_asModel
    s_asModel = ASModel(dataDir)

def getDataDir():
    """
    La fonction getDataDir() retourne le répertoire des données
    """
    return s_asModel.getDataDir()

def getInfo():
    """
    La fonction getInfo() retourne l'info sur les données.
    """
    return s_asModel.getInfo()

def getPointNames():
    """
    La fonction getPointNames() retourne la liste des noms
    des points de surverse.
    """
    return s_asModel.getPointNames()

def getPointTideNames(name):
    """
    La fonction getPointTideNames() retourne la liste des noms
    des cycles de marée pour le point de surverse de nom 'name'.
    """
    return s_asModel.getPointTideNames(name)

def getTideSignal(t_start, t_end, dt):
    """
    La fonction getTideSignal() retourne le signal de marée
    entre t_start et t_end, avec un pas de temps de dt.
    La fonction retourne l'information comme liste de tuples
    (temps, niveau d'eau).
    Tous les temps sont UTC.
    """
    return s_asModel.getTideSignal(t_start, t_end, dt)

def getOverflowData(dt, overflows, do_merge):
    """
    La fonction xeq(..) calcule les temps d'arrivée pour une surverse. L'intervalle de surverse
    est donné par [t_start, t_end], le pas de calcul est dt. Le calcul est effectué pour
    chacun des points de surverse. La liste pts comprend, pour chaque point de surverse,
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
    return s_asModel.getOverflowData(dt, overflows, do_merge)

def getOverflowPlumes(dt, overflows):
    """
    Retourne las param des particle path.
    Tous les temps sont UTC.
    """
    return s_asModel.getOverflowPlumes(dt, overflows)
