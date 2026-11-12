"""Skin lendária: um personagem com poses e efeitos dourados. Só aparência.

Usada por SkinVisual quando a skin é do tipo 'personagem' (config/skins.py).
Nada aqui muda o Passaro: ele continua colidindo com o sprite original, e
este módulo só LÊ a posição e a velocidade dele para escolher a pose.

Poses (assets/personagens/<id>/, geradas por tools/importar_personagem.py):
  pular    logo depois de bater asas (subindo rápido)
  correr   planando
  desviar  mergulhando (caindo rápido)
  morrer   deitado, quando chega ao chão
  retrato  o rosto, nos cartões da loja e no Estilingue
Na vitrine da loja as poses se revezam (idle, correr, pular, atacar, vitória...).

Efeitos 'lendario' (somem com os efeitos visuais desligados):
  aura dourada pulsando atrás do corpo (mistura aditiva: brilha sem escurecer o cenário);
  rastro de silhuetas douradas que ficam para trás como o cenário;
  faíscas em forma de estrela saindo das costas, com um pouco de gravidade;
  explosão de faíscas e uma onda dourada a cada bater de asas;
  reflexo: uma faixa de luz atravessa o personagem a cada 2 segundos.
Os sorteios usam um random.Random próprio: o random do jogo (canos, golden master)
nunca é tocado.
"""
import math
from collections import deque

import pygame

from ..config.constants import Y_CHAO

OURO = (255, 196, 40)
OURO_CLARO = (255, 236, 140)
BRANCO_QUENTE = (255, 252, 230)

DESLIZE = 5                  # px por quadro: rastro e faíscas ficam para trás como o cenário
FATOR_GIRO = 0.3             # uma pessoa inclinada a 75 graus fica estranha: gira só 30% do pássaro
VY_PULO = -3                 # mais rápido que isso subindo: pose de pulo
VY_MERGULHO = 8              # mais rápido que isso caindo: pose de mergulho
POSES_VITRINE = ('idle', 'correr', 'pular', 'desviar', 'atacar', 'vitoria', 'tomba')
QUADROS_POR_POSE_VITRINE = 26
RAIOS_AURA = (40, 42, 44, 46, 48, 50)
PERIODO_REFLEXO = 60         # quadros (2 s a 30 FPS)
DURACAO_REFLEXO = 12
MAX_FAISCAS = 70


def escolher_pose(vy, no_chao):
    """Pose do voo a partir da velocidade vertical (px/quadro; negativo = subindo)."""
    if no_chao:
        return 'morrer'
    if vy < VY_PULO:
        return 'pular'
    if vy > VY_MERGULHO:
        return 'desviar'
    return 'correr'


def _aura(raio, intensidade):
    """Brilho radial SEM canal alfa, para somar (BLEND_RGB_ADD): o preto não soma nada."""
    lado = raio * 2 + 2
    aura = pygame.Surface((lado, lado))
    aura.fill((0, 0, 0))
    for r in range(raio, 0, -2):
        forca = intensidade * (1 - r / raio) ** 1.6
        cor = tuple(min(255, round(c * forca)) for c in OURO)
        pygame.draw.circle(aura, cor, (raio + 1, raio + 1), r)
    return aura


