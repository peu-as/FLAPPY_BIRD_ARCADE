"""Regras de uma casa do Combina 3: objetivos, chefão e ataques (sem tela).

A sessão (sessao.py) usa esta classe para animar cada etapa; o robô
(tools/playtest_combina3.py) usa `jogar`, que faz a jogada inteira de uma vez.
As duas jogam com exatamente as mesmas regras.

    partida = Partida(cfg.casa_combina3(5), semente=1)
    onda = partida.tab.trocar(a, b)          # a troca (None = não combina)
    partida.usar_jogada()
    while onda:
        partida.aplicar(onda)                # dano no chefão, casulos quebrados
        partida.tab.cair()
        onda = partida.tab.proxima_onda()
    if not partida.cumprida():
        ataque = partida.planejar_ataque()   # o chefão ataca a cada N jogadas
        if ataque:
            partida.aplicar_ataque(ataque)   # (a tela anima entre os dois)
"""
import random
from dataclasses import dataclass

from ...config import combina3 as cfg
from .tabuleiro import TIPOS, Tabuleiro

CASULO, BARRIL = 'casulo', 'barril'
GOLPES = {CASULO: 1, BARRIL: 2}


@dataclass
class Ataque:
    casas: list               # [((l, c), CASULO | BARRIL)]
    bravo: bool = False


def dano_da_onda(onda):
    """Quanto uma onda tira da vida do chefão."""
    return len(onda.limpas) + len(onda.gelo) + len(onda.caixas) + cfg.DANO_POR_EFEITO * len(onda.efeitos)


class Partida:
    def __init__(self, casa, semente=None, linhas=cfg.LINHAS, colunas=cfg.COLUNAS):
        self.casa = casa
        pedras, caixas, gelo = casa.obstaculos()
        self.tab = Tabuleiro(linhas, colunas, tipos=TIPOS[:casa.tipos], semente=semente,
                             pedras=pedras, caixas=caixas, gelo=gelo)
        self.gelo_total = sum(gelo.values())
        self.caixas_total = sum(caixas.values())
        self.jogadas = casa.jogadas
        self.usadas = 0
        self.dano = 0
        self.casulos = set()                  # casas com casulo do Rei-Inseto (para o desenho)
        self.barris = set()                   # casas com barril do Kong
        self.ataques = 0
        self.embaralhou = False              # o último ataque obrigou a embaralhar?
        self.sorteio = random.Random(None if semente is None else semente * 7 + 3)

    # ------------------------------------------------------------ chefão
    @property
    def chefao(self):
        return self.casa.chefao

    @property
    def vida(self):
        return self.chefao.vida - self.dano if self.chefao else 0

    @property
    def bravo(self):
        return bool(self.chefao) and self.dano * 2 >= self.chefao.vida

    def jogadas_para_ataque(self):
        """Quantas jogadas faltam para o próximo ataque (None sem chefão)."""
        if not self.chefao:
            return None
        return self.chefao.a_cada - self.usadas % self.chefao.a_cada

    # ------------------------------------------------------------ objetivos
    def progresso(self):
        """[(objetivo, feito, alvo)] na ordem da casa."""
        tab = self.tab
        lista = []
        for objetivo in self.casa.objetivos:
            tipo = objetivo[0]
            if tipo == cfg.PONTOS:
                feito, alvo = tab.pontos, objetivo[1]
            elif tipo == cfg.COLETAR:
                feito, alvo = tab.contagem.get(objetivo[1], 0), objetivo[2]
            elif tipo == cfg.GELO:
                alvo = self.gelo_total
                feito = alvo - sum(map(sum, tab.gelo))
            elif tipo == cfg.CAIXAS:
                alvo = self.caixas_total
                feito = alvo - sum(map(sum, tab.caixa))
            else:
                feito, alvo = self.dano, self.chefao.vida
            lista.append((objetivo, min(feito, alvo), alvo))
        return lista

    def cumprida(self):
        return all(feito >= alvo for _, feito, alvo in self.progresso())

    def fracao(self):
        """De 0 a 1: quanto dos objetivos já foi feito (média), para o robô e a barra."""
        partes = [feito / alvo if alvo else 1.0 for _, feito, alvo in self.progresso()]
        return sum(partes) / len(partes)

    # ------------------------------------------------------------ jogada
    def usar_jogada(self):
        self.jogadas -= 1
        self.usadas += 1

    def aplicar(self, onda):
        """Aplica uma onda no tabuleiro e no chefão. Devolve o dano causado."""
        dano = 0
        if self.chefao:
            dano = min(self.vida, dano_da_onda(onda))
            self.dano += dano
        self.tab.aplicar(onda)
        for casa in onda.caixas:
            if self.tab.caixa[casa[0]][casa[1]] <= 0:
                self.casulos.discard(casa)
                self.barris.discard(casa)
        return dano

    def planejar_ataque(self):
        """Depois de uma jogada: o chefão ataca? Devolve o Ataque (sem aplicar) ou None."""
        if (not self.chefao or self.cumprida() or self.jogadas <= 0
                or self.usadas % self.chefao.a_cada != 0):
            return None
        bravo = self.bravo
        pedidos = [CASULO] * self.chefao.casulos + [BARRIL] * self.chefao.barris
        if bravo:
            pedidos.append(CASULO if self.chefao.casulos >= self.chefao.barris else BARRIL)
        ja = sum(1 for linha in self.tab.caixa for v in linha if v > 0)
        vagas = max(0, cfg.MAX_CAIXAS_DO_CHEFE - ja)
        candidatas = [casa for casa in self.tab.casas()
                      if self.tab.peca(casa) is not None and not self.tab.peca(casa).especial
                      and self.tab.gelo[casa[0]][casa[1]] == 0]
        self.sorteio.shuffle(candidatas)
        escolhidas = list(zip(sorted(candidatas[:min(vagas, len(pedidos))]), pedidos))
        return Ataque(escolhidas, bravo) if escolhidas else None

    def aplicar_ataque(self, ataque):
        """As peças atingidas viram casulos/barris (caixas). Devolve as peças que sumiram."""
        removidas = []
        for (l, c), tipo in ataque.casas:
            removidas.append(((l, c), self.tab.grade[l][c]))
            self.tab.grade[l][c] = None
            self.tab.caixa[l][c] = GOLPES[tipo]
            (self.casulos if tipo == CASULO else self.barris).add((l, c))
        self.ataques += 1
        self.embaralhou = self.tab.dica() is None
        if self.embaralhou:
            self.tab.embaralhar()
        return removidas

    def jogar(self, a, b):
        """A jogada inteira de uma vez (robô e testes). Devolve o Ataque que veio depois (ou None).
        Levanta ValueError se a troca não combina."""
        onda = self.tab.trocar(a, b)
        if onda is None:
            raise ValueError(f'troca inválida: {a} {b}')
        self.usar_jogada()
        while onda:
            self.aplicar(onda)
            self.tab.cair()
            onda = self.tab.proxima_onda()
        ataque = self.planejar_ataque()
        if ataque:
            self.aplicar_ataque(ataque)
        elif self.tab.dica() is None:
            self.tab.embaralhar()
        return ataque

    @property
    def vitoria(self):
        return self.cumprida()

    @property
    def derrota(self):
        return not self.cumprida() and self.jogadas <= 0
