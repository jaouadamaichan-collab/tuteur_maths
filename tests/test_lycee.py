"""Spécificités du lycée : fonctions dans la vérification des calculs, courbe de fonction, prompts."""

import math

import pytest

import exercices as E
import tuteur as T
from figures import FigureInvalide, dessiner, valider_figure


@pytest.mark.parametrize("expression, attendu", [
    ("exp(2)-ln(3)", math.exp(2) - math.log(3)),
    ("1000*1.03**12", 1000 * 1.03 ** 12),            # intérêts composés : exposant > 10
    ("cos(pi/3)", 0.5),
    ("log10(1000)", 3),
    ("abs(-2.5)+e", 2.5 + math.e),
    ("2*x**2-3", 15.0),                               # avec x = 3
])
def test_calculs_du_lycee(expression, attendu):
    assert math.isclose(E.evaluer_calcul(expression, {"x": 3}), attendu)


@pytest.mark.parametrize("expression, raison", [
    ("__import__('os')", "non autorisé"), ("x.real", "non autorisé"), ("y+1", "non autorisé"),
    ("ln(0)", "impossible"), ("2**1000", "trop grand"),
])
def test_calculs_refuses(expression, raison):
    with pytest.raises(E.ExerciceInvalide, match=raison):
        E.evaluer_calcul(expression, {"x": 1})


def test_reponse_numerique_verifiee_avec_exp():
    brut = {"format": "numerique", "notion": "fonction exponentielle", "mission": "Une population de bactéries.",
            "enonce": "Calcule N(2) = 500 × e^(0,3 × 2), arrondi à l'unité.", "calcul": "500*exp(0.3*2)", "reponse": 911,
            "arrondi": "unité", "unite": "bactéries", "figure": None, "indices": ["a", "b"], "correction": "N(2) ≈ 911."}
    assert E.valider_exercice(brut, "numerique")["reponse"] == 911
    with pytest.raises(E.ExerciceInvalide):
        E.valider_exercice({**brut, "reponse": 900}, "numerique")


def test_courbe_dessinee_avec_asymptote():
    fig = valider_figure({"type": "courbe", "expression": "1/(x-1)", "xmin": -3, "xmax": 4, "nom": "h"})
    assert fig == {"type": "courbe", "expression": "1/(x-1)", "xmin": -3.0, "xmax": 4.0, "nom": "h", "unite": ""}
    assert dessiner(fig)[:4] == b"\x89PNG"


def test_courbe_nom_nettoye():
    assert valider_figure({"type": "courbe", "expression": "x", "xmin": 0, "xmax": 1, "nom": "f<script>"})["nom"] == "fs"


@pytest.mark.parametrize("brut", [
    {"type": "courbe", "expression": "__import__('os').system('ls')", "xmin": 0, "xmax": 1},
    {"type": "courbe", "expression": "ln(x)", "xmin": -10, "xmax": 1},      # presque pas définie
    {"type": "courbe", "expression": "x", "xmin": 3, "xmax": 1},
    {"type": "courbe", "expression": "", "xmin": 0, "xmax": 1},
    {"type": "courbe", "expression": "x" * 200, "xmin": 0, "xmax": 1},
])
def test_courbe_refusee(brut):
    with pytest.raises(FigureInvalide):
        valider_figure(brut)


def test_prompts_du_lycee():
    assert "lycéens (Seconde à Terminale" in T.SOCLE and "ln" in T.SOCLE
    assert '"type": "courbe"' in T.FIGURES and "exp()" in T.SPECIFICATIONS["numerique"]
    assert "lycéen" in T.PROMPT_LECTURE and "sujet de bac" in T.consigne_mission({"interets": []}, 0)


def test_ton_sobre_de_lycee():
    """Retour des élèves : l'app collège était trop enfantine pour des lycéens."""
    import exercices as E
    import progression as P
    assert "pas d'emojis" in T.SOCLE and "bac" in T.NIVEAUX["difficile"]
    assert "Sport" not in " ".join(T.CENTRES_INTERET[:3]) and "Physique-chimie" in T.CENTRES_INTERET
    assert [b[1] for b in P.BADGES.values()] == ["Autonomie", "Régularité", "Polyvalence", "Rebond", "Séance complète"]
    assert E.NOMS_FORMATS["ordre"] == "Ordonner une démonstration" and E.FREQUENCE_OUVERT == 3
    source = open("ecran.py").read()
    assert "balloons" not in source and "Bravo" not in source
