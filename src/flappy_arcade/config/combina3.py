"""Modo Combina 3: medidas do tabuleiro e as 25 casas.

Fase 16: todas as casas pedem PONTOS em um número de jogadas (metas calibradas
com tools/playtest_combina3.py). A Fase 17 troca esta tabela por objetivos
variados (coletar peças, quebrar gelo e caixas, chefões).

Estrelas: a casa termina quando a meta é batida; quanto mais jogadas sobram,
mais estrelas (como as vidas nos outros mapas).
"""
import math
from dataclasses import dataclass

LINHAS, COLUNAS = 8, 7
CELULA = 70                           # px
TIPOS_DE_PECA = 6

JOGADAS = 20
PONTOS_POR_JOGADA_CASA_1 = 150        # um jogador que troca ao acaso faz ~170; um médio, ~340
PONTOS_POR_JOGADA_A_MAIS = 7          # por casa: a casa 25 pede ~320 por jogada
EXTRA_CHEFE = 1.15                    # casas 5, 10, 15, 20 e 25 pedem 15% a mais

FRACAO_3_ESTRELAS = 0.30              # sobrando 30% das jogadas (ou mais)
FRACAO_2_ESTRELAS = 0.12

MOEDAS_POR_ESPECIAL = 1               # cada peça especial criada
JOGADAS_POR_MOEDA = 2                 # na vitória: jogadas que sobraram / 2
MOEDAS_POR_VITORIA = 4


@dataclass(frozen=True)
class CasaCombina3:
    jogadas: int
    meta: int
    tipos: int = TIPOS_DE_PECA
    chefe: bool = False


def _casa(numero):
    chefe = numero % 5 == 0
    por_jogada = PONTOS_POR_JOGADA_CASA_1 + PONTOS_POR_JOGADA_A_MAIS * (numero - 1)
    meta = JOGADAS * por_jogada * (EXTRA_CHEFE if chefe else 1)
    return CasaCombina3(JOGADAS, int(round(meta / 100) * 100), chefe=chefe)


CASAS_COMBINA3 = tuple(_casa(n) for n in range(1, 26))


def casa_combina3(numero):
    return CASAS_COMBINA3[numero - 1]


def jogadas_para_estrelas(total):
    """(sobrando para 3 estrelas, sobrando para 2 estrelas)."""
    return math.ceil(total * FRACAO_3_ESTRELAS), math.ceil(total * FRACAO_2_ESTRELAS)


def estrelas_combina3(total, usadas):
    tres, duas = jogadas_para_estrelas(total)
    sobrando = total - usadas
    return 3 if sobrando >= tres else 2 if sobrando >= duas else 1
