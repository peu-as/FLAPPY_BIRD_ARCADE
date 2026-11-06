"""Menu principal: os modos, loja, equipamentos, configurações e sair.

O cenário é o do próprio jogo, em movimento (céu deslizando, chão rolando e
pássaros cruzando ao fundo). Os botões entram em cascata ao abrir o jogo.
Com os efeitos visuais desligados, tudo fica parado, sem perder função.
"""
import math
import random

import pygame

from ..config.constants import LARGURA, Y_CHAO
from ..config.levels import MAPAS, ORDEM_MAPAS
from ..core.paths import MUSICA_MENU
from ..core.scene import Scene
from ..gameplay.coins import icone_moeda
from ..gameplay.flappy import Chao
from ..gameplay.resources import ajustar_sprite
from ..ui.theme import Palette
from ..ui.widgets import Botao, GrupoBotoes, desenhar_texto, ease_out_back, painel, texto
from .equipment_scene import EquipmentScene
from .game_scene import GameScene
from .map_scene import MapScene
from .settings_scene import SettingsScene
from .shop_scene import ShopScene

LARGURA_BOTAO, ALTURA_BOTAO, ESPACO = 430, 54, 10
LARGURA_LINHA_DE_BAIXO = 500      # equipamentos, configurações e sair
Y_PRIMEIRO_BOTAO = 246
RECORTE_LOGO = (0, 0, 368, 96)     # só a palavra "FlappyBird" do logotipo
ENTRADA, ATRASO_ENTRADA = 0.5, 0.06
VELOCIDADE_CEU = 14                # px/s
PASSAROS_FUNDO = ('Fishy', 'Propellor', 'Bubble', 'Speed')     # sprites que cruzam o céu


