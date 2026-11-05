"""Mapas de 25 casas: identidade de cada mapa, objetivos e chefões.

Cada casa é um desafio fechado com VIDAS_POR_CASA vidas. A dificuldade da
casa N é o nível N da curva (config/difficulty_profiles.py).

Estrelas ao vencer: 3 sem perder vida, 2 perdendo uma, 1 perdendo duas.
A casa N + 1 é liberada quando a casa N tem pelo menos uma estrela.
"""
from dataclasses import dataclass

from .difficulty_profiles import NIVEIS

CASAS = NIVEIS
VIDAS_POR_CASA = 3
INTERVALO_CHEFE = 5          # chefão nas casas 5, 10, 15, 20 e 25


def tem_chefe(casa):
    return casa % INTERVALO_CHEFE == 0


def estrelas_por_danos(danos):
    """Estrelas de uma vitória, pelas vidas perdidas na tentativa."""
    return max(1, VIDAS_POR_CASA - danos)


def meta_flappy(casa):
    """Canos a passar numa casa comum do mapa Flappy (9 na casa 1 ... 33 na 24)."""
    return 8 + casa


@dataclass(frozen=True)
class Mapa:
    id: str
    titulo: str
    subtitulo: str
    cor: tuple               # cor de destaque do mapa (botões, caminho)


MAPAS = {
    'donkey': Mapa('donkey', 'SELVA DO KONG', 'Donkey Kong', (214, 128, 44)),
    'galaga': Mapa('galaga', 'ESQUADRILHA GALAGA', 'Galaga', (96, 128, 236)),
    'flappy': Mapa('flappy', 'CÉUS DO FLAPPY', 'Flappy clássico', (80, 160, 40)),
}
ORDEM_MAPAS = ('donkey', 'galaga', 'flappy')
