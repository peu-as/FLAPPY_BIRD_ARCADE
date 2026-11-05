"""Objetos do modo clássico: pássaro, canos e chão."""
import math
import random

import pygame

from ..config.constants import (
    ABERTURA_CANOS,
    COMPENSACAO_IMPULSO,
    GRAVIDADE,
    IMPULSO,
    LARGURA,
    PASSAROS_ESPECIAIS,
    USAR_MASCARAS,
    VELOCIDADE_CANOS,
    VELOCIDADE_CHAO,
    Y_CHAO,
)


# Atributos guardam o estado do objeto; métodos definem ações.
# self identifica a instância que está executando o método.
class Passaro:
    """Representa o jogador: posição, velocidade e animação."""

    # Skin (só aparência): None desenha o pássaro original. A colisão usa sempre
    # o sprite original (retangulo/máscara), com ou sem skin.
    skin = None

    def __init__(self, recursos):
        self.recursos = recursos
        self.x, self.y, self.vy = 200.0, 350.0, 0.0
        self.indice, self.contador = 0, 0
        self.familia = 'dia'
        # Gravidade e impulso viram ATRIBUTOS: o modo clássico os
        # ajusta a cada nível (aplicar_dificuldade); as fases especiais usam
        # os valores base, por isso não herdam a dificuldade do modo clássico.
        self.gravidade = GRAVIDADE
        self.impulso = IMPULSO

    def aplicar_dificuldade(self, gravidade):
        """Define a gravidade do nível atual e compensa o impulso.

        A altura de um bater de asas é v²/(2g). Se só a gravidade subisse, o
        pássaro subiria cada vez menos a cada toque. Por isso o impulso cresce
        na proporção (g/g0)**COMPENSACAO_IMPULSO: compensação parcial, que
        deixa o jogo mais difícil sem torná-lo injusto.
        """
        self.gravidade = gravidade
        self.impulso = IMPULSO*(gravidade/GRAVIDADE)**COMPENSACAO_IMPULSO

    def pular(self):
        """Aplica impulso vertical quando há clique ou barra de espaço."""
        self.vy = self.impulso      # antes: IMPULSO (constante)

    def atualizar(self):
        # Integração discreta: primeiro velocidade, depois posição.
        # A cada quadro: vy <- vy + gravidade; y <- y + vy.
        # min(..., 16) limita a velocidade de queda.
        self.vy = min(self.vy + self.gravidade, 16)   # antes: GRAVIDADE
        self.y += self.vy
        self.contador += 1
        if self.contador >= 5:
            self.contador = 0
            self.indice = (self.indice + 1) % 3

    @property
    def sprite(self):
        """Seleciona o quadro atual; acesso como atributo: self.sprite.

        @property permite consultar o método sem escrever self.sprite().
        """
        return self.recursos.passaros[self.familia][self.indice]

    def retangulo(self):
        return self.sprite.get_rect(topleft=(int(self.x), int(self.y)))

    def desenhar(self, tela):
        # A rotação é visual; o retângulo/máscara usa sprite sem giro.
        angulo = max(-75, min(25, -self.vy*5))
        if self.skin is not None:
            self.skin.desenhar(tela, self, angulo)
            return
        rot = pygame.transform.rotate(self.sprite, angulo)
        tela.blit(rot, rot.get_rect(center=self.retangulo().center))

