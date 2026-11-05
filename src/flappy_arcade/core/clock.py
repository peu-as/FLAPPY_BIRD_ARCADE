"""Relógio do jogo.

Toda leitura de tempo da jogabilidade passa por aqui. Isso permite testar o
jogo com um relógio controlado (sempre o mesmo resultado) e, no futuro,
congelar o tempo do jogo enquanto um menu de pausa estiver aberto.
"""
import time

import pygame


class GameClock:
    """Relógio real: now() em segundos, ticks() em milissegundos."""

    def now(self):
        return time.monotonic()

    def ticks(self):
        return pygame.time.get_ticks()
