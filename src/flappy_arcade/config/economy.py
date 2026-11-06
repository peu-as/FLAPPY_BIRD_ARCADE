"""Regras da economia: onde as moedas aparecem e quanto valem.

As moedas nunca mudam a dificuldade: ficam onde o jogador já precisa passar
(o centro da passagem dos canos), caem soltas e opcionais na Galaga, ou
vêm das bananas que o Donkey Kong já espalha pela selva.
O jogo clássico (o original) não tem moedas.

Fase 14: renda ~3x maior que a da Fase 7, calibrada para que completar os
quatro mapas com 3 estrelas pague cerca de 1/3 da loja inteira (skins e
cenários). O resto vem do Modo Livre. Veja docs/balanceamento.md.
"""

VALOR_MOEDA = 1

# Flappy (canos e fase dos pássaros): chance de cada passagem trazer uma moeda.
CHANCE_MOEDA_NA_PASSAGEM = 0.9

# Galaga: uma moeda cai do topo a cada tantos segundos.
INTERVALO_MOEDA_GALAGA = 2.0
VELOCIDADE_MOEDA_GALAGA = 140         # px/s

# Donkey Kong: cada banana coletada vale tantas moedas.
MOEDAS_POR_BANANA = 2

# Modo Livre: a cada tantos pontos seguidos sem cair, um bônus.
SEQUENCIA_PARA_BONUS = 10
BONUS_POR_SEQUENCIA = 10

# Mapas e jornada: bônus por estrela NOVA (repetir uma casa não multiplica o bônus).
# Casa mais difícil paga mais: 22 por estrela na casa 1, 70 na casa 25.
BONUS_ESTRELA_BASE = 20
BONUS_ESTRELA_POR_CASA = 2


def bonus_por_estrela(casa):
    return BONUS_ESTRELA_BASE + BONUS_ESTRELA_POR_CASA * casa

RAIO_MOEDA = 13