class Obstaculo:
    """Representa um par de canos ou de pássaros da fase especial.

    Velocidade e abertura são atributos (com os valores
    originais como padrão) e os sprites são montados em criar_sprites().
    Assim, uma subclasse (ObstaculoSelva, na fase Donkey Kong) pode mudar
    a aparência e a dinâmica sem copiar o resto da classe.
    """
    def __init__(self, x, recursos, especial=False, tema='bg',
                 velocidade=VELOCIDADE_CANOS, abertura=ABERTURA_CANOS, oscilacao=0.0, topo=None):
        self.x = float(x)
        # 'topo' vem de sortear_topo_passagem (limita a distância até a passagem
        # anterior); sem ele, sorteia livremente como antes.
        self.topo_passagem = topo if topo is not None else random.randint(150, 400)
        self.passou = False
        self.especial = especial
        # Oscilação (fase dos pássaros nos níveis altos): a passagem inteira
        # sobe e desce até `oscilacao` px em torno da posição base, SEM mudar o
        # tamanho da abertura (os dois pássaros se movem juntos).
        self.topo_base = float(self.topo_passagem)
        self.oscilacao = oscilacao
        self.fase_osc = random.uniform(0, 2*math.pi)
        self.tempo_osc = 0
        self.velocidade = velocidade      # px/quadro de rolagem
        self.abertura = abertura          # passagem vertical em px
        self.cima, self.baixo = self.criar_sprites(recursos, especial, tema)
        self.largura = max(self.cima.get_width(), self.baixo.get_width())

    def criar_sprites(self, recursos, especial, tema):
        """Devolve (sprite_de_cima, sprite_de_baixo). É o ponto que
        as subclasses sobrescrevem para trocar o visual do obstáculo."""
        if especial:
            nomes = random.sample(PASSAROS_ESPECIAIS, 2)
            # Os dois usam o sprite original, virados para cima (o de cima fica "pendurado" acima da passagem).
            cima = recursos.especiais[nomes[0]]
            baixo = recursos.especiais[nomes[1]]
        else:
            baixo = (recursos.cano_dia if tema != 'night' and tema != 'bg5'
                     else recursos.cano_noite)
            cima = pygame.transform.flip(baixo, False, True)
        return cima, baixo

    def atualizar(self):
        self.x -= self.velocidade   # era VELOCIDADE_CANOS fixo
        if self.oscilacao:
            # Movimento senoidal: período de ~3 s (0,07 rad/quadro a 30 FPS).
            self.tempo_osc += 1
            self.topo_passagem = (self.topo_base
                                  + self.oscilacao*math.sin(self.fase_osc + self.tempo_osc*0.07))

    def retangulos(self):
        x = int(self.x)
        topo = self.cima.get_rect(bottomleft=(x, self.topo_passagem))
        base = self.baixo.get_rect(topleft=(x, self.topo_passagem+self.abertura))   # usa self.abertura
        return topo, base

    def desenhar(self, tela):
        a,b = self.retangulos()
        tela.blit(self.cima, a)
        tela.blit(self.baixo, b)

    def colide(self, passaro):
        """Verifica colisão usando retângulos e, opcionalmente, máscaras.

        Retângulos fazem o teste rápido; máscaras refinam pixel a pixel.
        """
        ret_p = passaro.retangulo()
        # A máscara distingue pixels opacos dos transparentes no PNG.
        mascara_p = pygame.mask.from_surface(passaro.sprite) if USAR_MASCARAS else None
        for sprite,ret in zip((self.cima,self.baixo),self.retangulos()):
            if not ret_p.colliderect(ret):
                continue
            if not USAR_MASCARAS:
                return True
            mascara = pygame.mask.from_surface(sprite)
            desloc = (ret.x-ret_p.x,ret.y-ret_p.y)
            if mascara_p.overlap(mascara, desloc) is not None:
                return True
        return False

class Chao:
    """Desenha uma faixa de chão repetida para simular movimento."""
    def __init__(self, sprite):
        self.sprite = sprite
        self.x = 0
        self.y = Y_CHAO   # era ALTURA - 100; agora vem da constante compartilhada

    def atualizar(self, velocidade=VELOCIDADE_CHAO):
        # A velocidade do chão acompanha a do nível.
        self.x = (self.x-velocidade) % self.sprite.get_width()

    def desenhar(self, tela):
        # A imagem é repetida sem deixar lacunas no eixo horizontal.
        x = int(self.x)-self.sprite.get_width()
        while x < LARGURA:
            tela.blit(self.sprite,(x,self.y))
            x += self.sprite.get_width()
