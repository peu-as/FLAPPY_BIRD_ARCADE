"""Pequenos elementos de HUD compartilhados pelas fases especiais."""
import pygame

from ..config.constants import ALTURA, VIDAS_POR_FASE_ESPECIAL


def texto_vidas_extras():
    """'+1 VIDA' ou '+2 VIDAS', conforme VIDAS_POR_FASE_ESPECIAL."""
    n = VIDAS_POR_FASE_ESPECIAL
    return f'+{n} VIDA' if n == 1 else f'+{n} VIDAS'

def desenhar_hud_bonus(tela, linhas):
    """Lista de bônus ativos no canto inferior esquerdo (acima do texto de status).
    linhas = [(texto, cor), ...]"""
    fonte = pygame.font.Font(None, 24)
    for i, (texto, cor) in enumerate(linhas):
        img = fonte.render(texto, True, cor)
        fundo = pygame.Surface((img.get_width() + 10, img.get_height() + 2), pygame.SRCALPHA)
        fundo.fill((0, 0, 0, 150))
        tela.blit(fundo, (6, ALTURA - 190 + i*24))
        tela.blit(img, (11, ALTURA - 189 + i*24))
