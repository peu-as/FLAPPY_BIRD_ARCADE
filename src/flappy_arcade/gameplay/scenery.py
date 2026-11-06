"""Cenários comprados: da faixa de horizonte (assets/cenarios) ao fundo de tela.

Os cenários são paisagens: a faixa fica apoiada no chão e o céu acima dela é
estendido com as cores do topo da própria faixa, como no fundo original do
Flappy (cidade embaixo, céu em cima). A montagem é feita uma vez por cenário.
"""
import pygame

from ..config.constants import ALTURA, LARGURA, Y_CHAO

ALTURA_EMENDA = 90          # px de transição entre o topo da faixa e o céu liso
ESCURECER_TOPO = 0.18       # o céu escurece um pouco em direção ao alto da tela


def _cor_media(superficie, rect):
    return tuple(int(c) for c in pygame.transform.average_color(superficie, rect)[:3])


def montar_retrato(faixa):
    """Faixa de horizonte (575 x ~400) -> fundo de tela inteira (575 x 860)."""
    tela = pygame.Surface((LARGURA, ALTURA))
    y_faixa = Y_CHAO - faixa.get_height()
    cor = _cor_media(faixa, pygame.Rect(0, 0, LARGURA, 6))
    alto = tuple(int(c * (1 - ESCURECER_TOPO)) for c in cor)
    for y in range(max(0, y_faixa)):
        t = y / max(1, y_faixa)
        tela.fill(tuple(round(a + (b - a) * t) for a, b in zip(alto, cor)), (0, y, LARGURA, 1))
    # emenda: as cores do topo da faixa (suavizadas) se dissolvem no céu liso
    linha = pygame.transform.smoothscale(faixa.subsurface((0, 0, LARGURA, 2)).copy(), (24, 1))
    linha = pygame.transform.smoothscale(linha, (LARGURA, 1))
    for y in range(ALTURA_EMENDA):
        copia = linha.copy()
        copia.set_alpha(round(255 * y / ALTURA_EMENDA))
        tela.blit(copia, (0, y_faixa - ALTURA_EMENDA + y))
    tela.blit(faixa, (0, y_faixa))
    tela.fill(_cor_media(faixa, pygame.Rect(0, faixa.get_height() - 4, LARGURA, 4)),
              (0, Y_CHAO, LARGURA, ALTURA - Y_CHAO))          # atrás do chão (fica escondido)
    return tela
