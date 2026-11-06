"""Visual novo dos bônus (só nos modos novos; o clássico mantém as cápsulas).

Cada bônus vira um item do mundo do pássaro, desenhado em pixel art por código:

  GEMEO       Pena Dupla        pena azul      -> um ala azulado voa ao lado, soltando penas
  BOMBA       Ovo Nova          ovo rachado    -> onda de choque em dois anéis e casca voando
  TURBO       Semente-Foguete   semente/foguete-> rastro de fogo saindo das naves
  BUMERANGUE  Cacho Bumerangue  cacho de banana-> o cacho gira e deixa um arco amarelo
  MOLA        Folha-Trampolim   folha          -> folha sob o pássaro e um anel "BOING!" a cada pulo

Só o desenho muda: o item continua com o mesmo raio de coleta
(CapsulaBonus.RAIO), as mesmas durações (TIPOS_BONUS) e a mesma lógica.
As partículas usam o próprio sorteador (nunca o random do jogo).
"""
import math
import random
import re

import pygame

from ..config.constants import DESLOC_GEMEO, TIPOS_BONUS, Y_NAVE
from ..ui.theme import Fonts
from .hud import texto_vidas_extras

# ---------------------------------------------------------------- nomes
NOMES_NOVOS = {
    'GEMEO': 'PENA DUPLA', 'BOMBA': 'OVO NOVA', 'TURBO': 'SEMENTE-FOGUETE',
    'BUMERANGUE': 'CACHO BUMERANGUE', 'MOLA': 'FOLHA-TRAMPOLIM',
}
_TROCAS = (('CAÇA GÊMEO', NOMES_NOVOS['GEMEO']), ('BOMBA NOVA', NOMES_NOVOS['BOMBA']),
           ('PULO DE MOLA', NOMES_NOVOS['MOLA']), ('BANANA-RANG', NOMES_NOVOS['BUMERANGUE']),
           ('TURBO', NOMES_NOVOS['TURBO']), ('MOLA', NOMES_NOVOS['MOLA']))
_PADRAO = re.compile('|'.join(rf'\b{re.escape(velho)}\b' for velho, _ in _TROCAS))
_NOVO = dict(_TROCAS)


def renomear(texto):
    """'TURBO 7s' -> 'SEMENTE-FOGUETE 7s' (avisos e HUD dos bônus)."""
    return _PADRAO.sub(lambda m: _NOVO[m.group(0)], texto)


# ---------------------------------------------------------------- itens (pixel art)
PALETA = {
    'o': (52, 40, 56),       # contorno (tinta escura, como os sprites originais)
    'w': (250, 250, 250), 'c': (252, 238, 200), 'k': (230, 206, 150),
    'b': (110, 200, 255), 'B': (60, 140, 230), 'l': (200, 236, 255),
    'r': (232, 92, 48), 'y': (255, 222, 72), 'Y': (240, 176, 32), 'f': (255, 140, 40),
    'm': (150, 96, 52), 'M': (110, 66, 36), 'g': (110, 220, 110), 'G': (52, 150, 70), 'v': (190, 250, 170),
    'p': (255, 150, 220),
}
DESENHOS = {
    'GEMEO': (
        "...........ooo..",
        ".........oollbo.",
        "........olllbbo.",
        ".......ollbbbBo.",
        "......ollbbbBo..",
        ".....olbbbbBo...",
        "....olbbbbBo....",
        "...olbbbbBo.....",
        "..olbbbbBo......",
        "..obbbbBo.......",
        "..obbBBo........",
        "...oowo.........",
        "...owo..........",
        "..owo...........",
        ".owo............",
        ".oo.............",
    ),
    'BOMBA': (
        ".....oooo.....",
        "...oowwwwoo...",
        "..owwwwwwcko..",
        ".owwwwwwwccko.",
        ".owwwwwwwccko.",
        "owwwwwwwwcccko",
        "orwwrwwrwwrcko",
        "ofrrfrrfrrfrko",
        "owfwwfwwfwwcko",
        "owwwwwwwwcccko",
        ".owwwwwwcccko.",
        ".owwwwwccccko.",
        "..owwcccckko..",
        "...ookkkkoo...",
        ".....oooo.....",
    ),
    'TURBO': (
        "......oo......",
        ".....omMo.....",
        "....ommmMo....",
        "....ommmMo....",
        "...ommmmmMo...",
        "...ommwmmMo...",
        "...ommmmmMo...",
        "..oommmmmMoo..",
        ".orommmmmMoro.",
        ".orrommmMorro.",
        ".oo.ommmMo.oo.",
        "....oooooo....",
        "....yfyyfy....",
        ".....yffy.....",
        "......ff......",
        "......y.......",
    ),
    'BUMERANGUE': (
        "......opo.......",
        ".....oppo.......",
        "....oMMo........",
        "...oyYMyo.......",
        "..oyyoyYyo......",
        ".oyyoyyoYyo.....",
        ".oyyoyyoyYo.....",
        "oyyoyyoyyYo.....",
        "oyyoyyoyyyYo....",
        "oyyyoyyoyyyYo...",
        ".oyyyoyyoyyyYo..",
        ".oyyyyoyyooyyYoo",
        "..oyyyyooyyyyyYo",
        "...ooyyyyyyyyoo.",
        ".....oooooooo...",
    ),
    'MOLA': (
        "..........ooo...",
        "........oovvgo..",
        "......oovvggGo..",
        ".....ovvgggGGo..",
        "....ovggggGgGo..",
        "...ovgggGGgGo...",
        "..ovggGGgggGo...",
        "..ovgGgggggGo...",
        ".ovgGggggGGo....",
        ".ovGgggGGGo.....",
        ".oGggGGGoo......",
        ".oGGGooo........",
        "ooooo...........",
        "oG..............",
        "o...............",
        "................",
    ),
}
ESCALA_ITEM = 2