class MainMenuScene(Scene):
    fps = 60

    def __init__(self, ctx):
        super().__init__(ctx)
        r = ctx.resources
        self.fundo = r.fundos['bg']
        self.chao = Chao(r.chao)
        self.logo = r.logo.subsurface(RECORTE_LOGO).copy()
        self.titulo = texto('ARCADE', 64, Palette.BIRD_YELLOW, Palette.INK, 3)
        self.tempo = 0.0
        self.ceu = 0.0
        self.entrada = 0.0                 # tempo desde que os botões começaram a entrar
        self.aleatorio = random.Random()
        self.voadores = []                 # pássaros de fundo: [x, y, velocidade, sprite]
        self.proximo_voador = 1.0
        self.icones = {
            'donkey': ajustar_sprite(r.kong['parado'], 34),
            'galaga': ajustar_sprite(next(iter(r.inimigos.values())), 32),
            'flappy': ajustar_sprite(r.passaros['dia'][1], 34),
            'livre': ajustar_sprite(r.passaros['tarde'][1], 34),
            'classico': ajustar_sprite(r.medalhas['ouro'], 30),
            'arcade': ajustar_sprite(r.chefe_galaga, 34),
        }
        self.sprites_fundo = [ajustar_sprite(r.especiais[nome], 40) for nome in PASSAROS_FUNDO]
        self.grupo = GrupoBotoes(self._criar_botoes())

    # ------------------------------------------------------------ botões
    def _criar_botoes(self):
        progresso = self.ctx.progress
        botoes = []

        def modo(i, rotulo, acao, icone, detalhe='', estilo='primario', estrela=False):
            rect = pygame.Rect(0, 0, LARGURA_BOTAO, ALTURA_BOTAO)
            rect.midtop = (LARGURA // 2, Y_PRIMEIRO_BOTAO + i * (ALTURA_BOTAO + ESPACO))
            botoes.append(Botao(rect, rotulo, acao, estilo, detalhe, self.icones[icone],
                                tamanho_texto=30, mostrar_estrela=estrela))

        def estrelas(mapa):
            return f'{progresso.total(mapa)}/{progresso.maximo()}'

        for i, mapa in enumerate(ORDEM_MAPAS):
            modo(i, MAPAS[mapa].subtitulo.upper(), lambda m=mapa: self._abrir(MapScene(self.ctx, m)),
                 mapa, estrelas(mapa), estrela=True)
        modo(3, 'ARCADE (HISTÓRIA)', lambda: self._abrir(MapScene(self.ctx, 'arcade')), 'arcade',
             estrelas('arcade'), estilo='destaque', estrela=True)
        modo(4, 'MODO LIVRE', lambda: self._abrir(GameScene(self.ctx, 'livre')), 'livre', 'treino')
        modo(5, 'CLÁSSICO', lambda: self._abrir(GameScene(self.ctx, 'classico')), 'classico', 'original',
             estilo='secundario')
        y = Y_PRIMEIRO_BOTAO + 6 * (ALTURA_BOTAO + ESPACO) + 6
        x = (LARGURA - LARGURA_LINHA_DE_BAIXO) // 2
        botoes.append(Botao((x, y, 190, 48), 'EQUIPAMENTOS',
                            lambda: self._abrir(EquipmentScene(self.ctx)), 'secundario', tamanho_texto=24))
        botoes.append(Botao((x + 200, y, 190, 48), 'CONFIGURAÇÕES',
                            lambda: self._abrir(SettingsScene(self.ctx)), 'secundario', tamanho_texto=24))
        botoes.append(Botao((x + 400, y, 100, 48), 'SAIR', self._sair, 'perigo', tamanho_texto=24))
        botoes.append(Botao((LARGURA - 136, 14, 122, 48), 'LOJA', lambda: self._abrir(ShopScene(self.ctx)),
                            'destaque', icone=icone_moeda(12), tamanho_texto=28))
        for b in botoes:
            b.base_x = b.rect.x
        return botoes

    def _abrir(self, cena):
        self.ctx.audio.play_sfx('ponto', 0.35)
        self.manager.push(cena)

    def _sair(self):
        self.manager.clear()

    # ------------------------------------------------------------ cena
    def on_enter(self):
        self.ctx.audio.play_music(MUSICA_MENU, volume=0.5)
        indice = self.grupo.indice
        self.grupo = GrupoBotoes(self._criar_botoes())     # estrelas e saldo atualizados
        self.grupo.indice = indice
        self.grupo.mover(0)
        if self.entrada > 0:
            self.entrada = ENTRADA + ATRASO_ENTRADA * len(self.grupo.botoes)   # só anima na 1ª vez

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._sair()
            return
        self.grupo.tratar_evento(event)

    def update(self, dt):
        efeitos = self.ctx.settings.visual_fx_enabled
        self.tempo += dt
        self.entrada += dt
        if efeitos:
            self.ceu = (self.ceu + VELOCIDADE_CEU * dt) % self.fundo.get_width()
            self.chao.atualizar(2)
            self._atualizar_voadores(dt)
        for i, b in enumerate(self.grupo.botoes):
            t = (self.entrada - i * ATRASO_ENTRADA) / ENTRADA
            deslize = (1 - ease_out_back(t)) * (LARGURA + 40) if efeitos else 0
            b.rect.x = b.base_x + round(deslize)
        self.grupo.atualizar(dt)

    def _atualizar_voadores(self, dt):
        self.proximo_voador -= dt
        if self.proximo_voador <= 0 and self.sprites_fundo:
            self.proximo_voador = self.aleatorio.uniform(2.5, 5.0)
            self.voadores.append([-50.0, self.aleatorio.uniform(120, 220), self.aleatorio.uniform(50, 90),
                                  self.aleatorio.choice(self.sprites_fundo)])
        for v in self.voadores:
            v[0] += v[2] * dt
        self.voadores = [v for v in self.voadores if v[0] < LARGURA + 60]

    def draw(self, surface):
        efeitos = self.ctx.settings.visual_fx_enabled
        largura = self.fundo.get_width()
        surface.blit(self.fundo, (-round(self.ceu), 0))
        surface.blit(self.fundo, (largura - round(self.ceu), 0))
        for x, y, _, sprite in self.voadores:
            onda = math.sin(self.tempo * 4 + x * 0.05) * 6
            surface.blit(sprite, sprite.get_rect(center=(x, y + onda)))
        oscila = math.sin(self.tempo * 2.2) * 6 if efeitos else 0
        surface.blit(self.logo, self.logo.get_rect(center=(LARGURA // 2, 92 + oscila)))
        pulso = 1 + 0.035 * math.sin(self.tempo * 3) if efeitos else 1
        titulo = pygame.transform.rotozoom(self.titulo, 0, pulso) if pulso != 1 else self.titulo
        surface.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 172)))
        quadro = self.ctx.resources.passaros['dia'][int(self.tempo * 9) % 3]
        surface.blit(quadro, quadro.get_rect(center=(LARGURA // 2 + 150, 170 - oscila)))
        desenhar_texto(surface, 'ESCOLHA O MODO', 24, (LARGURA // 2, 222), Palette.WHITE)
        self._desenhar_saldo(surface)
        self.grupo.desenhar(surface)
        self.chao.desenhar(surface)
        dica = texto('SETAS escolhem   ENTER confirma   ESC sai', 22, Palette.INK, None)
        surface.blit(dica, dica.get_rect(center=(LARGURA // 2, Y_CHAO + 70)))

    def _desenhar_saldo(self, surface):
        rotulo = texto(str(self.ctx.wallet.saldo), 28, Palette.WHITE, Palette.INK, 2)
        caixa = pygame.Rect(14, 18, rotulo.get_width() + 56, 40)
        painel(surface, caixa, Palette.INK, Palette.INK, raio=20, sombra=0, brilho=False)
        icone = icone_moeda(13)
        surface.blit(icone, icone.get_rect(center=(caixa.x + 22, caixa.centery)))
        surface.blit(rotulo, rotulo.get_rect(midleft=(caixa.x + 40, caixa.centery)))
