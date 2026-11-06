"""Aparência das skins (config/skins.py). Nada aqui toca na física.

O Passaro continua colidindo com o sprite original: a skin só é usada em
Passaro.desenhar, centralizada no mesmo retângulo, com a mesma rotação.
"""
import colorsys
import math
import random
from collections import deque

import pygame

from ..config.skins import BARRIGA, BICO, CORPO, CORPO_SOMBRA, PALETA_ORIGINAL, POR_ID

PASSOS_ARCO_IRIS = 12
DESLIZE_RASTRO = 5            # px por quadro: o rastro "fica para trás" como o cenário


def trocar_paleta(sprite, cores):
    """Cópia do sprite com as cores originais trocadas (comparação exata)."""
    novo = sprite.copy()
    pixels = pygame.PixelArray(novo)
    for papel, cor in cores.items():
        pixels.replace(PALETA_ORIGINAL[papel], cor, distance=0)
    del pixels
    return novo


def _cores_do_matiz(matiz):
    corpo = colorsys.hsv_to_rgb(matiz, 0.72, 0.98)
    sombra = colorsys.hsv_to_rgb(matiz, 0.80, 0.80)
    barriga = colorsys.hsv_to_rgb(matiz, 0.28, 1.0)
    return {papel: tuple(round(c * 255) for c in rgb)
            for papel, rgb in ((CORPO, corpo), (CORPO_SOMBRA, sombra), (BARRIGA, barriga))}


class SkinVisual:
    """Desenha uma skin no lugar do pássaro. Uma instância por partida."""

    def __init__(self, skin_id, recursos):
        self.definicao = POR_ID[skin_id]
        self.efeitos = True           # efeitos visuais extras (configuração)
        base = recursos.passaros['dia']
        d = self.definicao
        if d.tipo == 'especial':
            self.quadros = [recursos.especiais[d.sprite]]
        elif d.tipo == 'arte':
            self.quadros = [recursos.arte_skin(d.sprite)]
        else:
            self.quadros = [trocar_paleta(q, d.cores) for q in base]
        self.variantes = None
        if d.efeito == 'arco_iris':
            self.variantes = [[trocar_paleta(q, {**_cores_do_matiz(i / PASSOS_ARCO_IRIS), BICO: PALETA_ORIGINAL[BICO]})
                               for q in base] for i in range(PASSOS_ARCO_IRIS)]
        self.rastro = deque(maxlen=7)
        self.brilhos = []
        self.poeira = []
        self.quadro_atual = 0
        self.aleatorio = random.Random(skin_id)   # nunca usa o random do jogo

    @property
    def id(self):
        return self.definicao.id

    def sprite_para(self, indice):
        if self.variantes:
            matiz = (self.quadro_atual // 3) % PASSOS_ARCO_IRIS
            return self.variantes[matiz][indice % 3]
        return self.quadros[indice % len(self.quadros)]

    def desenhar(self, tela, passaro, angulo):
        self.quadro_atual += 1
        centro = passaro.retangulo().center
        efeito = self.definicao.efeito if self.efeitos else ''
        sprite = pygame.transform.rotate(self.sprite_para(passaro.indice), angulo)
        if efeito in ('arco_iris', 'fantasma', 'neon', 'rastro_arco_iris'):
            self._rastro(tela, sprite, efeito)
        if efeito == 'poeira':
            self._poeira(tela, centro, sprite.get_height())
        if efeito == 'neon':
            self._contorno(tela, sprite, centro)
        if efeito == 'fantasma':
            sprite = sprite.copy()
            sprite.set_alpha(150 + int(60 * math.sin(self.quadro_atual * 0.25)))
        tela.blit(sprite, sprite.get_rect(center=centro))
        if efeito == 'brilho':
            self._brilhos(tela, centro)
        marca = self._silhueta(sprite) if efeito == 'rastro_arco_iris' else sprite
        self.rastro.appendleft([centro[0], centro[1], marca])

    # ---- efeitos ----
    def _rastro(self, tela, sprite_atual, efeito):
        for ponto in self.rastro:
            ponto[0] -= DESLIZE_RASTRO
        for i, (x, y, sprite) in enumerate(self.rastro):
            if i % 2:
                continue
            copia = sprite.copy()
            alfa = {'neon': 80 - i * 12, 'rastro_arco_iris': 150 - i * 20}.get(efeito, 110 - i * 16)
            copia.set_alpha(max(0, alfa))
            tela.blit(copia, copia.get_rect(center=(x, y)))

    def _silhueta(self, sprite):
        """Sombra colorida do sprite, com a cor girando pelo arco-íris."""
        matiz = (self.quadro_atual % 36) / 36
        cor = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(matiz, 0.65, 1.0))
        return pygame.mask.from_surface(sprite).to_surface(setcolor=(*cor, 255), unsetcolor=(0, 0, 0, 0))

    def _poeira(self, tela, centro, altura):
        """Nuvenzinhas de poeira saindo de trás do pássaro (Dinossauro)."""
        if self.quadro_atual % 3 == 0:
            self.poeira.append([centro[0] - 24 + self.aleatorio.uniform(-4, 4),
                                centro[1] + altura * 0.25 + self.aleatorio.uniform(-6, 6), 0])
        vivas = []
        for nuvem in self.poeira:
            nuvem[0] -= DESLIZE_RASTRO
            nuvem[1] -= 0.4
            nuvem[2] += 1
            if nuvem[2] < 16:
                raio = 4 + nuvem[2] * 0.7
                bolha = pygame.Surface((raio * 2 + 2, raio * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(bolha, (214, 188, 136, max(0, 170 - nuvem[2] * 11)), (raio + 1, raio + 1), raio)
                tela.blit(bolha, (nuvem[0] - raio, nuvem[1] - raio))
                vivas.append(nuvem)
        self.poeira = vivas

    def _contorno(self, tela, sprite, centro):
        rect = sprite.get_rect(center=centro)
        contorno = pygame.mask.from_surface(sprite).outline()
        if len(contorno) > 2:
            fase = (math.sin(self.quadro_atual * 0.2) + 1) / 2
            cor = (64 + int(120 * fase), 248, 232)
            pontos = [(rect.x + x, rect.y + y) for x, y in contorno]
            pygame.draw.lines(tela, cor, True, pontos, 3)

    def _brilhos(self, tela, centro):
        if self.quadro_atual % 4 == 0:
            self.brilhos.append([centro[0] + self.aleatorio.uniform(-30, 30),
                                 centro[1] + self.aleatorio.uniform(-26, 26), 0])
        vivos = []
        for brilho in self.brilhos:
            brilho[0] -= DESLIZE_RASTRO * 0.6
            brilho[2] += 1
            if brilho[2] < 14:
                tamanho = 5 - abs(brilho[2] - 7) * 0.6
                x, y = brilho[0], brilho[1]
                cor = (255, 246, 180)
                pygame.draw.line(tela, cor, (x - tamanho, y), (x + tamanho, y), 2)
                pygame.draw.line(tela, cor, (x, y - tamanho), (x, y + tamanho), 2)
                vivos.append(brilho)
        self.brilhos = vivos