class Lendaria:
    """Desenha o personagem e os efeitos. Uma instância por SkinVisual."""

    def __init__(self, poses, aleatorio):
        self.poses = poses
        self.aleatorio = aleatorio
        self.quadro = 0
        self.pose_atual = 'idle'
        self.rastro = deque(maxlen=6)        # [x, y, silhueta]
        self.faiscas = []                    # [x, y, vx, vy, idade, vida, tamanho]
        self.ondas = []                      # [x, y, idade]
        self._vy_anterior = 0.0
        self._cache = {}
        self._auras = [_aura(r, 0.30 + 0.05 * i) for i, r in enumerate(RAIOS_AURA)]

    # ------------------------------------------------------------ sprites
    def _sprite(self, tipo, pose, giro):
        """Pose girada, silhueta dourada ou máscara branca (guardadas: giro é inteiro)."""
        chave = (tipo, pose, giro)
        if chave not in self._cache:
            if tipo == 'pose':
                imagem = pygame.transform.rotate(self.poses[pose], giro) if giro else self.poses[pose]
            else:
                mascara = pygame.mask.from_surface(self._sprite('pose', pose, giro))
                cor = (*OURO, 255) if tipo == 'silhueta' else (255, 255, 255, 255)
                imagem = mascara.to_surface(setcolor=cor, unsetcolor=(0, 0, 0, 0))
            self._cache[chave] = imagem
        return self._cache[chave]

    def escolher(self, passaro, vitrine):
        if vitrine:
            return POSES_VITRINE[(self.quadro // QUADROS_POR_POSE_VITRINE) % len(POSES_VITRINE)]
        return escolher_pose(passaro.vy, passaro.retangulo().bottom >= Y_CHAO - 2)

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela, passaro, angulo, efeitos, vitrine=False):
        self.quadro += 1
        pose = self.escolher(passaro, vitrine)
        trocou = pose != self.pose_atual
        self.pose_atual = pose
        giro = 0 if pose == 'morrer' else round(angulo * FATOR_GIRO)
        sprite = self._sprite('pose', pose, giro)
        corpo = passaro.retangulo()
        if pose == 'morrer':                       # deitado no chão, não flutuando
            destino = sprite.get_rect(midbottom=(corpo.centerx, corpo.bottom))
        else:
            destino = sprite.get_rect(center=corpo.center)

        if efeitos:
            bateu_asas = passaro.vy <= -4 and self._vy_anterior > passaro.vy + 3
            if bateu_asas or (vitrine and trocou and pose == 'pular'):
                self._explosao(destino.center)
            self._desenhar_aura(tela, destino.center, pose)
            self._desenhar_rastro(tela)
            if pose != 'morrer':
                self._emitir(destino, pose)
            self._desenhar_ondas(tela)
            self._desenhar_faiscas(tela)
        else:
            self.rastro.clear()
            self.faiscas.clear()
            self.ondas.clear()
        self._vy_anterior = passaro.vy

        tela.blit(sprite, destino)
        if efeitos:
            self._reflexo(tela, pose, giro, destino)
            self.rastro.appendleft([destino.centerx, destino.centery, self._sprite('silhueta', pose, giro)])

    # ------------------------------------------------------------ efeitos
    def _desenhar_aura(self, tela, centro, pose):
        fase = (math.sin(self.quadro * 0.16) + 1) / 2
        aura = self._auras[min(len(self._auras) - 1, int(fase * len(self._auras)))]
        if pose == 'morrer':
            aura = self._auras[0]
        tela.blit(aura, aura.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)

    def _desenhar_rastro(self, tela):
        for ponto in self.rastro:
            ponto[0] -= DESLIZE
        for i, (x, y, silhueta) in enumerate(self.rastro):
            if i % 2 == 0:
                continue
            copia = silhueta.copy()
            copia.set_alpha(max(0, 170 - i * 25))
            tela.blit(copia, copia.get_rect(center=(x, y)))

    def _emitir(self, destino, pose):
        quantas = 2 if pose == 'pular' else 1
        if len(self.faiscas) >= MAX_FAISCAS:
            return
        sorteio = self.aleatorio
        for _ in range(quantas):
            x = destino.left + destino.width * sorteio.uniform(0.1, 0.45)
            y = destino.top + destino.height * sorteio.uniform(0.2, 0.9)
            self.faiscas.append([x, y, sorteio.uniform(-1.6, 0.2), sorteio.uniform(-1.4, 0.4),
                                 0, sorteio.randint(16, 28), sorteio.uniform(2.5, 4.5)])

    def _explosao(self, centro):
        sorteio = self.aleatorio
        for i in range(12):
            angulo = i / 12 * math.tau + sorteio.uniform(-0.2, 0.2)
            velocidade = sorteio.uniform(3.0, 5.0)
            self.faiscas.append([centro[0], centro[1], math.cos(angulo) * velocidade,
                                 math.sin(angulo) * velocidade, 0, sorteio.randint(12, 18),
                                 sorteio.uniform(3.5, 5.5)])
        self.ondas.append([centro[0], centro[1], 0])

    def _desenhar_faiscas(self, tela):
        vivas = []
        for f in self.faiscas:
            f[0] += f[2] - DESLIZE * 0.5
            f[1] += f[3]
            f[3] += 0.08                       # um pouco de gravidade: caem como purpurina
            f[2] *= 0.94
            f[4] += 1
            if f[4] >= f[5]:
                continue
            vivas.append(f)
            resto = 1 - f[4] / f[5]
            tamanho = f[6] * resto
            x, y = round(f[0]), round(f[1])
            cor = OURO_CLARO if (f[4] // 3) % 2 == 0 else OURO
            if tamanho < 1.5:
                tela.fill(cor, (x, y, 2, 2))
                continue
            t = round(tamanho)
            pygame.draw.line(tela, cor, (x - t, y), (x + t, y), 2)
            pygame.draw.line(tela, cor, (x, y - t), (x, y + t), 2)
            tela.fill(BRANCO_QUENTE, (x - 1, y - 1, 2, 2))
        self.faiscas = vivas

    def _desenhar_ondas(self, tela):
        vivas = []
        for onda in self.ondas:
            onda[0] -= DESLIZE * 0.5
            onda[2] += 1
            if onda[2] > 12:
                continue
            vivas.append(onda)
            raio = 10 + onda[2] * 3.2
            camada = pygame.Surface((raio * 2 + 6, raio * 2 + 6), pygame.SRCALPHA)
            alfa = round(220 * (1 - onda[2] / 12))
            pygame.draw.circle(camada, (*OURO, alfa), (raio + 3, raio + 3), raio, 3)
            tela.blit(camada, camada.get_rect(center=(onda[0], onda[1])))
        self.ondas = vivas

    def _reflexo(self, tela, pose, giro, destino):
        """Faixa de luz diagonal que atravessa o personagem (recortada pela silhueta)."""
        fase = self.quadro % PERIODO_REFLEXO
        if fase >= DURACAO_REFLEXO:
            return
        largura, altura = destino.size
        inclinacao = altura * 0.5
        x = -10 + (largura + inclinacao + 20) * fase / DURACAO_REFLEXO
        faixa = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.polygon(faixa, (255, 255, 255, 170),
                            [(x, 0), (x + 9, 0), (x + 9 - inclinacao, altura), (x - inclinacao, altura)])
        faixa.blit(self._sprite('mascara', pose, giro), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        tela.blit(faixa, destino)
