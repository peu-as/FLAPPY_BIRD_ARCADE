"""Loja de skins: vitrine com o pássaro animado + grade de cartões.

Comprar pede confirmação (segundo clique em até 3 s) e já equipa a skin.
Mouse: clique escolhe; roda rola a grade. Teclado: setas escolhem, ENTER
compra/equipa, ESC volta.
"""
import math
import random

import pygame

from ..config.constants import ALTURA, LARGURA
from ..config.skins import CORES_RARIDADE, NOMES_RARIDADE, SKINS
from ..core.paths import MUSICA_MENU
from ..core.scene import Scene
from ..gameplay.coins import icone_moeda
from ..gameplay.flappy import Passaro
from ..gameplay.skins import SkinVisual
from ..systems.shop import OK
from ..ui.theme import Palette
from ..ui.widgets import Botao, aproximar, clarear, desenhar_texto, painel, texto

ALTURA_TOPO = 78
VITRINE = pygame.Rect(0, ALTURA_TOPO, LARGURA, 262)
COLUNAS, CARTAO_L, CARTAO_A, ESPACO = 3, 172, 150, 12
X_GRADE = (LARGURA - (COLUNAS * CARTAO_L + (COLUNAS - 1) * ESPACO)) // 2
AREA_GRADE = pygame.Rect(0, VITRINE.bottom + 10, LARGURA, ALTURA - VITRINE.bottom - 10)
TEMPO_CONFIRMAR = 3.0
CENTRO_PREVIA = (150, VITRINE.centery + 6)


def retangulo_cartao(indice):
    linha, coluna = divmod(indice, COLUNAS)
    return pygame.Rect(X_GRADE + coluna * (CARTAO_L + ESPACO),
                       AREA_GRADE.y + 8 + linha * (CARTAO_A + ESPACO), CARTAO_L, CARTAO_A)


