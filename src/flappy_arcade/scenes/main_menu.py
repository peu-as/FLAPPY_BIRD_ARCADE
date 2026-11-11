"""Menu principal: os modos, loja, equipamentos, configurações e sair.

O cenário é o do próprio jogo, em movimento (céu deslizando, chão rolando e
pássaros cruzando ao fundo). Os botões entram em cascata ao abrir o jogo.
Com os efeitos visuais desligados, tudo fica parado, sem perder função.

Atalho secreto: Ctrl + Shift + A liga/desliga o Modo Apresentação (tudo liberado,
sem tocar no save de verdade; veja systems/apresentacao.py).
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
from ..systems import apresentacao
from ..ui.theme import Palette
from ..ui.widgets import Botao, GrupoBotoes, desenhar_texto, ease_out_back, painel, texto
from .equipment_scene import EquipmentScene
from .game_scene import GameScene
from .map_scene import MapScene
from .settings_scene import SettingsScene
from .shop_scene import ShopScene

LARGURA_BOTAO, ALTURA_BOTAO, ESPACO = 430, 46, 8      # 8 modos em uma coluna
LARGURA_LINHA_DE_BAIXO = 500      # equipamentos, configurações e sair
Y_PRIMEIRO_BOTAO = 246
RECORTE_LOGO = (0, 0, 368, 96)     # só a palavra "FlappyBird" do logotipo
ENTRADA, ATRASO_ENTRADA = 0.5, 0.06
VELOCIDADE_CEU = 14                # px/s
PASSAROS_FUNDO = ('Fishy', 'Propellor', 'Bubble', 'Speed')     # sprites que cruzam o céu
TEMPO_AVISO = 3.0                  # s: aviso ao ligar/desligar o Modo Apresentação


def icone_estilingue(r):
    """Um estilingue de madeira com um pássaro no elástico."""
    icone = pygame.Surface((32, 32), pygame.SRCALPHA)
    madeira, escuro = (150, 92, 46), (84, 50, 26)
    pygame.draw.line(icone, madeira, (16, 31), (16, 18), 5)
    pygame.draw.line(icone, madeira, (16, 19), (8, 6), 4)
    pygame.draw.line(icone, madeira, (16, 19), (24, 6), 4)
    pygame.draw.line(icone, escuro, (8, 7), (24, 7), 2)
    passaro = ajustar_sprite(r.passaros['dia'][1], 18)
    icone.blit(passaro, passaro.get_rect(center=(16, 6)))
    return icone


def icone_combina3():
    """Três peças do Combina 3 (as cores dos bônus) em fila."""
    icone = pygame.Surface((32, 32), pygame.SRCALPHA)
    for i, cor in enumerate(((255, 222, 72), (110, 200, 255), (110, 220, 110))):
        pygame.draw.circle(icone, (52, 40, 56), (6 + i * 10, 16), 6)
        pygame.draw.circle(icone, cor, (6 + i * 10, 16), 4)
    return icone


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
            'donkey': ajustar_sprite(r.kong['parado'], 30),
            'galaga': ajustar_sprite(next(iter(r.inimigos.values())), 28),
            'flappy': ajustar_sprite(r.passaros['dia'][1], 30),
            'estilingue': icone_estilingue(r),
            'combina3': icone_combina3(),
            'livre': ajustar_sprite(r.passaros['tarde'][1], 30),
            'classico': ajustar_sprite(r.medalhas['ouro'], 26),
            'arcade': ajustar_sprite(r.chefe_galaga, 30),
        }
        self.sprites_fundo = [ajustar_sprite(r.especiais[nome], 40) for nome in PASSAROS_FUNDO]
        self.aviso = ('', 0.0)             # (texto, segundos restantes)
        self.grupo = GrupoBotoes(self._criar_botoes())

    # ------------------------------------------------------------ botões
    def _criar_botoes(self):
        progresso = self.ctx.progress
        botoes = []

        def modo(i, rotulo, acao, icone, detalhe='', estilo='primario', estrela=False):
            rect = pygame.Rect(0, 0, LARGURA_BOTAO, ALTURA_BOTAO)
            rect.midtop = (LARGURA // 2, Y_PRIMEIRO_BOTAO + i * (ALTURA_BOTAO + ESPACO))
            botoes.append(Botao(rect, rotulo, acao, estilo, detalhe, self.icones[icone],
                                tamanho_texto=28, mostrar_estrela=estrela))

        def estrelas(mapa):
            return f'{progresso.total(mapa)}/{progresso.maximo()}'

        for i, mapa in enumerate(ORDEM_MAPAS):          # Donkey, Galaga, Flappy, Estilingue
            modo(i, MAPAS[mapa].subtitulo.upper(), lambda m=mapa: self._abrir(MapScene(self.ctx, m)),
                 mapa, estrelas(mapa), estrela=True)
        n = len(ORDEM_MAPAS)
        if apresentacao.ligado():                        # o mapa já existe; o botão abre de vez na Fase 17
            modo(n, 'COMBINA 3', lambda: self._abrir(MapScene(self.ctx, 'combina3')), 'combina3',
                 estrelas('combina3'), estrela=True)
        else:
            modo(n, 'COMBINA 3', None, 'combina3', 'em breve')    # a próxima fase (match-3)
            botoes[-1].habilitado = False
        modo(n + 1, 'ARCADE (HISTÓRIA)', lambda: self._abrir(MapScene(self.ctx, 'arcade')), 'arcade',
             estrelas('arcade'), estilo='destaque', estrela=True)
        modo(n + 2, 'MODO LIVRE', lambda: self._abrir(GameScene(self.ctx, 'livre')), 'livre', 'treino')
        modo(n + 3, 'CLÁSSICO', lambda: self._abrir(GameScene(self.ctx, 'classico')), 'classico', 'original',
             estilo='secundario')
        y = Y_PRIMEIRO_BOTAO + (n + 4) * (ALTURA_BOTAO + ESPACO) + 6
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
        self._recriar_botoes()

    def _recriar_botoes(self):
        indice = self.grupo.indice
        self.grupo = GrupoBotoes(self._criar_botoes())     # estrelas e saldo atualizados
        self.grupo.indice = indice
        self.grupo.mover(0)
        if self.entrada > 0:
            self.entrada = ENTRADA + ATRASO_ENTRADA * len(self.grupo.botoes)   # só anima na 1ª vez

    def handle_event(self, event):
        if apresentacao.eh_atalho(event):
            self._alternar_apresentacao()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._sair()
            return
        self.grupo.tratar_evento(event)

    def _alternar_apresentacao(self):
        if apresentacao.alternar(self.ctx):
            self.aviso = ('MODO APRESENTAÇÃO: TUDO LIBERADO', TEMPO_AVISO)
            self.ctx.audio.play_sfx('ponto', 0.6)
        else:
            self.aviso = ('DE VOLTA AO SEU JOGO', TEMPO_AVISO)
            self.ctx.audio.play_sfx('pulo', 0.5)
        self._recriar_botoes()

    def update(self, dt):
        efeitos = self.ctx.settings.visual_fx_enabled
        self.tempo += dt
        texto_aviso, restante = self.aviso
        self.aviso = (texto_aviso, max(0.0, restante - dt))
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
        self._desenhar_apresentacao(surface)

    def _desenhar_apresentacao(self, surface):
        """Selo enquanto o Modo Apresentação está ligado e o aviso ao ligar/desligar."""
        if apresentacao.ligado():
            selo = texto('MODO APRESENTAÇÃO', 20, Palette.WHITE, Palette.INK, 2)
            caixa = selo.get_rect(midtop=(LARGURA // 2, 8)).inflate(20, 8)
            painel(surface, caixa, Palette.DANGER, Palette.INK, raio=12, sombra=0, brilho=False)
            surface.blit(selo, selo.get_rect(center=caixa.center))
        mensagem, restante = self.aviso
        if restante > 0:
            img = texto(mensagem, 30, Palette.BIRD_YELLOW, Palette.INK, 3).copy()
            img.set_alpha(round(255 * min(1.0, restante / 0.5)))
            fundo = img.get_rect(center=(LARGURA // 2, Y_CHAO + 30)).inflate(28, 14)
            painel(surface, fundo, Palette.INK, Palette.INK, raio=14, sombra=0, brilho=False)
            surface.blit(img, img.get_rect(center=fundo.center))

    def _desenhar_saldo(self, surface):
        rotulo = texto(str(self.ctx.wallet.saldo), 28, Palette.WHITE, Palette.INK, 2)
        caixa = pygame.Rect(14, 18, rotulo.get_width() + 56, 40)
        painel(surface, caixa, Palette.INK, Palette.INK, raio=20, sombra=0, brilho=False)
        icone = icone_moeda(13)
        surface.blit(icone, icone.get_rect(center=(caixa.x + 22, caixa.centery)))
        surface.blit(rotulo, rotulo.get_rect(midleft=(caixa.x + 40, caixa.centery)))
