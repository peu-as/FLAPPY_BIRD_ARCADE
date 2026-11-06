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

from ..config.constants import ALTURA, LARGURA, TEMPO_TEMA, Y_CHAO, Y_NAVE
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
        self._variantes = OrderedDict()   # versões Galaga/Donkey: só as da fase da vez
        self._miniaturas = {}             # cartões da loja e dos Equipamentos (pequenas)
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

    def miniatura(self, cenario_id, tamanho):
        """Recorte do horizonte em tamanho de cartão. Não ocupa o lugar dos fundos grandes."""
        chave = (cenario_id, tamanho)
        if chave not in self._miniaturas:
            retrato = self._prontos.get(cenario_id) or self._montar(POR_ID[cenario_id])
            altura = min(Y_CHAO - 80, round(LARGURA * tamanho[1] / tamanho[0]))
            corte = pygame.Rect(0, Y_CHAO - 40 - altura, LARGURA, altura)
            self._miniaturas[chave] = pygame.transform.smoothscale(retrato.subsurface(corte), tamanho)
        return self._miniaturas[chave]

    def tem_miniatura(self, cenario_id, tamanho):
        return (cenario_id, tamanho) in self._miniaturas

    def variante(self, cenario_id, tipo):
        """'galaga', 'galaga_chefe' ou 'donkey', montada uma vez por fase."""
        chave = (cenario_id, tipo)
        if chave not in self._variantes:
            retrato = self.fundo(cenario_id)
            r = self.recursos
            self._variantes[chave] = (visual_donkey(retrato, r.banana) if tipo == 'donkey'
                                      else visual_galaga(retrato, r.nave, chefe=tipo == 'galaga_chefe'))
            while len(self._variantes) > 2:          # galaga + galaga_chefe, ou donkey
                self._variantes.popitem(last=False)
        else:
            self._variantes.move_to_end(chave)
        return self._variantes[chave]

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
    Só muda o desenho (fundo do Flappy e, adaptado, o da Galaga e do Donkey) e a
    cor dos canos e do pássaro (pelo período); a física,
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

    def desenhar(self):
        if self.diretor is not None and self.estado == 'ALERTA' and self.variante_alerta:
            # prepara a versão da fase durante o alerta de 5 s: a entrada não engasga
            tipo = 'galaga' if self.variante_alerta == 'GALAGA' else 'donkey'
            self.diretor.gerenciador.variante(self.diretor.atual, tipo)
        if self.diretor is not None:              # fases bônus: o cenário da vez, adaptado
            for fase in (getattr(self, 'galaga', None), getattr(self, 'donkey', None)):
                if fase is not None and fase.cenario is None:
                    fase.cenario = CenarioNaFase(self.diretor.gerenciador, self.diretor.atual)
        super().desenhar()


# ---------------------------------------------------------------- Galaga e Donkey
COR_ESPACO = (6, 6, 28)               # o fundo original da Galaga
GALAGA_INICIO_HORIZONTE = 380         # acima disso é só espaço (onde a formação voa)
GALAGA_FIM_DEGRADE = 640              # daqui para baixo o horizonte aparece inteiro
GALAGA_COR_NOITE = (14, 18, 60)
GALAGA_ESCURECER_MINIMO = 0.50        # quanto o horizonte puxa, no mínimo, para o azul do espaço
GALAGA_A_MAIS_NO_CHEFE = 0.24         # no chefão o mundo lá embaixo fica mais longe
DONKEY_TINTA = (10, 40, 44)           # selva à noite: puxa tudo para o verde-escuro
DONKEY_TINGIR_MINIMO = 0.58
DONKEY_PARALLAX = 0.05                # o cenário anda mais devagar que as palmeiras (0,15 e 0,35)
ESCURECER_MAXIMO = 0.90
PASSO_ESCURECER = 0.04
SEGUNDOS_ESCURECER_CHEFE = 1.0

# Leitura: o que o jogador precisa ver deve ter contraste de pelo menos 3:1
# (o mínimo das diretrizes de acessibilidade para elementos gráficos) com o
# fundo logo atrás dele. Cenário claro escurece mais; escuro fica como está.
CONTRASTE_MINIMO = 3.0
FAIXA_NAVE = pygame.Rect(0, Y_NAVE - 40, LARGURA, 80)       # por onde a nave anda
AREA_DONKEY = pygame.Rect(0, 120, LARGURA, Y_CHAO - 120)    # onde passam barris, bananas e o pássaro


def luminancia(cor):
    """Luminância relativa (0 = preto, 1 = branco), como nas diretrizes de acessibilidade."""
    canais = []
    for c in cor[:3]:
        c /= 255
        canais.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]


def luminancia_media(superficie, rect=None):
    return luminancia(pygame.transform.average_color(superficie, rect or superficie.get_rect()))


