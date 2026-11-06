"""Cenários comprados: da faixa de horizonte (assets/cenarios) ao fundo de tela.

Os cenários são paisagens: a faixa fica apoiada no chão e o céu acima dela é
estendido com as cores do topo da própria faixa, como no fundo original do
Flappy (cidade embaixo, céu em cima).

  montar_retrato        faixa -> fundo de tela 575x860
  GerenciadorCenarios   monta sob demanda; no máximo 3 fundos na memória
  DiretorCenarios       fixo ou playlist aleatória (troca a cada 20 s, com transição)
  SessaoComCenarios     mixin das sessões novas (Modo Livre, mapas, jornada)
"""
import random
from collections import OrderedDict

import pygame

from ..config.constants import ALTURA, LARGURA, TEMPO_TEMA, Y_CHAO
from ..config.scenarios import ORIGINAL, POR_ID
from ..core.paths import ARTES_CENARIOS
from .flappy import Obstaculo

ALTURA_EMENDA = 90          # px de transição entre o topo da faixa e o céu liso
ESCURECER_TOPO = 0.18       # o céu escurece um pouco em direção ao alto da tela


def _cor_media(superficie, rect):
    return tuple(int(c) for c in pygame.transform.average_color(superficie, rect)[:3])


def montar_retrato(faixa):
    """Faixa de horizonte (575 x ~400) -> fundo de tela inteira (575 x 860)."""
    tela = pygame.Surface((LARGURA, ALTURA))
    y_faixa = Y_CHAO - faixa.get_height()
    cor = _cor_media(faixa, pygame.Rect(0, 0, LARGURA, 6))
    alto = tuple(int(c * (1 - ESCURECER_TOPO)) for c in cor)
    for y in range(max(0, y_faixa)):
        t = y / max(1, y_faixa)
        tela.fill(tuple(round(a + (b - a) * t) for a, b in zip(alto, cor)), (0, y, LARGURA, 1))
    # emenda: as cores do topo da faixa (suavizadas) se dissolvem no céu liso
    linha = pygame.transform.smoothscale(faixa.subsurface((0, 0, LARGURA, 2)).copy(), (24, 1))
    linha = pygame.transform.smoothscale(linha, (LARGURA, 1))
    for y in range(ALTURA_EMENDA):
        copia = linha.copy()
        copia.set_alpha(round(255 * y / ALTURA_EMENDA))
        tela.blit(copia, (0, y_faixa - ALTURA_EMENDA + y))
    tela.blit(faixa, (0, y_faixa))
    tela.fill(_cor_media(faixa, pygame.Rect(0, faixa.get_height() - 4, LARGURA, 4)),
              (0, Y_CHAO, LARGURA, ALTURA - Y_CHAO))          # atrás do chão (fica escondido)
    return tela


# ---------------------------------------------------------------- fundos prontos
LIMITE_MEMORIA = 3          # o atual, o anterior (na transição) e o próximo (pré-carregado)
QUADROS_TRANSICAO = 30      # ~1 s a 30 FPS: um cenário se dissolve no outro
TEMA_DO_PERIODO = {'dia': 'bg', 'tarde': 'bg1', 'noite': 'night'}   # cor dos canos, como no original


class GerenciadorCenarios:
    """Monta os fundos sob demanda e guarda só os últimos LIMITE_MEMORIA.

    Com 15 cenários na playlist, a memória continua a de 3 fundos (~6 MB).
    """

    def __init__(self, recursos, limite=LIMITE_MEMORIA):
        self.recursos = recursos
        self.limite = limite
        self._prontos = OrderedDict()
        self.montagens = 0           # quantas vezes um fundo foi montado (testes)

    def fundo(self, cenario_id):
        if cenario_id in self._prontos:
            self._prontos.move_to_end(cenario_id)
            return self._prontos[cenario_id]
        superficie = self._montar(POR_ID[cenario_id])
        self.montagens += 1
        self._prontos[cenario_id] = superficie
        while len(self._prontos) > self.limite:
            self._prontos.popitem(last=False)
        return superficie

    @property
    def em_memoria(self):
        return list(self._prontos)

    def _montar(self, cenario):
        if cenario.tipo == ORIGINAL:
            return pygame.transform.scale(self.recursos.fundos[cenario.id], (LARGURA, ALTURA)).convert()
        faixa = pygame.image.load(str(ARTES_CENARIOS / cenario.arquivo)).convert()
        return montar_retrato(faixa).convert()


