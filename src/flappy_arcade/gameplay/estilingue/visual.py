"""Desenho do Estilingue: texturas dos blocos, personagens, estilingue, mira e efeitos.

Tudo em pixel art feito por código (blocos) ou com os sprites do jogo
(pássaros, insetos = o Rei-Inseto da Galaga em miniatura, Kong, barris).
Nada aqui mexe na física: só lê as peças do mundo.
"""
import math
import random

import pygame

from ...config import estilingue as cfg
from ...config.constants import ALTURA, LARGURA, Y_CHAO
from ...ui.widgets import texto
from ..bonus_visuals import EstiloBonus
from .mundo import BARRIL, BLOCO, CHEFE, INSETO

CORES_MATERIAL = {
    'madeira': ((196, 132, 70), (150, 96, 50), (92, 56, 30)),     # base, veio, contorno
    'gelo': ((176, 224, 248), (232, 248, 255), (92, 150, 200)),
    'pedra': ((150, 152, 162), (118, 120, 132), (72, 72, 84)),
}
COR_ELASTICO = (70, 38, 22)
COR_GARFO = ((120, 74, 38), (84, 50, 26))
PARALAXE_FUNDO = 0.3


def _textura(material, largura, altura, estagio):
    base, veio, contorno = CORES_MATERIAL[material]
    sup = pygame.Surface((largura, altura), pygame.SRCALPHA)
    sup.fill((*base, 235 if material == 'gelo' else 255))
    sorteio = random.Random(largura * 131 + altura * 7)          # mesma textura sempre
    if material == 'madeira':
        horizontal = largura >= altura
        for i in range(4, (altura if horizontal else largura), 7):
            if horizontal:
                pygame.draw.line(sup, veio, (2, i), (largura - 3, i), 1)
            else:
                pygame.draw.line(sup, veio, (i, 2), (i, altura - 3), 1)
        for cx, cy in ((5, 5), (largura - 6, 5), (5, altura - 6), (largura - 6, altura - 6)):
            if largura > 14 and altura > 14:
                pygame.draw.circle(sup, contorno, (cx, cy), 1)
    elif material == 'gelo':
        pygame.draw.line(sup, veio, (3, altura - 4), (min(largura, altura) - 4, 3), 3)
        pygame.draw.line(sup, (255, 255, 255), (4, 4), (largura // 3, 4), 2)
    else:
        for _ in range(max(2, largura * altura // 180)):
            x, y = sorteio.randrange(2, max(3, largura - 2)), sorteio.randrange(2, max(3, altura - 2))
            pygame.draw.rect(sup, veio, (x, y, 3, 2))
    for i in range(estagio * 2):                                    # rachaduras
        x0 = sorteio.uniform(0.2, 0.8) * largura
        y0 = sorteio.uniform(0.2, 0.8) * altura
        pontos = [(x0, y0)]
        for _ in range(3):
            x0 += sorteio.uniform(-9, 9)
            y0 += sorteio.uniform(-9, 9)
            pontos.append((min(largura - 2, max(1, x0)), min(altura - 2, max(1, y0))))
        pygame.draw.lines(sup, contorno, False, pontos, 2)
    pygame.draw.rect(sup, contorno, sup.get_rect(), 2)
    return sup


class Visual:
    def __init__(self, recursos):
        self.r = recursos
        self.estilo = EstiloBonus(recursos)              # ícones dos bônus (pena, semente, ovo)
        self._texturas = {}
        self._sprites = {}
        self.particulas = []                             # [x, y, vx, vy, idade, vida, cor, tamanho]
        self.aneis = []                                  # explosões: [x, y, raio_max, idade]
        self.textos = []                                 # [x, y, texto, cor, idade]
        self.rastro = []                                 # pontos do último voo (mundo)
        self.rastro_anterior = []
        self.fundo = None
        self.efeitos = True
        self.sorteio = random.Random(5)

    # ------------------------------------------------------------ preparo
    def preparar_fundo(self, retrato):
        """O cenário do jogador, espelhado para rolar sem emenda."""
        faixa = pygame.Surface((LARGURA * 2, ALTURA))
        faixa.blit(retrato, (0, 0))
        faixa.blit(pygame.transform.flip(retrato, True, False), (LARGURA, 0))
        self.fundo = faixa

    def textura(self, peca):
        estagio = 0 if peca.dano < 0.34 else 1 if peca.dano < 0.67 else 2
        chave = (peca.material, *peca.tamanho, estagio)
        if chave not in self._texturas:
            self._texturas[chave] = _textura(peca.material, *[round(v) for v in peca.tamanho], estagio)
        return self._texturas[chave]

    def sprite(self, chave, fabrica):
        if chave not in self._sprites:
            self._sprites[chave] = fabrica()
        return self._sprites[chave]

    def sprite_inseto(self, raio):
        tamanho = round(raio * 2.6)
        return self.sprite(('inseto', tamanho), lambda: pygame.transform.smoothscale(
            self.r.chefe_galaga, (tamanho, round(tamanho * 0.79))))

    def sprite_chefe(self, nome, raio, bravo):
        if nome == 'kong':
            base = (self.r.kong_furioso if bravo else self.r.kong)['parado']
            largura = round(raio * 2.3)
            return self.sprite(('kong', bravo, largura), lambda: pygame.transform.smoothscale(
                base, (largura, round(largura * base.get_height() / base.get_width()))))
        return self.sprite_inseto(raio * 1.05)

    def sprite_passaro(self, tipo, skin, raio):
        definicao = cfg.PASSAROS[tipo]
        if not definicao.sprite:
            base = skin.sprite_para(0) if skin is not None else self.r.passaros['dia'][0]
            chave = ('skin', getattr(skin, 'id', 'classico'), round(raio))
        else:
            base = self.r.especiais[definicao.sprite]
            chave = ('especial', definicao.sprite, round(raio))
        largura = round(raio * 2.9)
        return self.sprite(chave, lambda: pygame.transform.smoothscale(
            base, (largura, round(largura * base.get_height() / base.get_width()))))

    # ------------------------------------------------------------ eventos
    def ao_quebrar(self, peca):
        x, y = peca.posicao
        if peca.tipo == BLOCO:
            cor = CORES_MATERIAL[peca.material][0]
            n = 8
        elif peca.tipo in (INSETO, CHEFE):
            cor, n = (110, 220, 110), 14
            self.texto(x, y - 30, f'+{peca.pontos}', (255, 236, 80))
        else:
            cor, n = (150, 96, 52), 10
        if not self.efeitos:
            return
        for _ in range(n):
            ang = self.sorteio.uniform(0, math.tau)
            vel = self.sorteio.uniform(80, 260)
            self.particulas.append([x, y, vel * math.cos(ang), vel * math.sin(ang) - 120, 0.0,
                                    self.sorteio.uniform(0.5, 0.9), cor, self.sorteio.randint(3, 7)])

    def ao_explodir(self, centro, raio):
        self.aneis.append([centro[0], centro[1], raio, 0.0])

    def texto(self, x, y, conteudo, cor):
        self.textos.append([x, y, conteudo, cor, 0.0])

    def atualizar(self, dt):
        vivas = []
        for p in self.particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += cfg.GRAVIDADE * 0.8 * dt
            p[4] += dt
            if p[4] < p[5]:
                vivas.append(p)
        self.particulas = vivas
        self.aneis = [[*a[:3], a[3] + dt] for a in self.aneis if a[3] < 0.45]
        self.textos = [[t[0], t[1] - 40 * dt, t[2], t[3], t[4] + dt] for t in self.textos if t[4] < 1.1]

    # ------------------------------------------------------------ desenho
    def desenhar_fundo(self, tela, camera):
        if self.fundo is None:
            tela.blit(self.r.fundos['bg'], (0, 0))
        else:
            x = -int(camera * PARALAXE_FUNDO) % self.fundo.get_width()
            tela.blit(self.fundo, (x - self.fundo.get_width(), 0))
            tela.blit(self.fundo, (x, 0))
        chao = self.r.chao
        x = -int(camera) % chao.get_width()
        for dx in (-chao.get_width(), 0, chao.get_width()):
            tela.blit(chao, (x + dx, Y_CHAO))

    def desenhar_estilingue(self, tela, camera, ancora, puxada, frente):
        """frente=False: braço de trás (antes do pássaro); True: braço da frente e elástico."""
        x = cfg.X_ESTILINGUE - camera
        topo = Y_CHAO - cfg.ALTURA_ESTILINGUE
        claro, escuro = COR_GARFO
        if not frente:
            pygame.draw.line(tela, escuro, (x + 12, topo + 6), (x + 2, topo + 46), 9)
            if puxada is not None:
                pygame.draw.line(tela, COR_ELASTICO, (x + 12, topo + 6), puxada, 6)
            return
        pygame.draw.line(tela, claro, (x, Y_CHAO), (x, topo + 50), 12)
        pygame.draw.line(tela, claro, (x, topo + 50), (x - 12, topo + 4), 10)
        pygame.draw.line(tela, escuro, (x, Y_CHAO), (x, topo + 50), 3)
        if puxada is not None:
            pygame.draw.line(tela, COR_ELASTICO, (x - 12, topo + 6), puxada, 6)
            pygame.draw.circle(tela, COR_ELASTICO, puxada, 6)

    def desenhar_mira(self, tela, camera, pontos):
        for i, (x, y) in enumerate(pontos):
            raio = 4 if i % 2 == 0 else 3
            pygame.draw.circle(tela, (255, 255, 255), (round(x - camera), round(y)), raio)
            pygame.draw.circle(tela, (40, 30, 36), (round(x - camera), round(y)), raio, 1)

    def desenhar_rastros(self, tela, camera):
        for i, (x, y) in enumerate(self.rastro_anterior[::2]):
            pygame.draw.circle(tela, (235, 235, 235), (round(x - camera), round(y)), 2 if i % 3 else 3)
        for i, (x, y) in enumerate(self.rastro[::2]):
            pygame.draw.circle(tela, (255, 255, 255), (round(x - camera), round(y)), 3 if i % 3 else 4)

    def desenhar_pecas(self, tela, camera, mundo, skin, tempo):
        for peca in mundo.pecas:
            if peca.morta:
                continue
            x, y = peca.posicao
            sx = x - camera
            if sx < -160 or sx > LARGURA + 160:
                continue
            graus = -math.degrees(peca.corpo.angle)
            if peca.tipo == BLOCO:
                img = pygame.transform.rotate(self.textura(peca), graus)
            elif peca.tipo == INSETO:
                img = pygame.transform.rotate(self.sprite_inseto(peca.raio), graus)
                if peca.dano > 0:
                    img = self._ferido(img, tempo)
            elif peca.tipo == CHEFE:
                img = pygame.transform.rotate(self.sprite_chefe(peca.nome, peca.raio, peca.dano > 0.5), graus * 0.3)
                if peca.dano > 0:
                    img = self._ferido(img, tempo)
            elif peca.tipo == BARRIL:
                img = pygame.transform.rotate(self.r.barril, graus)
            else:
                continue
            tela.blit(img, img.get_rect(center=(round(sx), round(y))))
        for chefe in mundo.vivos(CHEFE):                 # por cima das tábuas da fortaleza
            self._barra_de_vida(tela, chefe.posicao.x - camera, chefe.posicao.y - chefe.raio - 24, chefe)

    def desenhar_passaros(self, tela, camera, mundo, skin):
        for p in mundo.passaros_no_ar:
            v = p.corpo.velocity
            graus = -math.degrees(math.atan2(v.y, v.x)) if v.length > 60 else -math.degrees(p.corpo.angle)
            img = pygame.transform.rotate(self.sprite_passaro(p.nome, skin, p.raio), graus)
            centro = (round(p.posicao.x - camera), round(p.posicao.y))
            if p.disparou and self.efeitos:
                for k in range(1, 5):
                    pygame.draw.circle(tela, (255, 200 - k * 30, 60),
                                       (round(centro[0] - v.normalized().x * k * 12),
                                        round(centro[1] - v.normalized().y * k * 12)), 9 - k * 2)
            tela.blit(img, img.get_rect(center=centro))

    def desenhar_fila(self, tela, camera, fila, skin, preparado):
        """Pássaros esperando a vez, no chão atrás do estilingue."""
        x = cfg.X_ESTILINGUE - 50 - camera
        for i, tipo in enumerate(fila[1:] if preparado else fila):
            raio = cfg.PASSAROS[tipo].raio * 0.8
            img = self.sprite_passaro(tipo, skin, raio)
            tela.blit(img, img.get_rect(midbottom=(round(x - i * 42), Y_CHAO - 2)))

    def desenhar_passaro_no_estilingue(self, tela, posicao, tipo, skin, angulo):
        img = pygame.transform.rotate(self.sprite_passaro(tipo, skin, cfg.PASSAROS[tipo].raio), angulo)
        tela.blit(img, img.get_rect(center=(round(posicao[0]), round(posicao[1]))))

    def desenhar_efeitos(self, tela, camera):
        for x, y, vx, vy, idade, vida, cor, tamanho in self.particulas:
            pygame.draw.rect(tela, cor, (round(x - camera), round(y), tamanho, tamanho))
        for x, y, raio, idade in self.aneis:
            t = min(1.0, idade / 0.45)
            if self.efeitos:
                clarao = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                clarao.fill((255, 246, 220, int(70 * (1 - t))))
                tela.blit(clarao, (0, 0))
            pygame.draw.circle(tela, (252, 238, 200), (round(x - camera), round(y)), max(2, round(raio * t)), 6)
            pygame.draw.circle(tela, (232, 92, 48), (round(x - camera), round(y)), max(2, round(raio * 0.7 * t)), 3)
        for x, y, conteudo, cor, idade in self.textos:
            img = texto(conteudo, 26, cor).copy()
            img.set_alpha(max(0, 255 - int(idade * 230)))
            tela.blit(img, img.get_rect(center=(round(x - camera), round(y))))

    @staticmethod
    def _ferido(img, tempo):
        if int(tempo * 8) % 2:
            return img
        img = img.copy()
        img.fill((255, 120, 120), special_flags=pygame.BLEND_RGB_MULT)
        return img

    @staticmethod
    def _barra_de_vida(tela, x, y, peca):
        largura = 80
        caixa = pygame.Rect(0, 0, largura, 10)
        caixa.center = (round(x), round(y))
        pygame.draw.rect(tela, (40, 30, 36), caixa.inflate(4, 4), border_radius=4)
        pygame.draw.rect(tela, (90, 40, 40), caixa, border_radius=3)
        cheia = caixa.copy()
        cheia.w = max(0, round(largura * peca.vida / peca.vida_max))
        pygame.draw.rect(tela, (120, 230, 90), cheia, border_radius=3)

