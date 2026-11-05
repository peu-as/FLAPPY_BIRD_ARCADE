"""Componentes de interface no estilo do jogo (pixel art com contorno grosso).

    texto(...)            superfície de texto com contorno, em cache
    painel(...)           cartão creme com contorno e sombra sólida
    estrela(...)          estrela cheia ou vazia
    Botao, GrupoBotoes    botões com hover animado, clique e teclado

Todas as cores e medidas vêm de ui/theme.py.
"""
import math

import pygame

from .theme import Fonts, Metrics, Motion, Palette

_CACHE_TEXTO = {}
Fonts.ao_limpar(_CACHE_TEXTO.clear)     # textos prontos somem junto com as fontes


def texto(conteudo, tamanho, cor=Palette.WHITE, contorno=Palette.INK, espessura=2):
    """Texto com contorno (como os números do placar). Fica em cache."""
    chave = (conteudo, tamanho, cor, contorno, espessura)
    if chave not in _CACHE_TEXTO:
        fonte = Fonts.get(tamanho)
        miolo = fonte.render(conteudo, True, cor)
        if contorno is None or espessura <= 0:
            _CACHE_TEXTO[chave] = miolo
        else:
            borda = fonte.render(conteudo, True, contorno)
            e = espessura
            final = pygame.Surface((miolo.get_width() + 2 * e, miolo.get_height() + 2 * e), pygame.SRCALPHA)
            for dx in (-e, 0, e):
                for dy in (-e, 0, e):
                    if dx or dy:
                        final.blit(borda, (e + dx, e + dy))
            final.blit(miolo, (e, e))
            _CACHE_TEXTO[chave] = final
        if len(_CACHE_TEXTO) > 600:            # textos que mudam (cronômetros) não crescem sem fim
            _CACHE_TEXTO.pop(next(iter(_CACHE_TEXTO)))
    return _CACHE_TEXTO[chave]


def desenhar_texto(superficie, conteudo, tamanho, centro=None, cor=Palette.WHITE,
                   contorno=Palette.INK, espessura=2, topo_esquerdo=None):
    imagem = texto(conteudo, tamanho, cor, contorno, espessura)
    rect = imagem.get_rect(center=centro) if centro else imagem.get_rect(topleft=topo_esquerdo)
    superficie.blit(imagem, rect)
    return rect


