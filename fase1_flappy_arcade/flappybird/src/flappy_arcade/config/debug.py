"""Atalhos de teste do desenvolvedor (desligados por padrão).

Para ligar, defina a variável de ambiente FLAPPY_DEBUG=1 antes de abrir o jogo
(PowerShell: $env:FLAPPY_DEBUG=1; python src/main.py).

Teclas (fora da tela de cadastro):
  G / K / F   alerta + Galaga / Donkey Kong / fase dos pássaros
  T           pontuação 1 ponto abaixo do próximo gatilho
  B           (Galaga ou Donkey) pula direto para o chefão
  C           (Galaga ou Donkey) solta uma cápsula de bônus
  V           tela de Honra Máxima
  1..9 e 0    muda na hora para o nível 1..10
Partida em que um atalho foi usado não entra no ranking.
"""
import os

import pygame

from .constants import NIVEL_MAXIMO


# Teclas numéricas de teste -> nível (1 a 9; 0 = nível 10; teclado numérico também).
TECLAS_NIVEL = {}

for _nivel in range(1, NIVEL_MAXIMO + 1):
    _digito = _nivel % 10
    TECLAS_NIVEL[getattr(pygame, f'K_{_digito}')] = _nivel
    TECLAS_NIVEL[getattr(pygame, f'K_KP{_digito}')] = _nivel

MODO_TESTE = os.environ.get('FLAPPY_DEBUG') == '1'   # atalhos de teste ligados?

ATALHO_INVALIDA_RANKING = True   # partida em que um atalho foi usado NÃO entra no ranking (veja ClassicSession.registrar_partida)
