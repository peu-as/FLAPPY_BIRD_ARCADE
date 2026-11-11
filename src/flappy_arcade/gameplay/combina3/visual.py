"""Desenho do Combina 3: peças, tabuleiro, animações e efeitos.

Peças em pixel art com as cores bem separadas (azul, verde, branco, dourado,
marrom e vermelho). Cada peça tem uma posição na tela que persegue a casa onde
ela está no tabuleiro: é isso que anima a troca, a queda e o embaralhamento.
"""
import math
import random

import pygame

from ...config.combina3 import CELULA, COLUNAS, LINHAS
from ...config.constants import LARGURA
from ...ui.theme import Palette
from ...ui.widgets import texto
from ..bonus_visuals import DESENHOS, PALETA, pixel_art
from ..coins import icone_moeda
from ..estilingue.visual import _textura
from .tabuleiro import ARCO, LINHA_H, LINHA_V, OVO

X0 = (LARGURA - COLUNAS * CELULA) // 2
Y0 = 178
AREA = pygame.Rect(X0, Y0, COLUNAS * CELULA, LINHAS * CELULA)
TAMANHO_PECA = 48
CORES_TIPO = {'pena': (110, 200, 255), 'folha': (110, 220, 110), 'ovo': (252, 244, 220),
              'moeda': (255, 214, 64), 'semente': (170, 110, 60), 'fruta': (232, 60, 72)}
CORES_ARCO = [(232, 60, 72), (255, 150, 40), (255, 222, 72), (110, 220, 110), (110, 200, 255), (170, 110, 230)]
PALETA_LOCAL = {**PALETA, 'R': (232, 60, 72), 'D': (168, 32, 52), 'h': (255, 170, 170)}
OVO_LISO = (
    ".....oooo.....",
    "...oowwwwoo...",
    "..owwwwwwcko..",
    ".owwwwwwwccko.",
    ".owwwwwwwccko.",
    "owwwwwwwwcccko",
    "owwwwwwwwcccko",
    "owwwwwwwccccko",
    "owwwwwwwccccko",
    "owwwwwwcccccko",
    ".owwwwwccccko.",
    ".owwwwcccccko.",
    "..owwcccckko..",
    "...ookkkkoo...",
    ".....oooo.....",
)
FRUTA = (
    "........oGGo....",
    ".......oGvGo....",
    "......oMoGo.....",
    ".....oMo.o......",
    "...oooMooo......",
    "..oRRRoRRRo.....",
    ".oRhhRRRRRRo....",
    "oRhhRRRRRRRDo...",
    "oRhRRRRRRRRDo...",
    "oRRRRRRRRRRDo...",
    "oRRRRRRRRRDDo...",
    "oRRRRRRRRRDDo...",
    ".oRRRRRRRDDo....",
    "..oRRRRDDDo.....",
    "...ooooooo......",
)


def _arte(desenho, escala=3):
    largura = max(len(linha) for linha in desenho)
    pequeno = pygame.Surface((largura, len(desenho)), pygame.SRCALPHA)
    for y, linha in enumerate(desenho):
        for x, ch in enumerate(linha):
            if ch in PALETA_LOCAL:
                pequeno.set_at((x, y), PALETA_LOCAL[ch])
    return pygame.transform.scale(pequeno, (largura * escala, len(desenho) * escala))


def centro_da_casa(l, c):
    return X0 + c * CELULA + CELULA // 2, Y0 + l * CELULA + CELULA // 2