class DiretorCenarios:
    """Decide o cenário da partida: um fixo, ou a playlist em ordem sorteada.

    No aleatório, troca a cada `periodo` segundos de jogo (os mesmos 20 s do
    original), nunca repete o que acabou de passar e já deixa o próximo
    montado. Usa o próprio sorteador: o `random` do jogo decide os canos.
    """

    def __init__(self, ids, gerenciador, periodo=TEMPO_TEMA, semente=None):
        self.ids = [c for c in dict.fromkeys(ids) if c in POR_ID] or ['bg']
        self.gerenciador = gerenciador
        self.periodo = periodo
        self.sorteio = random.Random(semente)
        self.atual = self.sorteio.choice(self.ids)
        self.proximo = self._sortear_proximo()
        self.anterior = None
        self.transicao = 0           # quadros que faltam da transição
        self.indice = 0
        self.trocas = 0

    @property
    def cenario(self):
        return POR_ID[self.atual]

    def _sortear_proximo(self):
        opcoes = [c for c in self.ids if c != self.atual] or self.ids
        proximo = self.sorteio.choice(opcoes)
        self.gerenciador.fundo(proximo)          # pré-carrega: a troca não engasga
        return proximo

    def atualizar(self, tempo):
        indice = int(tempo // self.periodo)
        if indice == self.indice:
            return False
        self.indice = indice
        if len(self.ids) == 1:
            return False
        self.anterior, self.atual = self.atual, self.proximo
        self.gerenciador.fundo(self.atual)       # o que entra é o mais recente: não sai da memória
        self.proximo = self._sortear_proximo()
        self.transicao = QUADROS_TRANSICAO
        self.trocas += 1
        return True

    def desenhar(self, tela, efeitos=True):
        fundo = self.gerenciador.fundo(self.atual)
        if self.transicao and self.anterior and efeitos:
            tela.blit(self.gerenciador.fundo(self.anterior), (0, 0))
            fundo.set_alpha(round(255 * (1 - self.transicao / QUADROS_TRANSICAO)))
            tela.blit(fundo, (0, 0))
            fundo.set_alpha(None)
            self.transicao -= 1
        else:
            self.transicao = 0
            tela.blit(fundo, (0, 0))


class SessaoComCenarios:
    """Mixin: os cenários do jogador no lugar do ciclo de fundos do original.

    Uso: class FreeSession(SessaoComCenarios, SessaoComMoedas, ClassicSession).
    Só muda o desenho e a cor dos canos e do pássaro (pelo período); a física,
    o tempo e os sorteios dos canos continuam os do original. Sem diretor
    (preparar_cenarios não chamado), tudo fica exatamente como no clássico.
    """

    diretor = None
    efeitos_cenario = True

    def preparar_cenarios(self, diretor, efeitos=True):
        self.diretor = diretor
        self.efeitos_cenario = efeitos
        self._aplicar_cenario()
        for obstaculo in self.obstaculos:        # canos que já estavam na tela
            if type(obstaculo) is Obstaculo and not obstaculo.especial:
                obstaculo.cima, obstaculo.baixo = obstaculo.criar_sprites(self.recursos, False, self.tema)

    def _aplicar_cenario(self):
        cenario = self.diretor.cenario
        self.tema = cenario.id if cenario.tipo == ORIGINAL else TEMA_DO_PERIODO[cenario.periodo]
        self.passaro.familia = cenario.periodo

    def reiniciar(self):
        super().reiniciar()
        if self.diretor is not None:
            self._aplicar_cenario()

    def tema_por_tempo(self):
        if self.diretor is None:
            return super().tema_por_tempo()
        self.diretor.atualizar(self.tempo_ativo)
        self._aplicar_cenario()

    def rotulo_tema(self):
        return super().rotulo_tema() if self.diretor is None else self.diretor.cenario.nome

    def desenhar_fundo(self):
        if self.diretor is None:
            return super().desenhar_fundo()
        self.diretor.desenhar(self.tela, self.efeitos_cenario)