class ShopScene(Scene):
    fps = 60

    def __init__(self, ctx):
        super().__init__(ctx)
        r = ctx.resources
        self.loja = ctx.shop
        self.tempo = 0.0
        self.indice = next(i for i, s in enumerate(SKINS) if s.id == self.loja.equipada)
        self.rolagem = self.rolagem_alvo = 0.0
        self.miniaturas = {s.id: SkinVisual(s.id, r).sprite_para(0) for s in SKINS}
        self.visuais = {}
        self.passaro = Passaro(r)
        self.confirmando = None          # (skin_id, segundos restantes)
        self.confetes = []
        self.aleatorio = random.Random(7)
        self.voltar = Botao((14, 16, 56, 46), '<', self._sair, 'secundario', tamanho_texto=40)
        self.acao = Botao((318, VITRINE.y + 176, 230, 58), '', self._agir, tamanho_texto=30)
        self.hover = [0.0] * len(SKINS)
        self.mouse_em = None
        self._garantir_visivel()

    def on_enter(self):
        self.ctx.audio.play_music(MUSICA_MENU, volume=0.5)

    # ------------------------------------------------------------ estado
    @property
    def skin(self):
        return SKINS[self.indice]

    def visual(self, skin_id):
        if skin_id not in self.visuais:
            self.visuais[skin_id] = SkinVisual(skin_id, self.ctx.resources)
        visual = self.visuais[skin_id]
        visual.efeitos = self.ctx.settings.visual_fx_enabled
        return visual

    def _rolagem_maxima(self):
        ultimo = retangulo_cartao(len(SKINS) - 1)
        return max(0, ultimo.bottom + 16 - AREA_GRADE.bottom)

    def _garantir_visivel(self):
        rect = retangulo_cartao(self.indice).move(0, -self.rolagem_alvo)
        if rect.top < AREA_GRADE.top + 6:
            self.rolagem_alvo -= AREA_GRADE.top + 6 - rect.top
        elif rect.bottom > AREA_GRADE.bottom - 6:
            self.rolagem_alvo += rect.bottom - (AREA_GRADE.bottom - 6)
        self.rolagem_alvo = max(0, min(self._rolagem_maxima(), self.rolagem_alvo))

    def _selecionar(self, indice):
        if 0 <= indice < len(SKINS) and indice != self.indice:
            self.indice = indice
            self.confirmando = None
            self._garantir_visivel()

    def _sair(self):
        self.manager.pop()

    def _agir(self):
        skin = self.skin
        audio = self.ctx.audio
        if self.loja.possui(skin.id):
            if self.loja.equipada != skin.id:
                self.loja.equipar(skin.id)
                audio.play_sfx('ponto', 0.4)
            return
        if not self.ctx.wallet.pode_pagar(skin.preco):
            audio.play_sfx('colisao', 0.25)
            return
        if not self.confirmando or self.confirmando[0] != skin.id:
            self.confirmando = (skin.id, TEMPO_CONFIRMAR)
            audio.play_sfx('pulo', 0.4)
            return
        if self.loja.comprar(skin.id) == OK:
            self.loja.equipar(skin.id)
            self.confirmando = None
            audio.play_sfx('ponto', 0.6)
            self._comemorar()

    def _comemorar(self):
        if not self.ctx.settings.visual_fx_enabled:
            return
        cores = (Palette.COIN, Palette.LOGO_GREEN, Palette.WHITE, CORES_RARIDADE[self.skin.raridade])
        for _ in range(40):
            ang = self.aleatorio.uniform(0, 2 * math.pi)
            vel = self.aleatorio.uniform(120, 320)
            self.confetes.append([*CENTRO_PREVIA, vel * math.cos(ang), vel * math.sin(ang) - 120, 0.0,
                                  self.aleatorio.choice(cores)])

    def _texto_acao(self):
        """(rótulo, estilo, habilitado) do botão da vitrine."""
        skin = self.skin
        if self.loja.equipada == skin.id:
            return 'EQUIPADA', 'secundario', False
        if self.loja.possui(skin.id):
            return 'EQUIPAR', 'primario', True
        faltam = skin.preco - self.ctx.wallet.saldo
        if faltam > 0:
            return f'FALTAM {faltam}', 'primario', False
        if self.confirmando and self.confirmando[0] == skin.id:
            return 'CONFIRMAR?', 'perigo', True
        return f'COMPRAR {skin.preco}', 'destaque', True

    # ------------------------------------------------------------ entrada
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            tecla = event.key
            if tecla == pygame.K_ESCAPE:
                self._sair()
            elif tecla == pygame.K_LEFT:
                self._selecionar(self.indice - 1)
            elif tecla == pygame.K_RIGHT:
                self._selecionar(self.indice + 1)
            elif tecla == pygame.K_UP:
                self._selecionar(self.indice - COLUNAS)
            elif tecla == pygame.K_DOWN:
                self._selecionar(min(len(SKINS) - 1, self.indice + COLUNAS))
            elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._agir()
            return
        if event.type == pygame.MOUSEWHEEL:
            self.rolagem_alvo = max(0, min(self._rolagem_maxima(), self.rolagem_alvo - event.y * 80))
            return
        if event.type == pygame.MOUSEMOTION:
            self.voltar.foco = self.voltar.contem(event.pos)
            self.acao.foco = self.acao.contem(event.pos)
            self.mouse_em = self._cartao_em(event.pos)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for botao in (self.voltar, self.acao):
                if botao.contem(event.pos) and botao.habilitado:
                    botao.apertado = True
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for botao in (self.voltar, self.acao):
                if botao.apertado:
                    botao.apertado = False
                    if botao.contem(event.pos):
                        botao.ativar()
                        return
            indice = self._cartao_em(event.pos)
            if indice is not None:
                self._selecionar(indice)

    def _cartao_em(self, pos):
        if not AREA_GRADE.collidepoint(pos):
            return None
        for i in range(len(SKINS)):
            if retangulo_cartao(i).move(0, -self.rolagem).collidepoint(pos):
                return i
        return None

    # ------------------------------------------------------------ quadro
    def update(self, dt):
        self.tempo += dt
        self.rolagem = aproximar(self.rolagem, self.rolagem_alvo, dt, 220)
        if self.confirmando:
            restante = self.confirmando[1] - dt
            self.confirmando = (self.confirmando[0], restante) if restante > 0 else None
        rotulo, estilo, habilitado = self._texto_acao()
        self.acao.rotulo, self.acao.estilo, self.acao.habilitado = rotulo, estilo, habilitado
        self.voltar.atualizar(dt)
        self.acao.atualizar(dt)
        for i in range(len(SKINS)):
            alvo = 1.0 if i in (self.indice, self.mouse_em) else 0.0
            self.hover[i] = aproximar(self.hover[i], alvo, dt)
        self.passaro.contador += 1
        if self.passaro.contador >= 10:
            self.passaro.contador = 0
            self.passaro.indice = (self.passaro.indice + 1) % 3
        vivos = []
        for c in self.confetes:
            c[0] += c[2] * dt
            c[1] += c[3] * dt
            c[3] += 520 * dt
            c[4] += dt
            if c[4] < 1.4:
                vivos.append(c)
        self.confetes = vivos

    def draw(self, surface):
        surface.blit(self.ctx.resources.fundos['bg'], (0, -60))
        self._desenhar_vitrine(surface)
        self._desenhar_grade(surface)
        self._desenhar_topo(surface)

    def _desenhar_topo(self, surface):
        painel(surface, pygame.Rect(-6, -10, LARGURA + 12, ALTURA_TOPO + 10), Palette.PANEL, sombra=4)
        self.voltar.desenhar(surface)
        desenhar_texto(surface, 'LOJA', 40, (LARGURA // 2, 38), Palette.BIRD_YELLOW, espessura=3)
        saldo = texto(str(self.ctx.wallet.saldo), 30, Palette.WHITE, Palette.INK, 2)
        rect = saldo.get_rect(midright=(LARGURA - 16, 39))
        surface.blit(saldo, rect)
        icone = icone_moeda(14)
        surface.blit(icone, icone.get_rect(midright=(rect.x - 6, 39)))

    def _desenhar_vitrine(self, surface):
        skin = self.skin
        cor = CORES_RARIDADE[skin.raridade]
        pygame.draw.ellipse(surface, Palette.INK, (CENTRO_PREVIA[0] - 74, CENTRO_PREVIA[1] + 46, 148, 30))
        pygame.draw.ellipse(surface, clarear(cor, 0.25), (CENTRO_PREVIA[0] - 70, CENTRO_PREVIA[1] + 44, 140, 24))
        efeitos = self.ctx.settings.visual_fx_enabled
        sobe = math.sin(self.tempo * 3) * 8 if efeitos else 0
        p = self.passaro
        p.skin = self.visual(skin.id)
        largura, altura = p.sprite.get_size()
        p.x, p.y = CENTRO_PREVIA[0] - largura / 2, CENTRO_PREVIA[1] - altura / 2 + sobe
        p.vy = -math.sin(self.tempo * 3) * 2.5 if efeitos else 0
        p.desenhar(surface)
        for x, y, _, _, idade, cor_confete in self.confetes:
            pygame.draw.rect(surface, cor_confete, (x, y, 7, 7))
        x = 318
        desenhar_texto(surface, skin.nome.upper(), 36, topo_esquerdo=(x, VITRINE.y + 28), espessura=2)
        selo = texto(NOMES_RARIDADE[skin.raridade], 22, Palette.WHITE, None)
        caixa = pygame.Rect(x, VITRINE.y + 82, selo.get_width() + 24, 30)
        painel(surface, caixa, cor, raio=15, sombra=3, brilho=False)
        surface.blit(selo, selo.get_rect(center=caixa.center))
        if self.loja.possui(skin.id):
            estado = 'NA SUA COLEÇÃO'
            desenhar_texto(surface, estado, 24, topo_esquerdo=(x, VITRINE.y + 130), cor=Palette.WHITE)
        else:
            icone = icone_moeda(14)
            surface.blit(icone, (x, VITRINE.y + 128))
            desenhar_texto(surface, str(skin.preco), 34, topo_esquerdo=(x + 34, VITRINE.y + 124),
                           cor=Palette.COIN)
        self.acao.desenhar(surface)

    def _desenhar_grade(self, surface):
        fundo = pygame.Surface(AREA_GRADE.size, pygame.SRCALPHA)
        fundo.fill((*Palette.INK, 150))
        surface.blit(fundo, AREA_GRADE)
        surface.set_clip(AREA_GRADE)
        for i, skin in enumerate(SKINS):
            rect = retangulo_cartao(i).move(0, -round(self.rolagem))
            if rect.bottom < AREA_GRADE.top or rect.top > AREA_GRADE.bottom:
                continue
            self._desenhar_cartao(surface, i, skin, rect)
        surface.set_clip(None)

    def _desenhar_cartao(self, surface, i, skin, rect):
        escala = 1 + 0.05 * self.hover[i]
        rect = rect.inflate(rect.w * (escala - 1), rect.h * (escala - 1))
        cor = CORES_RARIDADE[skin.raridade]
        possui = self.loja.possui(skin.id)
        painel(surface, rect, Palette.PANEL_LIGHT if possui else Palette.PANEL, sombra=4)
        faixa = pygame.Rect(rect.x + 3, rect.y + 3, rect.w - 6, 24)
        pygame.draw.rect(surface, cor, faixa, border_top_left_radius=8, border_top_right_radius=8)
        rotulo = texto(NOMES_RARIDADE[skin.raridade], 18, Palette.WHITE, None)
        surface.blit(rotulo, rotulo.get_rect(center=faixa.center))
        mini = self.miniaturas[skin.id]
        surface.blit(mini, mini.get_rect(center=(rect.centerx, rect.y + 64)))
        nome = texto(skin.nome, 22, Palette.INK, None)
        surface.blit(nome, nome.get_rect(center=(rect.centerx, rect.y + 104)))
        if self.loja.equipada == skin.id:
            desenhar_texto(surface, 'EQUIPADA', 22, (rect.centerx, rect.bottom - 22), Palette.LOGO_GREEN)
        elif possui:
            desenhar_texto(surface, 'COMPRADA', 22, (rect.centerx, rect.bottom - 22), Palette.WHITE)
        else:
            preco = texto(str(skin.preco), 24, Palette.COIN, Palette.INK, 2)
            icone = icone_moeda(10)
            largura = icone.get_width() + 4 + preco.get_width()
            x = rect.centerx - largura // 2
            surface.blit(icone, icone.get_rect(midleft=(x, rect.bottom - 22)))
            surface.blit(preco, preco.get_rect(midleft=(x + icone.get_width() + 4, rect.bottom - 22)))
        if i == self.indice:
            pygame.draw.rect(surface, Palette.WHITE, rect.inflate(8, 8), 3, border_radius=12)
