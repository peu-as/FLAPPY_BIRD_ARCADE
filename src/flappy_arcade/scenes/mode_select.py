"""Tela de escolha de modo (provisória até o menu principal da Fase 6).

Mapas Donkey Kong, Galaga e Flappy, Modo Livre e o jogo clássico original.
O modo Arcade (história) chega na Fase 4.
"""
import math

import pygame

from ..config.constants import LARGURA, Y_CHAO
from ..config.levels import MAPAS, ORDEM_MAPAS
from ..core.scene import Scene
from ..gameplay.flappy import Chao
from ..gameplay.resources import ajustar_sprite
from ..ui.theme import Palette
from ..ui.widgets import Botao, GrupoBotoes, desenhar_texto, texto
from .game_scene import GameScene
from .map_scene import MapScene

LARGURA_BOTAO, ALTURA_BOTAO, ESPACO = 430, 60, 12
Y_PRIMEIRO_BOTAO = 262
RECORTE_LOGO = (0, 0, 368, 96)     # só a palavra "FlappyBird" do logotipo


class ModeSelectScene(Scene):
    fps = 60

    def __init__(self, ctx):
        super().__init__(ctx)
        r = ctx.resources
        self.fundo = r.fundos['bg']
        self.chao = Chao(r.chao)
        self.logo = r.logo.subsurface(RECORTE_LOGO).copy()
        self.tempo = 0.0
        self.icones = {
            'donkey': ajustar_sprite(r.kong['parado'], 38),
            'galaga': ajustar_sprite(next(iter(r.inimigos.values())), 36),
            'flappy': ajustar_sprite(r.passaros['dia'][1], 38),
            'livre': ajustar_sprite(r.passaros['tarde'][1], 38),
            'classico': ajustar_sprite(r.medalhas['ouro'], 34),
            'arcade': ajustar_sprite(r.chefe_galaga, 38),
        }
        self.grupo = GrupoBotoes(self._criar_botoes())

    def _criar_botoes(self):
        progresso = self.ctx.progress
        botoes = []

        def botao(i, rotulo, acao, icone, detalhe='', estilo='primario', habilitado=True, estrela_=False):
            rect = pygame.Rect(0, 0, LARGURA_BOTAO, ALTURA_BOTAO)
            rect.midtop = (LARGURA // 2, Y_PRIMEIRO_BOTAO + i * (ALTURA_BOTAO + ESPACO))
            botoes.append(Botao(rect, rotulo, acao, estilo, detalhe, self.icones[icone],
                                habilitado, tamanho_texto=32, mostrar_estrela=estrela_))

        for i, mapa in enumerate(ORDEM_MAPAS):
            total = f'{progresso.total(mapa)}/{progresso.maximo()}'
            botao(i, MAPAS[mapa].subtitulo.upper(), lambda m=mapa: self._abrir_mapa(m), mapa,
                  total, estrela_=True)
        botao(3, 'ARCADE (HISTÓRIA)', None, 'arcade', 'em breve', habilitado=False)
        botao(4, 'MODO LIVRE', lambda: self._jogar('livre'), 'livre', 'treino', estilo='destaque')
        botao(5, 'CLÁSSICO', lambda: self._jogar('classico'), 'classico', 'original', estilo='secundario')
        return botoes

    def _abrir_mapa(self, mapa):
        self.ctx.audio.play_sfx('ponto', 0.35)
        self.manager.push(MapScene(self.ctx, mapa))

    def _jogar(self, modo):
        self.ctx.audio.play_sfx('ponto', 0.35)
        self.manager.push(GameScene(self.ctx, modo))

    def on_enter(self):
        indice = self.grupo.indice if hasattr(self, 'grupo') else 0
        self.grupo = GrupoBotoes(self._criar_botoes())     # estrelas atualizadas
        self.grupo.indice = indice
        self.grupo.mover(0)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop()
            return
        self.grupo.tratar_evento(event)

    def update(self, dt):
        self.tempo += dt
        self.chao.atualizar(2)
        self.grupo.atualizar(dt)

    def draw(self, surface):
        surface.blit(self.fundo, (0, 0))
        oscila = math.sin(self.tempo * 2.2) * 6 if self.ctx.settings.visual_fx_enabled else 0
        surface.blit(self.logo, self.logo.get_rect(center=(LARGURA // 2, 92 + oscila)))
        desenhar_texto(surface, 'ARCADE', 64, (LARGURA // 2, 172), Palette.BIRD_YELLOW, espessura=3)
        quadro = self.ctx.resources.passaros['dia'][int(self.tempo * 9) % 3]
        surface.blit(quadro, quadro.get_rect(center=(LARGURA // 2 + 150, 170 - oscila)))
        desenhar_texto(surface, 'ESCOLHA O MODO', 26, (LARGURA // 2, 226), Palette.WHITE)
        self.grupo.desenhar(surface)
        self.chao.desenhar(surface)
        dica = texto('SETAS escolhem   ENTER joga   ESC sai', 22, Palette.INK, None)
        surface.blit(dica, dica.get_rect(center=(LARGURA // 2, Y_CHAO + 70)))
