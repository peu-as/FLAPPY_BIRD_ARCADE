"""Cenários determinísticos do golden master.

Os mesmos cenários rodam no jogo original (gravação) e na nova arquitetura
(teste). Cada cenário controla a sessão só pela API que as duas versões
compartilham: eventos de teclado, atualizar(), desenhar() e alguns métodos
de alto nível (iniciar_alerta, ir_para_nivel...).
"""
import random

import pygame

from snapshot import hash_estado, hash_pixels

DT = 1 / 30
PIXELS_A_CADA = 10
ESTADO_A_CADA = 50


class FakeClock:
    """Relógio controlado: avança exatamente 1/30 s por quadro."""

    def __init__(self):
        self.quadro = 0

    def avancar(self):
        self.quadro += 1

    def now(self):
        return 1000.0 + self.quadro / 30

    def ticks(self):
        return round(self.quadro * 1000 / 30)


def tecla(sessao, key, unicode=''):
    return sessao.tratar_evento(pygame.event.Event(
        pygame.KEYDOWN, key=key, unicode=unicode, mod=0, scancode=0))


class Gravador:
    """Avança a sessão quadro a quadro e acumula os hashes."""

    def __init__(self, sessao, clock, pos_atualizar):
        self.s, self.clock, self.pos_atualizar = sessao, clock, pos_atualizar
        self.frame = 0
        self.estados, self.pixels = {}, {}

    def passo(self, n=1, antes=None):
        for _ in range(n):
            if antes:
                antes(self.frame)
            self.clock.avancar()
            self.s.atualizar(DT, self.clock.ticks())
            self.pos_atualizar(self.s)
            self.s.desenhar()
            self.frame += 1
            h = hash_estado(self.s)
            if self.frame % ESTADO_A_CADA == 0:
                self.estados[self.frame] = h
            self.ultimo_estado = h
            if self.frame % PIXELS_A_CADA == 0:
                self.pixels[self.frame] = hash_pixels(self.s.tela)

    def resultado(self):
        return {'frames': self.frame, 'final': self.ultimo_estado,
                'estado_final_nome': self.s.estado,
                'estados': {str(k): v for k, v in self.estados.items()},
                'pixels': {str(k): v for k, v in self.pixels.items()}}


def _entrar_no_jogo(s, g):
    g.passo(10)
    tecla(s, pygame.K_SPACE)                 # MENU -> CADASTRO
    for ch in 'QA1':
        tecla(s, getattr(pygame, 'K_' + ch.lower()), ch)
    tecla(s, pygame.K_BACKSPACE)
    tecla(s, pygame.K_RETURN)                # CADASTRO -> JOGO
    g.passo(5)


def _bot_classico(s):
    """Bate asas se estiver abaixo do centro da próxima passagem."""
    if s.estado != 'JOGO' or not s.obstaculos:
        return
    alvo = next((o for o in s.obstaculos if o.x + o.largura > s.passaro.x), None)
    if alvo and s.passaro.y + 12 > alvo.topo_passagem + alvo.abertura / 2 and s.passaro.vy >= 0:
        tecla(s, pygame.K_SPACE)


def cenario_partida(s, g):
    """Cadastro, partida com bot imperfeito, pausa e mortes."""
    _entrar_no_jogo(s, g)

    def entrada(f):
        if f in (300, 330):
            tecla(s, pygame.K_p)
        elif f % 14 == 0:
            tecla(s, pygame.K_SPACE)
    g.passo(1200, entrada)


def cenario_ciclo_natural(s, g):
    """Pontuação chega a 35: alerta e fase especial pelo caminho normal."""
    _entrar_no_jogo(s, g)
    s.vidas = 99
    s.pontos = 33

    def entrada(f):
        if s.estado == 'JOGO':
            _bot_classico(s)
        elif s.estado == 'DONKEY' and f % 11 == 0:
            tecla(s, pygame.K_SPACE)
        elif s.estado == 'GALAGA' and f % 5 == 0:
            tecla(s, pygame.K_SPACE)
    g.passo(2400, entrada)


def cenario_galaga(s, g):
    _entrar_no_jogo(s, g)
    s.vidas = 99
    s.ir_para_nivel(6)
    s.iniciar_alerta('GALAGA')

    def entrada(f):
        if s.estado == 'GALAGA' and s.galaga:
            vivos = [i for i in getattr(s.galaga, 'inimigos', []) if hasattr(i, 'x')]
            if vivos:
                s.galaga.alvo_x = vivos[f // 40 % len(vivos)].x
            if f % 5 == 0:
                tecla(s, pygame.K_SPACE)
    g.passo(1500, entrada)
    if s.estado == 'GALAGA':
        s.pular_para_chefe()
    g.passo(600, entrada)


def cenario_donkey(s, g):
    _entrar_no_jogo(s, g)
    s.vidas = 99
    s.ir_para_nivel(4)
    s.iniciar_alerta('DONKEY')

    def entrada(f):
        if s.estado != 'DONKEY':
            return
        if f % 90 == 0:
            tecla(s, pygame.K_x)
        elif f % 11 == 0:
            tecla(s, pygame.K_SPACE)
    g.passo(1500, entrada)
    if s.estado == 'DONKEY':
        s.pular_para_chefe()
    g.passo(600, entrada)


def cenario_fim_de_jogo(s, g):
    """Fase dos pássaros, game over por queda, volta ao menu e vitória."""
    _entrar_no_jogo(s, g)
    s.iniciar_alerta('PASSAROS')
    g.passo(400, lambda f: f % 13 == 0 and tecla(s, pygame.K_SPACE))
    s.vidas = 1
    g.passo(400)                              # sem bater asas: cai e perde
    g.passo(120)                              # GAMEOVER -> MENU pelo temporizador
    _entrar_no_jogo(s, g)
    s.vitoria_final()
    g.passo(200)


CENARIOS = {
    'partida': (7, cenario_partida),
    'ciclo_natural': (11, cenario_ciclo_natural),
    'galaga': (3, cenario_galaga),
    'donkey': (5, cenario_donkey),
    'fim_de_jogo': (9, cenario_fim_de_jogo),
}


def rodar(nome, criar_sessao, pos_atualizar):
    """criar_sessao(clock) -> sessão; deve ser chamada após random.seed."""
    seed, func = CENARIOS[nome]
    random.seed(seed)
    clock = FakeClock()
    sessao = criar_sessao(clock)
    g = Gravador(sessao, clock, pos_atualizar)
    func(sessao, g)
    return g.resultado()
