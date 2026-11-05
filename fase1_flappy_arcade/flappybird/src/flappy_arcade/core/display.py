"""Janela do sistema e escala da tela lógica.

O jogo sempre desenha numa superfície lógica de 575x860. A janela pode ter
qualquer tamanho: a imagem é ampliada mantendo a proporção, e o espaço que
sobra vira faixas laterais (letterbox), em vez de esticar e distorcer o jogo.
"""
import pygame

from ..config.constants import ALTURA, FATOR_TELA, LARGURA
from ..ui.theme import Palette

TAMANHO_MINIMO = (250, 350)
EVENTOS_DE_MOUSE = (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)


def calcular_viewport(tamanho_janela, tamanho_logico=(LARGURA, ALTURA)):
    """Retângulo (na janela) onde a tela lógica aparece, sem distorção."""
    jl, ja = tamanho_janela
    ll, la = tamanho_logico
    escala = min(jl / ll, ja / la)
    largura, altura = max(1, round(ll * escala)), max(1, round(la * escala))
    return pygame.Rect((jl - largura) // 2, (ja - altura) // 2, largura, altura)


class Window:
    def __init__(self, titulo):
        info = pygame.display.Info()
        escala = min(info.current_w * FATOR_TELA / LARGURA,
                     info.current_h * FATOR_TELA / ALTURA, 1.0)
        tamanho = (max(1, int(LARGURA * escala)), max(1, int(ALTURA * escala)))
        self.surface = pygame.display.set_mode(tamanho, pygame.RESIZABLE)
        pygame.display.set_caption(titulo)
        self._atualizar_viewport()

    def set_icon(self, sprite):
        pygame.display.set_icon(sprite)

    def resize(self, largura, altura):
        self.surface = pygame.display.set_mode(
            (max(TAMANHO_MINIMO[0], largura), max(TAMANHO_MINIMO[1], altura)),
            pygame.RESIZABLE)
        self._atualizar_viewport()

    def _atualizar_viewport(self):
        self.viewport = calcular_viewport(self.surface.get_size())

    def to_logical(self, pos):
        """Converte um ponto da janela para coordenadas lógicas (pode sair da área)."""
        vp = self.viewport
        return ((pos[0] - vp.x) * LARGURA / vp.w,
                (pos[1] - vp.y) * ALTURA / vp.h)

    def translate_event(self, evento):
        """Devolve o evento com a posição do mouse em coordenadas lógicas.

        Cliques nas faixas laterais (fora do jogo) viram None e são ignorados.
        """
        if evento.type not in EVENTOS_DE_MOUSE:
            return evento
        if evento.type != pygame.MOUSEMOTION and not self.viewport.collidepoint(evento.pos):
            return None
        x, y = self.to_logical(evento.pos)
        x = min(max(x, 0), LARGURA - 1)
        y = min(max(y, 0), ALTURA - 1)
        return pygame.event.Event(evento.type, {**evento.dict, 'pos': (x, y)})

    def present(self, tela_logica):
        vp = self.viewport
        if vp.size != self.surface.get_size():
            self.surface.fill(Palette.LETTERBOX)
        if vp.size == tela_logica.get_size():
            self.surface.blit(tela_logica, vp.topleft)
        else:
            self.surface.blit(pygame.transform.scale(tela_logica, vp.size), vp.topleft)
        pygame.display.flip()