def pixel_art(desenho, escala=ESCALA_ITEM):
    largura = max(len(linha) for linha in desenho)
    pequeno = pygame.Surface((largura, len(desenho)), pygame.SRCALPHA)
    for y, linha in enumerate(desenho):
        for x, ch in enumerate(linha):
            if ch in PALETA:
                pequeno.set_at((x, y), PALETA[ch])
    return pygame.transform.scale(pequeno, (largura * escala, len(desenho) * escala))


class EstiloBonus:
    """Desenho dos bônus dentro de uma fase (Galaga ou Donkey) dos modos novos."""

    def __init__(self, recursos):
        self.recursos = recursos
        self.efeitos = True                     # efeitos visuais extras (configuração)
        self.itens = {tipo: pixel_art(d) for tipo, d in DESENHOS.items()}
        self.sorteio = random.Random(13)
        self.fogo = []                          # [x, y, vx, vy, idade]
        self.penas = []                         # [x, y, vx, idade, giro]
        self.cascas = []                        # [x, y, vx, vy, idade, giro]
        self.aneis = []                         # [x, y, idade]
        self.rastros = {}                       # id(bumerangue) -> [(x, y), ...]
        self._onda_anterior = 0.0
        self._vy_anterior = 0.0
        self.quadro = 0
        ala = recursos.nave.copy()
        ala.fill((150, 205, 255), special_flags=pygame.BLEND_RGB_MULT)
        self.ala = ala
        self.cacho = pygame.transform.scale(self.itens['BUMERANGUE'], (26, 24))
        self.folha = pygame.transform.scale(pixel_art(DESENHOS['MOLA'], 1), (30, 18))

    nome = staticmethod(renomear)

    # ------------------------------------------------------------ item coletável
    def desenhar_item(self, tela, capsula, tempo):
        cor = TIPOS_BONUS[capsula.tipo][0]
        centro = (int(capsula.x), int(capsula.y + 3 * math.sin(tempo * 6)))
        raio = capsula.RAIO + 4 + int(2 * math.sin(tempo * 9))
        brilho = pygame.Surface((raio * 2 + 4, raio * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(brilho, (*cor, 70), (raio + 2, raio + 2), raio)
        pygame.draw.circle(brilho, (*cor, 220), (raio + 2, raio + 2), raio, 2)
        tela.blit(brilho, brilho.get_rect(center=centro))
        item = self.itens[capsula.tipo]
        inclina = 8 * math.sin(tempo * 3) if self.efeitos else 0
        if inclina:
            item = pygame.transform.rotate(item, inclina)
        tela.blit(item, item.get_rect(center=centro))

    # ------------------------------------------------------------ Galaga
    def desenhar_naves(self, fase, tela):
        self.quadro += 1
        turbo = fase.efeitos.ativo('TURBO')
        posicoes = (-DESLOC_GEMEO, DESLOC_GEMEO) if fase.gemeo else (0,)
        if turbo and self.efeitos:
            for dx in posicoes:
                for _ in range(2):
                    self.fogo.append([fase.nave_x + dx + self.sorteio.uniform(-6, 6), Y_NAVE + 26,
                                      self.sorteio.uniform(-0.6, 0.6), self.sorteio.uniform(4, 7), 0])
        self._desenhar_fogo(tela)
        for dx in posicoes:
            sprite = self.ala if (fase.gemeo and dx > 0) else self.recursos.nave
            tela.blit(sprite, fase.retangulo_nave().move(dx, 0))
            if turbo:                                  # bocal aceso (também sem efeitos extras)
                x, y = int(fase.nave_x + dx), Y_NAVE + 28
                pygame.draw.circle(tela, PALETA['y'], (x, y), 5)
                pygame.draw.circle(tela, PALETA['f'], (x, y), 5, 2)
        if fase.gemeo and self.efeitos:
            if self.quadro % 7 == 0:
                self.penas.append([fase.nave_x + DESLOC_GEMEO + self.sorteio.uniform(-10, 10), Y_NAVE + 10,
                                   self.sorteio.uniform(-0.8, 0.8), 0, self.sorteio.uniform(0, 360)])
        self._desenhar_penas(tela)

    def _desenhar_fogo(self, tela):
        vivos = []
        for p in self.fogo:
            p[0] += p[2]
            p[1] += p[3]
            p[4] += 1
            if p[4] < 12:
                t = p[4] / 12
                cor = (255, int(230 - 150 * t), int(90 - 80 * t))
                pygame.draw.circle(tela, cor, (int(p[0]), int(p[1])), max(1, int(6 * (1 - t))))
                vivos.append(p)
        self.fogo = vivos

    def _desenhar_penas(self, tela):
        vivas = []
        pena = self.itens['GEMEO']
        for p in self.penas:
            p[0] += p[2] + math.sin(p[3] * 0.3) * 0.8
            p[1] += 2.2
            p[3] += 1
            p[4] += 6
            if p[3] < 26:
                img = pygame.transform.rotozoom(pena, p[4], 0.45)
                img.set_alpha(max(0, 220 - p[3] * 8))
                tela.blit(img, img.get_rect(center=(int(p[0]), int(p[1]))))
                vivas.append(p)
        self.penas = vivas

    def desenhar_onda(self, fase, tela):
        """Ovo Nova: dois anéis, um clarão suave e a casca voando (mesmos 0,5 s da Bomba)."""
        progresso = 1 - fase.onda_bomba / 0.5
        cx, cy = fase.centro_bomba
        if fase.onda_bomba > self._onda_anterior and self.efeitos:      # acabou de estourar
            for i in range(10):
                angulo = i * 36 + self.sorteio.uniform(-12, 12)
                vel = self.sorteio.uniform(9, 15)
                self.cascas.append([cx, cy, vel * math.cos(math.radians(angulo)),
                                    -vel * math.sin(math.radians(angulo)), 0, self.sorteio.uniform(0, 360)])
        self._onda_anterior = fase.onda_bomba
        clarao = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        clarao.fill((255, 246, 220, int(130 * (1 - progresso))))
        tela.blit(clarao, (0, 0))
        pygame.draw.circle(tela, PALETA['c'], (int(cx), int(cy)), int(40 + 760 * progresso), 8)
        pygame.draw.circle(tela, PALETA['r'], (int(cx), int(cy)), int(20 + 560 * progresso), 4)

    def desenhar_cascas(self, tela):
        vivas = []
        for c in self.cascas:
            c[0] += c[2]
            c[1] += c[3]
            c[3] += 0.5
            c[4] += 1
            c[5] += 14
            if c[4] < 24:
                a = math.radians(c[5])
                pontos = [(c[0] + 7 * math.cos(a + k * 2.1), c[1] + 7 * math.sin(a + k * 2.1)) for k in range(3)]
                pygame.draw.polygon(tela, PALETA['w'], pontos)
                pygame.draw.polygon(tela, PALETA['o'], pontos, 1)
                vivas.append(c)
        self.cascas = vivas

    # ------------------------------------------------------------ Donkey
    def desenhar_mola(self, tela, passaro):
        """Folha-Trampolim: a folha sob o pássaro e um anel "BOING!" a cada pulo."""
        ret = passaro.retangulo()
        pulou = passaro.vy <= -4 and self._vy_anterior > passaro.vy + 3
        self._vy_anterior = passaro.vy
        if pulou and self.efeitos:
            self.aneis.append([ret.centerx, ret.bottom + 6, 0])
        balanco = math.sin(self.quadro * 0.3) * 4 if self.efeitos else 0
        self.quadro += 1
        folha = pygame.transform.rotate(self.folha, balanco)
        tela.blit(folha, folha.get_rect(center=(ret.centerx, ret.bottom + 8)))
        vivos = []
        for anel in self.aneis:
            anel[2] += 1
            if anel[2] < 12:
                t = anel[2] / 12
                largura, altura = int(24 + 60 * t), int(8 + 18 * t)
                caixa = pygame.Rect(0, 0, largura, altura)
                caixa.center = (anel[0], anel[1])
                camada = pygame.Surface(caixa.size, pygame.SRCALPHA)
                pygame.draw.ellipse(camada, (*PALETA['g'], int(255 * (1 - t))), camada.get_rect(), 3)
                tela.blit(camada, caixa)
                if anel[2] < 9:
                    boing = Fonts.get(22).render('BOING!', True, PALETA['v'])
                    boing.set_alpha(int(255 * (1 - t)))
                    tela.blit(boing, boing.get_rect(center=(anel[0] + 34, anel[1] - 10 - anel[2] * 2)))
                vivos.append(anel)
        self.aneis = vivos

    def esquecer_mola(self):
        self._vy_anterior = 0.0
        self.aneis.clear()

    def desenhar_bumerangues(self, tela, bumerangues):
        """Cacho Bumerangue: o cacho girando e um arco amarelo atrás dele."""
        ativos = set()
        for b in bumerangues:
            chave = id(b)
            ativos.add(chave)
            rastro = self.rastros.setdefault(chave, [])
            rastro.append((b['x'], b['y']))
            del rastro[:-12]
            if self.efeitos and len(rastro) > 1:
                for i in range(1, len(rastro)):
                    t = i / len(rastro)
                    pygame.draw.line(tela, (255, int(200 + 30 * t), 60), rastro[i - 1], rastro[i],
                                     max(1, int(9 * t)))
            giro = pygame.transform.rotate(self.cacho, b['angulo'])
            tela.blit(giro, giro.get_rect(center=(int(b['x']), int(b['y']))))
        for chave in list(self.rastros):
            if chave not in ativos:
                del self.rastros[chave]


class SessaoComBonusNovos:
    """Mixin dos modos novos: entrega um EstiloBonus à Galaga e ao Donkey da vez.

    Uso: class FreeSession(SessaoComBonusNovos, ..., ClassicSession). O clássico não
    herda isto: suas fases ficam com estilo_bonus = None (as cápsulas originais).
    """

    efeitos_bonus = True

    def desenhar_mensagem_fase(self, mensagem):
        """Sem o "+1 VIDA" da vitória no chefão: nos mapas as vidas extras não valem
        e o Modo Livre nem tem vidas (o clássico continua mostrando)."""
        linhas = [linha for linha in mensagem.split('\n') if linha != texto_vidas_extras()]
        super().desenhar_mensagem_fase('\n'.join(linhas))

    def desenhar(self):
        for fase in (getattr(self, 'galaga', None), getattr(self, 'donkey', None)):
            if fase is not None:
                if fase.estilo_bonus is None:
                    fase.estilo_bonus = EstiloBonus(self.recursos)
                fase.estilo_bonus.efeitos = self.efeitos_bonus
        super().desenhar()