def casa_em(pos):
    """Casa do tabuleiro sob um ponto da tela, ou None."""
    if not AREA.collidepoint(pos):
        return None
    return int((pos[1] - Y0) // CELULA), int((pos[0] - X0) // CELULA)


class VisualCombina3:
    def __init__(self, recursos):
        self.r = recursos
        self.efeitos = True
        self.sorteio = random.Random(11)
        self.icones = {
            'pena': pixel_art(DESENHOS['GEMEO'], 3), 'folha': pixel_art(DESENHOS['MOLA'], 3),
            'semente': pixel_art(DESENHOS['TURBO'], 3), 'ovo': _arte(OVO_LISO), 'fruta': _arte(FRUTA),
            'moeda': pygame.transform.smoothscale(icone_moeda(24), (TAMANHO_PECA, TAMANHO_PECA)),
        }
        self.posicoes = {}               # id da peça -> [x, y]
        self.alvos = {}                  # id da peça -> (x, y)
        self.fantasmas = []              # peças estourando: [peca, x, y, idade]
        self.particulas = []             # [x, y, vx, vy, idade, cor]
        self.raios = []                  # [tipo, dados, idade]
        self.textos = []                 # [x, y, conteudo, cor, idade, tamanho]
        self.vaivem = None               # (id_a, id_b, direção (dx, dy), idade)
        self.fundo = None
        self._caixas = {}
        self._painel = self._montar_painel()

    # ------------------------------------------------------------ preparo
    def preparar_fundo(self, retrato):
        fundo = retrato.copy()
        escuro = pygame.Surface(fundo.get_size(), pygame.SRCALPHA)
        escuro.fill((20, 16, 40, 110))
        fundo.blit(escuro, (0, 0))
        self.fundo = fundo

    @staticmethod
    def _montar_painel():
        painel = pygame.Surface(AREA.inflate(20, 20).size, pygame.SRCALPHA)
        pygame.draw.rect(painel, (*Palette.INK, 215), painel.get_rect(), border_radius=16)
        for l in range(LINHAS):
            for c in range(COLUNAS):
                cor = (255, 255, 255, 26 if (l + c) % 2 else 14)
                pygame.draw.rect(painel, cor, (10 + c * CELULA + 2, 10 + l * CELULA + 2, CELULA - 4, CELULA - 4),
                                 border_radius=8)
        return painel

    # ------------------------------------------------------------ sincronia com o tabuleiro
    def sincronizar(self, tab, movimentos=()):
        """Cada peça passa a perseguir a casa onde está. Peças novas começam de onde vêm (movimentos)."""
        origem = {peca.id: linha for peca, linha, _ in movimentos}
        vivos = set()
        for l in range(tab.linhas):
            for c in range(tab.colunas):
                peca = tab.grade[l][c]
                if peca is None:
                    continue
                vivos.add(peca.id)
                alvo = centro_da_casa(l, c)
                self.alvos[peca.id] = alvo
                if peca.id not in self.posicoes:
                    y = centro_da_casa(origem[peca.id], c)[1] if peca.id in origem else alvo[1]
                    self.posicoes[peca.id] = [alvo[0], y]
        for ident in list(self.posicoes):
            if ident not in vivos:
                del self.posicoes[ident]
                self.alvos.pop(ident, None)

    def ao_aplicar(self, onda):
        """Antes de as peças sumirem do tabuleiro: estouros, raios e pontos na tela."""
        xs, ys = [], []
        for (l, c), peca in onda.limpas.items():
            x, y = self.posicoes.get(peca.id, centro_da_casa(l, c))
            self.fantasmas.append([peca, x, y, 0.0])
            xs.append(x)
            ys.append(y)
            if self.efeitos:
                cor = CORES_TIPO.get(peca.tipo, (255, 255, 255))
                for _ in range(5):
                    ang = self.sorteio.uniform(0, math.tau)
                    vel = self.sorteio.uniform(60, 190)
                    self.particulas.append([x, y, vel * math.cos(ang), vel * math.sin(ang), 0.0, cor])
        for efeito in onda.efeitos:
            self.raios.append([efeito[0], efeito[1:], 0.0])
        if xs:
            self.textos.append([sum(xs) / len(xs), sum(ys) / len(ys), f'+{onda.pontos}', Palette.WHITE, 0.0, 28])
        if onda.multiplicador >= 2:
            self.textos.append([LARGURA // 2, Y0 - 22, f'COMBO x{onda.multiplicador}!', Palette.BIRD_YELLOW, 0.0, 34])

    def moedas(self, casa, quantidade):
        x, y = centro_da_casa(*casa)
        self.textos.append([x, y - 30, f'+{quantidade}', Palette.COIN, 0.0, 26])

    def tremer(self, peca_a, peca_b, a, b):
        """Troca que não combina: as duas vão e voltam."""
        self.vaivem = (peca_a.id, peca_b.id, (b[1] - a[1], b[0] - a[0]), 0.0)

    def atualizar(self, dt):
        for ident, pos in self.posicoes.items():
            ax, ay = self.alvos[ident]
            for i, alvo in ((0, ax), (1, ay)):
                falta = alvo - pos[i]
                passo = max(14.0, abs(falta) * 0.34)
                pos[i] = alvo if abs(falta) <= passo else pos[i] + math.copysign(passo, falta)
        self.fantasmas = [[p, x, y, t + dt] for p, x, y, t in self.fantasmas if t < 0.2]
        vivas = []
        for p in self.particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 500 * dt
            p[4] += dt
            if p[4] < 0.45:
                vivas.append(p)
        self.particulas = vivas
        self.raios = [[t, d, idade + dt] for t, d, idade in self.raios if idade < 0.3]
        self.textos = [[x, y - 36 * dt, c, cor, idade + dt, tam] for x, y, c, cor, idade, tam in self.textos
                       if idade < 0.9]
        if self.vaivem:
            a, b, direcao, idade = self.vaivem
            self.vaivem = (a, b, direcao, idade + dt) if idade < 0.26 else None

    def parado(self):
        """Nenhuma peça em movimento e nenhum estouro em andamento."""
        if self.fantasmas or self.vaivem:
            return False
        return all(abs(pos[0] - self.alvos[i][0]) < 1 and abs(pos[1] - self.alvos[i][1]) < 1
                   for i, pos in self.posicoes.items())

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela, tab, tempo, selecao=None, cursor=None, dica=None):
        if self.fundo is not None:
            tela.blit(self.fundo, (0, 0))
        else:
            tela.fill(Palette.SKY_DEEP)
        tela.blit(self._painel, AREA.inflate(20, 20))
        self._obstaculos(tela, tab)
        if selecao is not None:
            pygame.draw.rect(tela, Palette.WHITE, self._caixa_da_casa(selecao), 4, border_radius=10)
        elif cursor is not None:
            pygame.draw.rect(tela, Palette.BIRD_YELLOW, self._caixa_da_casa(cursor), 3, border_radius=10)
        recorte = tela.get_clip()
        tela.set_clip(AREA.inflate(8, 8))
        for l in range(tab.linhas):
            for c in range(tab.colunas):
                peca = tab.grade[l][c]
                if peca is None or peca.id not in self.posicoes:
                    continue
                x, y = self.posicoes[peca.id]
                x, y = self._com_vaivem(peca.id, x, y)
                pulso = 0.0
                if dica and (l, c) in dica:
                    pulso = 0.5 + 0.5 * math.sin(tempo * 9)
                self._peca(tela, peca, x, y, tempo, 1 + 0.12 * pulso)
        for peca, x, y, idade in self.fantasmas:
            self._peca(tela, peca, x, y, tempo, max(0.05, 1 - idade / 0.2), alfa=int(255 * (1 - idade / 0.2)))
        tela.set_clip(recorte)
        self._efeitos(tela)

    @staticmethod
    def _caixa_da_casa(casa):
        x, y = centro_da_casa(*casa)
        return pygame.Rect(x - CELULA // 2 + 3, y - CELULA // 2 + 3, CELULA - 6, CELULA - 6)

    def _com_vaivem(self, ident, x, y):
        if not self.vaivem or ident not in self.vaivem[:2]:
            return x, y
        a, b, (dx, dy), idade = self.vaivem
        desvio = math.sin(min(1.0, idade / 0.26) * math.pi) * CELULA * 0.4 * (1 if ident == a else -1)
        return x + dx * desvio, y + dy * desvio

    def _obstaculos(self, tela, tab):
        for l in range(tab.linhas):
            for c in range(tab.colunas):
                caixa = self._caixa_da_casa((l, c)).inflate(4, 4)
                if tab.pedra[l][c]:
                    tela.blit(self._bloco('pedra', 0), caixa)
                elif tab.caixa[l][c] > 0:
                    tela.blit(self._bloco('madeira', 0 if tab.caixa[l][c] >= 2 else 2), caixa)
                elif tab.gelo[l][c] > 0:
                    gelo = pygame.Surface(caixa.size, pygame.SRCALPHA)
                    pygame.draw.rect(gelo, (176, 224, 248, 90 + 60 * min(2, tab.gelo[l][c])), gelo.get_rect(),
                                     border_radius=8)
                    pygame.draw.rect(gelo, (232, 248, 255, 230), gelo.get_rect(), 3, border_radius=8)
                    pygame.draw.line(gelo, (255, 255, 255, 200), (8, caixa.h - 12), (22, 8), 3)
                    tela.blit(gelo, caixa)

    def _bloco(self, material, estagio):
        chave = (material, estagio)
        if chave not in self._caixas:
            self._caixas[chave] = _textura(material, CELULA - 2, CELULA - 2, estagio)
        return self._caixas[chave]

    def _peca(self, tela, peca, x, y, tempo, escala=1.0, alfa=255):
        centro = (round(x), round(y))
        if peca.especial == ARCO:
            img = self._orbe(tempo)
        else:
            img = self.icones[peca.tipo]
            if peca.especial == OVO and alfa == 255:
                raio = 30 + 2 * math.sin(tempo * 8)
                pygame.draw.circle(tela, (255, 150, 40), centro, round(raio), 5)
                pygame.draw.circle(tela, (255, 236, 120), centro, round(raio) - 5, 2)
        if escala != 1.0 or alfa != 255:
            lado = max(2, round(img.get_width() * escala)), max(2, round(img.get_height() * escala))
            img = pygame.transform.scale(img, lado)
            if alfa != 255:
                img.set_alpha(alfa)
        tela.blit(img, img.get_rect(center=centro))
        if peca.especial in (LINHA_H, LINHA_V) and alfa == 255:
            self._setas(tela, centro, peca.especial == LINHA_H, tempo)

    @staticmethod
    def _setas(tela, centro, horizontal, tempo):
        afasta = 27 + 2 * math.sin(tempo * 8)
        for sinal in (-1, 1):
            if horizontal:
                ponta = (centro[0] + sinal * (afasta + 7), centro[1])
                base = [(centro[0] + sinal * afasta, centro[1] - 8), (centro[0] + sinal * afasta, centro[1] + 8)]
            else:
                ponta = (centro[0], centro[1] + sinal * (afasta + 7))
                base = [(centro[0] - 8, centro[1] + sinal * afasta), (centro[0] + 8, centro[1] + sinal * afasta)]
            pygame.draw.polygon(tela, Palette.WHITE, [ponta, *base])
            pygame.draw.polygon(tela, Palette.INK, [ponta, *base], 2)

    def _orbe(self, tempo):
        orbe = pygame.Surface((TAMANHO_PECA + 4, TAMANHO_PECA + 4), pygame.SRCALPHA)
        centro = (orbe.get_width() // 2, orbe.get_height() // 2)
        giro = tempo * 2.5 if self.efeitos else 0.0
        for i, cor in enumerate(CORES_ARCO):
            a0 = giro + i * math.tau / 6
            pontos = [centro] + [(centro[0] + 25 * math.cos(a0 + k * math.tau / 30),
                                  centro[1] + 25 * math.sin(a0 + k * math.tau / 30)) for k in range(6)]
            pygame.draw.polygon(orbe, cor, pontos)
        pygame.draw.circle(orbe, Palette.INK, centro, 25, 3)
        pygame.draw.circle(orbe, (255, 255, 255), (centro[0] - 8, centro[1] - 9), 5)
        return orbe

    def _efeitos(self, tela):
        for x, y, vx, vy, idade, cor in self.particulas:
            pygame.draw.rect(tela, cor, (round(x), round(y), 5, 5))
        for tipo, dados, idade in self.raios:
            t = min(1.0, idade / 0.3)
            alfa = int(230 * (1 - t))
            if tipo in (LINHA_H, LINHA_V):
                if tipo == LINHA_H:
                    faixa = pygame.Rect(AREA.x, Y0 + dados[0] * CELULA + 12, AREA.w, CELULA - 24)
                else:
                    faixa = pygame.Rect(X0 + dados[0] * CELULA + 12, AREA.y, CELULA - 24, AREA.h)
                camada = pygame.Surface(faixa.size, pygame.SRCALPHA)
                camada.fill((200, 236, 255, alfa))
                tela.blit(camada, faixa)
            elif tipo == 'explosao':
                l, c, alcance = dados
                x, y = centro_da_casa(l, c)
                raio = (alcance + 0.5) * CELULA
                pygame.draw.circle(tela, (252, 238, 200), (x, y), max(3, round(raio * t)), 6)
                pygame.draw.circle(tela, (232, 92, 48), (x, y), max(3, round(raio * 0.7 * t)), 3)
            elif tipo == ARCO and self.efeitos:
                origem, casas = dados
                ox, oy = centro_da_casa(*origem)
                for i, casa in enumerate(casas):
                    pygame.draw.line(tela, CORES_ARCO[i % 6], (ox, oy), centro_da_casa(*casa), 3)
        for x, y, conteudo, cor, idade, tamanho in self.textos:
            img = texto(conteudo, tamanho, cor).copy()
            img.set_alpha(max(0, 255 - int(idade * 280)))
            tela.blit(img, img.get_rect(center=(round(x), round(y))))

