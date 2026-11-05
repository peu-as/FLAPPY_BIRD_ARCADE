"""Menu de pausa: Continuar, Configurações, Recomeçar (se houver) e Sair.

Abre por cima da partida, que fica congelada atrás (só a cena do topo é
atualizada). P ou ESC também continuam.
"""
import pygame

from ..config.constants import ALTURA, LARGURA
from ..ui.theme import Palette
from ..ui.widgets import Botao, GrupoBotoes
from .settings_scene import OverlayScene, SettingsScene, desenhar_cartao


class PauseScene(OverlayScene):
    def __init__(self, ctx, rotulo_sair, ao_sair, ao_recomecar=None):
        super().__init__(ctx)
        self.ao_sair, self.ao_recomecar = ao_sair, ao_recomecar
        opcoes = [('CONTINUAR', self._continuar, 'primario'),
                  ('CONFIGURAÇÕES', self._configurar, 'secundario')]
        if ao_recomecar:
            opcoes.append(('RECOMEÇAR', self._recomecar, 'secundario'))
        opcoes.append((rotulo_sair, self._sair, 'perigo'))
        altura = 90 + len(opcoes) * 72 + 16
        self.cartao = pygame.Rect(0, 0, 400, altura)
        self.cartao.center = (LARGURA // 2, ALTURA // 2)
        botoes = []
        for i, (rotulo, acao, estilo) in enumerate(opcoes):
            b = Botao((0, 0, 320, 58), rotulo, acao, estilo, tamanho_texto=30)
            b.rect.midtop = (LARGURA // 2, self.cartao.y + 88 + i * 72)
            botoes.append(b)
        self.grupo = GrupoBotoes(botoes)

    def _continuar(self):
        self.manager.pop()

    def _configurar(self):
        self.manager.push(SettingsScene(self.ctx))

    def _recomecar(self):
        self.manager.pop()
        self.ao_recomecar()

    def _sair(self):
        self.manager.pop()
        self.ao_sair()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
            self._continuar()
            return
        self.grupo.tratar_evento(event)

    def update(self, dt):
        self.grupo.atualizar(dt)

    def draw(self, surface):
        super().draw(surface)
        desenhar_cartao(surface, self.cartao, 'PAUSA', Palette.PIPE_MID)
        self.grupo.desenhar(surface)