def luminancia_sprite(sprite):
    """Luminância média só dos pixels visíveis do sprite."""
    mascara = pygame.mask.from_surface(sprite)
    soma = [0, 0, 0]
    for x, y in ((x, y) for x in range(sprite.get_width()) for y in range(sprite.get_height())
                 if mascara.get_at((x, y))):
        cor = sprite.get_at((x, y))
        for i in range(3):
            soma[i] += cor[i]
    total = max(1, mascara.count())
    return luminancia([v / total for v in soma])


def contraste(l1, l2):
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _misturar(superficie, cor, quanto):
    """Puxa a superfície para `cor` (0 = nada, 1 = só a cor)."""
    camada = pygame.Surface(superficie.get_size())
    camada.fill(cor)
    camada.set_alpha(round(255 * quanto))
    resultado = superficie.copy()
    resultado.blit(camada, (0, 0))
    return resultado


def _escurecer_ate_ler(superficie, cor, minimo, rect, alvo):
    """Mistura com `cor` a partir de `minimo`, aumentando até a luminância em
    `rect` ficar <= `alvo` (ou chegar a ESCURECER_MAXIMO)."""
    quanto = minimo
    while True:
        resultado = _misturar(superficie, cor, quanto)
        if luminancia_media(resultado, rect) <= alvo or quanto >= ESCURECER_MAXIMO:
            return resultado, quanto
        quanto = min(ESCURECER_MAXIMO, quanto + PASSO_ESCURECER)


def _alvo(luminancia_do_que_precisa_aparecer):
    """Luminância máxima do fundo para o contraste ficar >= CONTRASTE_MINIMO."""
    return (luminancia_do_que_precisa_aparecer + 0.05) / CONTRASTE_MINIMO - 0.05


def visual_galaga(retrato, nave, chefe=False):
    """Decolagem: o seu mundo fica lá embaixo e se dissolve no espaço."""
    mundo = pygame.Surface((LARGURA, ALTURA))
    mundo.blit(retrato, (0, ALTURA - Y_CHAO))            # o horizonte desce até a borda de baixo
    mundo, quanto = _escurecer_ate_ler(mundo, GALAGA_COR_NOITE, GALAGA_ESCURECER_MINIMO,
                                       FAIXA_NAVE, _alvo(luminancia_sprite(nave)))
    if chefe:
        mundo = _misturar(mundo, GALAGA_COR_NOITE, GALAGA_A_MAIS_NO_CHEFE)
    tela = pygame.Surface((LARGURA, ALTURA))
    tela.fill(COR_ESPACO)
    altura = GALAGA_FIM_DEGRADE - GALAGA_INICIO_HORIZONTE
    for y in range(GALAGA_INICIO_HORIZONTE, ALTURA):
        linha = mundo.subsurface((0, y, LARGURA, 1))
        linha.set_alpha(min(255, round(255 * ((y - GALAGA_INICIO_HORIZONTE) / altura) ** 1.6)))
        tela.blit(linha, (0, y))
    return tela


def visual_donkey(retrato, banana):
    """Selva sobre o seu mundo: o cenário no lugar do céu, tingido de selva à noite.
    Volta espelhado (largura dupla) para rolar sem emenda."""
    tingido, _ = _escurecer_ate_ler(retrato, DONKEY_TINTA, DONKEY_TINGIR_MINIMO,
                                    AREA_DONKEY, _alvo(luminancia_sprite(banana)))
    faixa = pygame.Surface((LARGURA * 2, ALTURA))
    faixa.blit(tingido, (0, 0))
    faixa.blit(pygame.transform.flip(tingido, True, False), (LARGURA, 0))
    return faixa


class CenarioNaFase:
    """O cenário da partida dentro das fases bônus (entregue pela sessão)."""

    def __init__(self, gerenciador, cenario_id):
        self.gerenciador = gerenciador
        self.id = cenario_id

    def desenhar_galaga(self, tela, chefe=False, tempo_chefe=0.0):
        tela.blit(self.gerenciador.variante(self.id, 'galaga'), (0, 0))
        if chefe:
            escuro = self.gerenciador.variante(self.id, 'galaga_chefe')
            escuro.set_alpha(round(255 * min(1.0, tempo_chefe / SEGUNDOS_ESCURECER_CHEFE)))
            tela.blit(escuro, (0, 0))
            escuro.set_alpha(None)

    def desenhar_donkey(self, tela, rolagem):
        faixa = self.gerenciador.variante(self.id, 'donkey')
        x = -int(rolagem * DONKEY_PARALLAX) % faixa.get_width()
        tela.blit(faixa, (x - faixa.get_width(), 0))
        tela.blit(faixa, (x, 0))
