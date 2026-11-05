"""Sistema de power-ups compartilhado pela Galaga e pelo Donkey Kong."""
import math

import pygame

from ..config.constants import ALTURA, TIPOS_BONUS


# As fases (FaseGalaga e FaseDonkey) continuam falando com a sessão só por sons, dano,
# vidas_ganhas e terminou; os bônus vivem DENTRO delas. Esta seção reúne as peças comuns:
# EfeitosAtivos (timers), CapsulaBonus (o item coletável) e o HUD dos bônus ativos.

class EfeitosAtivos:
    """Timers dos bônus temporizados: nome -> segundos restantes."""
    def __init__(self):
        self.tempo = {}

    def ativar(self, nome, duracao):
        self.tempo[nome] = duracao

    def ativo(self, nome):
        return self.tempo.get(nome, 0) > 0

    def atualizar(self, dt):
        """Avança os timers e devolve os nomes dos efeitos que ACABARAM neste quadro
        (a Galaga usa isso para ligar o superaquecimento depois do Turbo)."""
        acabaram = []
        for nome in list(self.tempo):
            self.tempo[nome] -= dt
            if self.tempo[nome] <= 0:
                del self.tempo[nome]
                acabaram.append(nome)
        return acabaram

    def limpar(self):
        self.tempo.clear()

class CapsulaBonus:
    """Cápsula coletável (círculo colorido com uma letra), desenhada por código.

    Na Galaga cai devagar (vy > 0); no Donkey acompanha a rolagem (vx < 0). As
    velocidades são em px/s, como na fase Galaga."""
    RAIO = 17
    fonte = None            # criada na primeira vez que é desenhada

    def __init__(self, tipo, x, y, vx=0.0, vy=0.0):
        self.tipo = tipo
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy

    def atualizar(self, dt):
        self.x += self.vx*dt
        self.y += self.vy*dt

    def retangulo(self):
        return pygame.Rect(int(self.x - self.RAIO), int(self.y - self.RAIO),
                           2*self.RAIO, 2*self.RAIO)

    def fora_da_tela(self):
        return self.y > ALTURA + 30 or self.x < -40

    def desenhar(self, tela, tempo):
        cor, letra, _ = TIPOS_BONUS[self.tipo]
        if CapsulaBonus.fonte is None:
            CapsulaBonus.fonte = pygame.font.Font(None, 26)
        centro = (int(self.x), int(self.y + 3*math.sin(tempo*6)))      # flutua um pouco
        pygame.draw.circle(tela, cor, centro, self.RAIO + 4 + int(2*math.sin(tempo*9)), 2)  # halo pulsante
        pygame.draw.circle(tela, cor, centro, self.RAIO)
        pygame.draw.circle(tela, (255, 255, 255), centro, self.RAIO, 2)
        letra_img = CapsulaBonus.fonte.render(letra, True, (20, 20, 40))
        tela.blit(letra_img, letra_img.get_rect(center=centro))