def painel(superficie, rect, cor=Palette.PANEL, borda=Palette.INK, raio=Metrics.RADIUS,
           sombra=Metrics.SHADOW, brilho=True):
    """Cartão com sombra sólida deslocada, contorno e faixa de brilho no topo."""
    rect = pygame.Rect(rect)
    if sombra:
        pygame.draw.rect(superficie, borda, rect.move(0, sombra), border_radius=raio)
    pygame.draw.rect(superficie, cor, rect, border_radius=raio)
    if brilho:
        faixa = pygame.Rect(rect.x + 6, rect.y + 5, rect.w - 12, max(4, rect.h // 7))
        pygame.draw.rect(superficie, clarear(cor, 0.35), faixa, border_radius=raio // 2)
    pygame.draw.rect(superficie, borda, rect, Metrics.OUTLINE, border_radius=raio)


def estrela(superficie, centro, raio, cheia=True, cor=Palette.COIN):
    cx, cy = centro
    pontos = []
    for i in range(10):
        r = raio if i % 2 == 0 else raio * 0.45
        ang = -math.pi / 2 + i * math.pi / 5
        pontos.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    pygame.draw.polygon(superficie, cor if cheia else Palette.LOCKED, pontos)
    if cheia:
        brilho = [(cx + (x - cx) * 0.55, cy + (y - cy) * 0.55 - raio * 0.12) for x, y in pontos]
        pygame.draw.polygon(superficie, clarear(cor, 0.45), brilho)
    pygame.draw.polygon(superficie, Palette.INK, pontos, max(2, int(raio // 7)))


def clarear(cor, quanto):
    return tuple(min(255, int(c + (255 - c) * quanto)) for c in cor[:3])


def escurecer(cor, quanto):
    return tuple(max(0, int(c * (1 - quanto))) for c in cor[:3])


def aproximar(atual, alvo, dt, tempo_ms=Motion.HOVER_MS):
    """Suavização exponencial independente da taxa de quadros."""
    if tempo_ms <= 0:
        return alvo
    return alvo + (atual - alvo) * math.exp(-dt * 1000 / (tempo_ms / 3))


def ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


ESTILOS = {
    'primario': (Palette.PIPE_MID, Palette.WHITE),
    'secundario': (Palette.PANEL_LIGHT, Palette.INK),
    'perigo': (Palette.DANGER, Palette.WHITE),
    'destaque': (Palette.BIRD_YELLOW, Palette.WHITE),
}


class Botao:
    """Botão com hover animado (cresce e clareia), clique e estado desabilitado.

    detalhe: texto pequeno à direita (ex.: "12/75"); icone: superfície à esquerda.
    """

    def __init__(self, rect, rotulo, acao=None, estilo='primario', detalhe='', icone=None,
                 habilitado=True, tamanho_texto=34, mostrar_estrela=False):
        self.rect = pygame.Rect(rect)
        self.rotulo, self.acao, self.estilo = rotulo, acao, estilo
        self.detalhe, self.icone = detalhe, icone
        self.habilitado = habilitado
        self.tamanho_texto = tamanho_texto
        self.mostrar_estrela = mostrar_estrela
        self.foco = False
        self.hover = 0.0          # 0 a 1, animado
        self.apertado = False

    def contem(self, pos):
        return self.rect.collidepoint(pos)

    def atualizar(self, dt):
        alvo = 1.0 if (self.foco and self.habilitado) else 0.0
        self.hover = aproximar(self.hover, alvo, dt)

    def ativar(self):
        if self.habilitado and self.acao:
            self.acao()
            return True
        return False

    def desenhar(self, superficie):
        escala = 1 + (Motion.HOVER_SCALE - 1) * self.hover
        rect = self.rect.inflate(self.rect.w * (escala - 1), self.rect.h * (escala - 1))
        if self.apertado:
            rect.y += 3
        fundo, cor_texto = ESTILOS[self.estilo]
        if not self.habilitado:
            fundo, cor_texto = Palette.LOCKED, Palette.PANEL_LIGHT
        else:
            fundo = clarear(fundo, 0.18 * self.hover)
        painel(superficie, rect, fundo, sombra=0 if self.apertado else Metrics.SHADOW - 1)
        x = rect.x + 16
        if self.icone:
            caixa = pygame.Rect(0, 0, rect.h - 14, rect.h - 14)
            caixa.midleft = (rect.x + 8, rect.centery)
            pygame.draw.rect(superficie, escurecer(fundo, 0.25), caixa, border_radius=8)
            superficie.blit(self.icone, self.icone.get_rect(center=caixa.center))
            x = caixa.right + 12
        contorno = Palette.INK if cor_texto == Palette.WHITE else None
        rotulo = texto(self.rotulo, self.tamanho_texto, cor_texto, contorno, 2)
        superficie.blit(rotulo, rotulo.get_rect(midleft=(x, rect.centery))
                        if self.icone else rotulo.get_rect(center=rect.center))
        if self.detalhe:
            detalhe = texto(self.detalhe, 24, Palette.INK if cor_texto == Palette.INK else Palette.WHITE,
                            None if cor_texto == Palette.INK else Palette.INK, 1)
            alvo = detalhe.get_rect(midright=(rect.right - 16, rect.centery))
            superficie.blit(detalhe, alvo)
            if self.mostrar_estrela:
                estrela(superficie, (alvo.x - 14, rect.centery), 10, True)


class GrupoBotoes:
    """Foco por mouse ou teclado (setas e ENTER) sobre uma lista de botões."""

    def __init__(self, botoes, colunas=1):
        self.botoes = botoes
        self.colunas = colunas
        self.indice = next((i for i, b in enumerate(botoes) if b.habilitado), 0)
        self._sincronizar()

    def _sincronizar(self):
        for i, b in enumerate(self.botoes):
            b.foco = i == self.indice

    def mover(self, passo):
        n = len(self.botoes)
        i = self.indice
        for _ in range(n):
            i = (i + passo) % n
            if self.botoes[i].habilitado:
                self.indice = i
                break
        self._sincronizar()

    def focar(self, botao):
        if botao in self.botoes and botao.habilitado:
            self.indice = self.botoes.index(botao)
            self._sincronizar()

    def tratar_evento(self, evento):
        """Devolve True se o evento foi consumido (ativou ou moveu o foco)."""
        if evento.type == pygame.MOUSEMOTION:
            for b in self.botoes:
                if b.contem(evento.pos) and b.habilitado:
                    self.focar(b)
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for b in self.botoes:
                if b.contem(evento.pos) and b.habilitado:
                    b.apertado = True
            return False
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            for b in self.botoes:
                foi = b.apertado and b.contem(evento.pos)
                b.apertado = False
                if foi:
                    self.focar(b)
                    return b.ativar()
            return False
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_DOWN, pygame.K_s) if self.colunas == 1 else evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.mover(1)
                return True
            if evento.key in (pygame.K_UP, pygame.K_w) if self.colunas == 1 else evento.key in (pygame.K_LEFT, pygame.K_a):
                self.mover(-1)
                return True
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.botoes[self.indice].ativar()
        return False

    def atualizar(self, dt):
        for b in self.botoes:
            b.atualizar(dt)

    def desenhar(self, superficie):
        for b in self.botoes:
            b.desenhar(superficie)
