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
    """Canos a passar numa casa comum do Flappy (9 na casa 1 ... 26 na casa 24).

    Cresce devagar porque a velocidade e a abertura já endurecem a casa; metas
    longas demais nas casas altas faziam um único erro custar a fase inteira.
    """
    return 8 + round(0.75 * casa)


# Chefão do Flappy: os pássaros sobem e descem mais que na fase dos pássaros
# comum (decisão da Fase 14: sem isso, os chefões 15 e 20 ficavam mais fáceis
# que as casas vizinhas).
OSCILACAO_CHEFE = 1.5
OSCILACAO_CHEFE_MAXIMA = 36      # px: acima disso o chefão final ficava impossível
CHEFE_ABERTURA_A_FRENTE = 3      # a passagem do chefão é a de 3 casas à frente
EXTRA_CHEFE = 8                  # pássaros a mais que a meta da casa...
EXTRA_CHEFE_POR_CAPITULO = 2     # ...e mais 2 a cada chefão (casa 5: +10 ... casa 25: +18)


def meta_chefe_flappy(casa):
    """Pássaros a passar na fase dos pássaros de uma casa de chefão.

    Os pássaros são alvos menores que os canos; com a mesma meta, o chefão
    ficava mais fácil que as casas vizinhas. Por isso pede mais, e um pouco
    mais a cada chefão.
    """
    return meta_flappy(casa) + EXTRA_CHEFE + EXTRA_CHEFE_POR_CAPITULO * (casa // INTERVALO_CHEFE)


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
    'arcade': Mapa('arcade', 'A GRANDE JORNADA', 'Arcade (história)', (200, 84, 200)),
    'estilingue': Mapa('estilingue', 'TORRES DO ESTILINGUE', 'Estilingue', (206, 96, 48)),
    # Combina 3: no menu desde a Fase 17 (ORDEM_MAPAS), fora da jornada Arcade
    'combina3': Mapa('combina3', 'TRILHA DO COMBINA 3', 'Combina 3', (232, 60, 120)),
}
ORDEM_MAPAS = ('donkey', 'galaga', 'flappy', 'estilingue', 'combina3')     # mapas de um estilo só


# ------------------------------------------------------------------ Arcade
# A jornada mistura os quatro estilos em 5 capítulos de 5 casas. Cada capítulo
# tem um cenário e termina num chefão. Para mudar a jornada, edite JORNADA.
NOMES_ESTILOS = {
    'flappy': 'Flappy',
    'passaros': 'Fase dos pássaros',
    'donkey': 'Donkey Kong',
    'galaga': 'Galaga',
}


@dataclass(frozen=True)
class Capitulo:
    titulo: str
    fundo: str               # 'dia', 'selva', 'tarde', 'noite' ou 'espaco'
    cor: tuple


@dataclass(frozen=True)
class Etapa:
    estilo: str              # chave de NOMES_ESTILOS
    chefe: bool
    capitulo: int            # 1 a 5


CAPITULOS = (
    Capitulo('CÉUS', 'dia', (80, 160, 40)),
    Capitulo('SELVA', 'selva', (214, 128, 44)),
    Capitulo('ENTARDECER', 'tarde', (232, 112, 60)),
    Capitulo('NOITE', 'noite', (96, 128, 236)),
    Capitulo('ESPAÇO', 'espaco', (200, 84, 200)),
)

# Uma linha por capítulo; '*' marca o chefão (sempre a 5ª casa do capítulo).
JORNADA = (
    ('flappy', 'flappy', 'donkey', 'flappy', 'donkey*'),
    ('galaga', 'flappy', 'donkey', 'passaros', 'galaga*'),
    ('donkey', 'galaga', 'flappy', 'donkey', 'passaros*'),
    ('galaga', 'passaros', 'donkey', 'galaga', 'donkey*'),
    ('flappy', 'donkey', 'galaga', 'passaros', 'galaga*'),
)


def etapa_arcade(casa):
    """Estilo, chefão e capítulo da casa N da jornada."""
    capitulo, posicao = divmod(casa - 1, INTERVALO_CHEFE)
    nome = JORNADA[capitulo][posicao]
    return Etapa(nome.rstrip('*'), nome.endswith('*'), capitulo + 1)


def cor_da_casa(mapa, casa):
    """Cor de destaque da casa: a do mapa, ou a do capítulo na jornada."""
    if mapa == 'arcade':
        return CAPITULOS[etapa_arcade(casa).capitulo - 1].cor
    return MAPAS[mapa].cor
