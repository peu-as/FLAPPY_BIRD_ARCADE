"""Efeitos visuais compartilhados entre as fases."""
import pygame


class Explosao:
    """Círculo que cresce e esmaece por DURACAO segundos."""
    DURACAO = 0.4

    def __init__(self, x, y):
        self.x, self.y, self.tempo = x, y, 0.0

    def atualizar(self, dt):
        self.tempo += dt

    @property
    def ativa(self):
        return self.tempo < self.DURACAO

    def desenhar(self, tela):
        p = min(1.0, self.tempo/self.DURACAO)   # progresso de 0 a 1
        raio = int(8 + 28*p)
        cor = (255, int(220 - 160*p), 40)
        pygame.draw.circle(tela, cor, (int(self.x), int(self.y)),
                           raio, max(1, int(5*(1-p))))
