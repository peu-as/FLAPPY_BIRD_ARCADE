"""Configurações: música, efeitos sonoros, efeitos visuais e resetar progresso.

Abre por cima da tela atual (menu principal ou pausa), escurecendo-a.
Resetar pede confirmação, com o foco inicial em CANCELAR.
"""
import pygame

from ..config.constants import ALTURA, LARGURA
from ..core.scene import Scene
from ..systems.settings_store import EFEITOS_VISUAIS, MUSICA, SFX
from ..ui.theme import Palette
from ..ui.widgets import Botao, GrupoBotoes, LinhaInterruptor, desenhar_texto, painel

CARTAO = pygame.Rect(0, 0, 500, 560)
CARTAO.center = (LARGURA // 2, ALTURA // 2)
TEMPO_AVISO = 2.2


def desenhar_cartao(surface, rect, titulo, cor_titulo=Palette.BIRD_YELLOW):
    """Cartão creme com faixa de título, usado pelas telas sobrepostas."""
    painel(surface, rect, Palette.PANEL)
    faixa = pygame.Rect(rect.x, rect.y, rect.w, 66)
    painel(surface, faixa, cor_titulo, sombra=0)
    desenhar_texto(surface, titulo, 40, faixa.center, espessura=3)


class OverlayScene(Scene):
    """Base das telas que aparecem por cima de outra, escurecendo-a."""
    fps = 60
    is_overlay = True

    def __init__(self, ctx):
        super().__init__(ctx)
        self.escurecer = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self.escurecer.fill(Palette.DIM)

    def draw(self, surface):
        surface.blit(self.escurecer, (0, 0))


class SettingsScene(OverlayScene):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.confirmando = False
        self.aviso = 0.0
        self._montar()

    def _montar(self):
        s = self.ctx.settings
        x, largura = CARTAO.x + 16, CARTAO.w - 32
        linhas = [
            LinhaInterruptor((x, CARTAO.y + 86, largura, 70), 'Música', lambda: s.music_enabled,
                             lambda: s.toggle(MUSICA)),
            LinhaInterruptor((x, CARTAO.y + 162, largura, 70), 'Efeitos sonoros', lambda: s.sfx_enabled,
                             lambda: s.toggle(SFX)),
            LinhaInterruptor((x, CARTAO.y + 238, largura, 76), 'Efeitos visuais', lambda: s.visual_fx_enabled,
                             lambda: s.toggle(EFEITOS_VISUAIS), 'partículas, rastros e animações extras'),
        ]
        resetar = Botao((0, 0, 330, 54), 'RESETAR PROGRESSO', self._pedir_reset, 'perigo', tamanho_texto=28)
        resetar.rect.midtop = (CARTAO.centerx, CARTAO.y + 350)
        voltar = Botao((0, 0, 330, 58), 'VOLTAR', self._voltar, 'primario', tamanho_texto=32)
        voltar.rect.midbottom = (CARTAO.centerx, CARTAO.bottom - 28)
        self.grupo = GrupoBotoes(linhas + [resetar, voltar])
        cancelar = Botao((0, 0, 200, 58), 'CANCELAR', self._cancelar, 'secundario', tamanho_texto=30)
        apagar = Botao((0, 0, 200, 58), 'APAGAR', self._apagar, 'perigo', tamanho_texto=30)
        cancelar.rect.bottomright = (CARTAO.centerx - 8, CARTAO.bottom - 28)
        apagar.rect.bottomleft = (CARTAO.centerx + 8, CARTAO.bottom - 28)
        self.grupo_confirmar = GrupoBotoes([cancelar, apagar], colunas=2)

    # ------------------------------------------------------------ ações
    def _voltar(self):
        self.ctx.audio.play_sfx('pulo', 0.3)
        self.manager.pop()

    def _pedir_reset(self):
        self.confirmando = True
        self.grupo_confirmar.focar(self.grupo_confirmar.botoes[0])     # foco em CANCELAR

    def _cancelar(self):
        self.confirmando = False

    def _apagar(self):
        self.ctx.save.reset_progress()
        self.ctx.bus.emit('progress_reset')
        self.ctx.audio.play_sfx('colisao', 0.4)
        self.confirmando = False
        self.aviso = TEMPO_AVISO

    # ------------------------------------------------------------ cena
    def handle_event(self, event):
        grupo = self.grupo_confirmar if self.confirmando else self.grupo
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cancelar() if self.confirmando else self._voltar()
            return
        grupo.tratar_evento(event)

    def update(self, dt):
        self.aviso = max(0.0, self.aviso - dt)
        (self.grupo_confirmar if self.confirmando else self.grupo).atualizar(dt)

    def draw(self, surface):
        super().draw(surface)
        if self.confirmando:
            desenhar_cartao(surface, CARTAO, 'APAGAR TUDO?', Palette.DANGER)
            linhas = ['Isto apaga suas moedas, as skins e',
                      'os cenários comprados, as estrelas',
                      'dos mapas e o recorde do Modo Livre.',
                      '',
                      'As configurações e o ranking do',
                      'jogo clássico continuam.',
                      '',
                      'Não dá para desfazer.']
            for i, linha in enumerate(linhas):
                cor = Palette.DANGER if i == len(linhas) - 1 else Palette.INK
                desenhar_texto(surface, linha, 28, (CARTAO.centerx, CARTAO.y + 116 + i * 34), cor,
                               contorno=None)
            self.grupo_confirmar.desenhar(surface)
            return
        desenhar_cartao(surface, CARTAO, 'CONFIGURAÇÕES')
        self.grupo.desenhar(surface)
        if self.aviso:
            desenhar_texto(surface, 'Progresso apagado', 26, (CARTAO.centerx, CARTAO.y + 432),
                           Palette.DANGER, contorno=None)
