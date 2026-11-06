"""Moedas durante o jogo (Modo Livre, mapas e jornada; o clássico não tem).

Onde aparecem (sempre sem mudar a dificuldade):
  * Flappy: no centro da passagem dos canos (ou dos pássaros), por onde o
    jogador já precisa passar, e acompanhando a oscilação da passagem;
  * Galaga: caem do topo, soltas e opcionais;
  * Donkey Kong: cada banana coletada vale moedas.

O coletor usa o PRÓPRIO gerador aleatório: sortear moedas não pode mexer na
sequência de canos e inimigos do jogo.
"""
import math
import random

import pygame

from ..config.constants import ALTURA, LARGURA, Y_NAVE
from ..config.economy import (
    CHANCE_MOEDA_NA_PASSAGEM,
    INTERVALO_MOEDA_GALAGA,
    MOEDAS_POR_BANANA,
    RAIO_MOEDA,
    VALOR_MOEDA,
    VELOCIDADE_MOEDA_GALAGA,
)
from ..ui.theme import Palette
from ..ui.widgets import painel, texto

QUADROS_GIRO = 8
_QUADROS = {}


def quadros_moeda(raio=RAIO_MOEDA):
    """Moeda girando: 8 quadros com a largura variando como |cos|."""
    if raio not in _QUADROS:
        quadros = []
        for i in range(QUADROS_GIRO):
            largura = max(3, round(2 * raio * abs(math.cos(i * math.pi / QUADROS_GIRO))))
            sup = pygame.Surface((2 * raio + 4, 2 * raio + 4), pygame.SRCALPHA)
            rect = pygame.Rect(0, 0, largura, 2 * raio)
            rect.center = (raio + 2, raio + 2)
            pygame.draw.ellipse(sup, Palette.INK, rect.inflate(4, 4))
            pygame.draw.ellipse(sup, Palette.COIN_SHADE, rect)
            pygame.draw.ellipse(sup, Palette.COIN, rect.inflate(-max(2, largura // 4), -6))
            if largura > 10:
                brilho = pygame.Rect(0, 0, max(2, largura // 5), raio)
                brilho.center = (rect.centerx - largura // 6, rect.centery - 2)
                pygame.draw.ellipse(sup, (255, 246, 196), brilho)
            quadros.append(sup)
        _QUADROS[raio] = quadros
    return _QUADROS[raio]


def icone_moeda(raio=11):
    return quadros_moeda(raio)[0]


def _toca(cx, cy, raio, rect):
    """Círculo encosta no retângulo?"""
    px = min(max(cx, rect.left), rect.right)
    py = min(max(cy, rect.top), rect.bottom)
    return (cx - px) ** 2 + (cy - py) ** 2 <= raio ** 2


class ColetorMoedas:
    def __init__(self, semente=None):
        self.aleatorio = random.Random(semente)
        self.coletadas = 0
        self.nas_passagens = {}     # id(obstáculo) -> True (com moeda) / False (sem)
        self.caindo = []            # [x, y] das moedas da Galaga
        self.espera_galaga = INTERVALO_MOEDA_GALAGA
        self.fase_donkey, self.bananas_vistas = None, 0
        self.avisos = []            # "+1" subindo: [x, y, idade, texto]
        self.giro = 0.0
        self.efeitos = True

    # ------------------------------------------------------------ lógica
    def atualizar(self, sessao, dt):
        self.giro += dt
        self.avisos = [[x, y - 40 * dt, t + dt, r] for x, y, t, r in self.avisos if t < (1.2 if len(r) > 3 else 0.7)]
        estado = sessao.estado
        if estado == 'JOGO':
            self._passagens(sessao)
        else:
            self.nas_passagens.clear()
        if estado == 'GALAGA' and sessao.galaga and not sessao.galaga.resultado:
            self._galaga(sessao.galaga, dt)
        else:
            self.caindo = []
        if estado == 'DONKEY' and sessao.donkey:
            self._bananas(sessao)

    def _ganhar(self, quantidade, x, y, rotulo=''):
        self.coletadas += quantidade
        self.avisos.append([x, y, 0.0, f'+{quantidade}{" " + rotulo if rotulo else ""}'])

    def ganhar_bonus(self, quantidade, x, y, rotulo):
        """Moedas que não vêm de um item (ex.: bônus de sequência do Modo Livre)."""
        self._ganhar(quantidade, x, y, rotulo)

    def _passagens(self, sessao):
        vivos = {id(o) for o in sessao.obstaculos}
        for chave in [k for k in self.nas_passagens if k not in vivos]:
            del self.nas_passagens[chave]
        rect = sessao.passaro.retangulo().inflate(-10, -8)
        for o in sessao.obstaculos:
            chave = id(o)
            if chave not in self.nas_passagens:
                self.nas_passagens[chave] = self.aleatorio.random() < CHANCE_MOEDA_NA_PASSAGEM
            if self.nas_passagens[chave]:
                x, y = self.posicao_na_passagem(o)
                if _toca(x, y, RAIO_MOEDA, rect):
                    self.nas_passagens[chave] = False
                    self._ganhar(VALOR_MOEDA, x, y)

    @staticmethod
    def posicao_na_passagem(obstaculo):
        return (obstaculo.x + obstaculo.largura / 2,
                obstaculo.topo_passagem + obstaculo.abertura / 2)

    def _galaga(self, fase, dt):
        self.espera_galaga -= dt
        if self.espera_galaga <= 0:
            self.espera_galaga = INTERVALO_MOEDA_GALAGA
            self.caindo.append([self.aleatorio.uniform(40, LARGURA - 40), -RAIO_MOEDA])
        nave = pygame.Rect(0, 0, 42, 56)
        nave.center = (fase.nave_x, Y_NAVE)
        restantes = []
        for moeda in self.caindo:
            moeda[1] += VELOCIDADE_MOEDA_GALAGA * dt
            if _toca(moeda[0], moeda[1], RAIO_MOEDA, nave):
                self._ganhar(VALOR_MOEDA, moeda[0], moeda[1])
            elif moeda[1] < ALTURA + RAIO_MOEDA:
                restantes.append(moeda)
        self.caindo = restantes

    def _bananas(self, sessao):
        fase = sessao.donkey
        if fase is not self.fase_donkey:
            self.fase_donkey, self.bananas_vistas = fase, fase.bananas_coletadas
        novas = fase.bananas_coletadas - self.bananas_vistas
        if novas > 0:
            self.bananas_vistas = fase.bananas_coletadas
            centro = sessao.passaro.retangulo().center
            self._ganhar(novas * MOEDAS_POR_BANANA, centro[0], centro[1] - 20)

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela, sessao):
        quadro = quadros_moeda()[int(self.giro * 12) % QUADROS_GIRO]
        if sessao.estado == 'JOGO':
            for o in sessao.obstaculos:
                if self.nas_passagens.get(id(o)):
                    tela.blit(quadro, quadro.get_rect(center=self.posicao_na_passagem(o)))
        for x, y in self.caindo:
            tela.blit(quadro, quadro.get_rect(center=(x, y)))
        if self.efeitos:
            for x, y, idade, rotulo in self.avisos:
                aviso = texto(rotulo, 26, Palette.COIN, Palette.INK, 2).copy()
                aviso.set_alpha(max(0, 255 - int(idade * (200 if len(rotulo) > 3 else 360))))
                tela.blit(aviso, aviso.get_rect(center=(x, y - 18)))

    def desenhar_saldo(self, tela, saldo):
        """Saldo no canto superior esquerdo, logo abaixo da pontuação."""
        rotulo = texto(str(saldo), 26, Palette.WHITE, Palette.INK, 2)
        caixa = pygame.Rect(14, 124, rotulo.get_width() + 52, 36)
        painel(tela, caixa, Palette.INK, Palette.INK, raio=18, sombra=0, brilho=False)
        tela.blit(icone_moeda(), icone_moeda().get_rect(center=(caixa.x + 20, caixa.centery)))
        tela.blit(rotulo, rotulo.get_rect(midleft=(caixa.x + 36, caixa.centery)))


class SessaoComMoedas:
    """Mixin: moedas e skin para sessões que não são o clássico original.

    Uso: class FreeSession(SessaoComMoedas, ClassicSession). A cena chama
    preparar_recompensas() logo após criar a sessão.
    """

    skin = None
    saldo_inicial = 0
    moedas_ativas = True

    def preparar_recompensas(self, skin=None, saldo=0, efeitos=True, moedas=True):
        self.skin = skin
        if skin is not None:
            skin.efeitos = efeitos
        self.saldo_inicial = saldo
        self.moedas_ativas = moedas
        self.coletor.efeitos = efeitos

    def reiniciar(self):
        super().reiniciar()
        self.coletor = ColetorMoedas()

    @property
    def moedas_coletadas(self):
        return self.coletor.coletadas

    def atualizar(self, dt, agora_ms):
        super().atualizar(dt, agora_ms)
        if self.moedas_ativas and not self.pausado and not getattr(self, 'resultado', None):
            self.coletor.atualizar(self, dt)

    def desenhar(self):
        self.passaro.skin = self.skin
        super().desenhar()
        if self.moedas_ativas and not self.pausado and self.estado in ('JOGO', 'GALAGA', 'DONKEY'):
            self.coletor.desenhar(self.tela, self)
            self.coletor.desenhar_saldo(self.tela, self.saldo_inicial + self.moedas_coletadas)
