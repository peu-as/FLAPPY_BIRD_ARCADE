"""Regras da economia: onde as moedas aparecem e quanto valem.

As moedas nunca mudam a dificuldade: ficam onde o jogador já precisa passar
(o centro da passagem dos canos), caem soltas e opcionais na Galaga, ou
vêm das bananas que o Donkey Kong já espalha pela selva.
O jogo clássico (o original) não tem moedas.
"""

VALOR_MOEDA = 1

# Flappy (canos e fase dos pássaros): chance de cada passagem trazer uma moeda.
CHANCE_MOEDA_NA_PASSAGEM = 0.6

# Galaga: uma moeda cai do topo a cada tantos segundos.
INTERVALO_MOEDA_GALAGA = 3.0
VELOCIDADE_MOEDA_GALAGA = 140         # px/s

# Donkey Kong: cada banana coletada vale tantas moedas.
MOEDAS_POR_BANANA = 1

# Mapas e jornada: bônus por estrela NOVA (repetir uma casa não multiplica o bônus).
BONUS_POR_ESTRELA_NOVA = 10

RAIO_MOEDA = 13
