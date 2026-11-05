"""Dificuldade por nível e helpers de justiça das passagens.

Funções puras: recebem o nível e devolvem parâmetros. São as tabelas do jogo
original (10 níveis); a curva de 25 níveis (difficulty_curve.py) parte delas.

Toda a dificuldade das fases passa por aqui: as classes das fases não fazem
contas com o número do nível, só leem estes dicionários (cfg).
"""
import random

from ..config.constants import (
    ABERTURA_CANOS,
    ABERTURA_DONKEY,
    ABERTURA_POR_NIVEL,
    CHANCE_BARRIL,
    ESPACO_ENTRE_CANOS,
    FRAMES_ANTECIPACAO_KONG,
    GRAVIDADE,
    GRAVIDADE_POR_NIVEL,
    NIVEL_MAXIMO,
    PONTOS_ENTRE_ESPECIAIS,
    QUADROS_ENTRE_TOQUES,
    TEMPO_GALAGA,
    VELOCIDADE_CANOS,
    VELOCIDADE_DONKEY,
    VELOCIDADE_POR_NIVEL,
    VELOCIDADE_TIRO_INIMIGO,
)


def parametros_nivel(nivel):
    """Tabela de dificuldade do modo clássico para o nível 1 a NIVEL_MAXIMO.

    nível 1: gravidade 1,10 | abertura 290 px | velocidade 4,00 px/quadro
    nível 10: gravidade 1,64 | abertura 191 px | velocidade 5,35 px/quadro
    (a abertura final é cerca de 4 alturas do pássaro, como no jogo original).
    'pontos_passaros' = quantos pássaros-obstáculo passar na fase dos pássaros do
    nível; 'oscilacao_passaros' = quanto (px) os pássaros sobem e descem
    (só a partir do nível 4), o que obriga a acompanhar a passagem.
    """
    n = max(1, min(NIVEL_MAXIMO, int(nivel))) - 1          # 0 a 9
    return {
        'gravidade': GRAVIDADE + GRAVIDADE_POR_NIVEL*n,
        'abertura': ABERTURA_CANOS - ABERTURA_POR_NIVEL*n,
        'velocidade': VELOCIDADE_CANOS + VELOCIDADE_POR_NIVEL*n,
        'pontos_passaros': 15 + n,
        'oscilacao_passaros': 0 if n < 3 else min(36, 9*(n - 2)),
    }

def proximo_multiplo(pontos):
    """Menor múltiplo de PONTOS_ENTRE_ESPECIAIS ESTRITAMENTE maior que 'pontos'.

    0 -> 35, 34 -> 35, 35 -> 70, 69 -> 70, 70 -> 105... Função pura: fácil de testar.
    """
    return (pontos // PONTOS_ENTRE_ESPECIAIS + 1)*PONTOS_ENTRE_ESPECIAIS

def desvio_maximo_passagem(abertura, velocidade, gravidade, impulso,
                           largura_cano, largura_passaro, altura_passaro):
    """Maior diferença de altura aceitável entre
    duas passagens seguidas.

    Entre o fim de um par de obstáculos e o começo do próximo o pássaro tem uma
    janela horizontal de (espaço - largura do cano - largura do pássaro) px, ou
    seja, janela/velocidade quadros. Batendo asas a cada QUADROS_ENTRE_TOQUES
    quadros ele sobe, em média, impulso - g*(k+1)/2 px por quadro (soma de
    -v0 + g*i para i = 1..k, dividida por k). A folga dentro da própria passagem
    (abertura - altura do pássaro) também conta. Usamos 75% da subida teórica
    para sobrar margem a quem joga: a fase fica difícil, mas nunca impossível.
    """
    janela = ESPACO_ENTRE_CANOS - largura_cano - largura_passaro
    quadros = janela/velocidade
    subida = max(1.0, abs(impulso) - gravidade*(QUADROS_ENTRE_TOQUES + 1)/2)
    folga = max(0.0, abertura - altura_passaro)
    return int(folga + 0.75*subida*quadros)

def sortear_topo_passagem(topo_anterior, desvio_max):
    """Sorteia o topo da próxima passagem (150 a 400 px), limitando a
    distância até a passagem anterior a desvio_max (veja a função acima)."""
    topo = random.randint(150, 400)
    if topo_anterior is not None:
        topo = max(topo_anterior - desvio_max, min(topo_anterior + desvio_max, topo))
        topo = max(150, min(400, topo))
    return topo

def parametros_galaga(nivel):
    """Parâmetros de dificuldade da Galaga para o nível do jogo.

    nivel = 0 no nível 1 (dificuldade MODERADA) ... 9 no nível 10. A curva liga
    mecânicas novas pelo caminho, em vez de só acelerar tudo:
      níveis 1-2: formação balançando, mergulhos e tiros (base) + FÚRIA suave;
      nível 2+  : mergulhos em ESQUADRÃO (2 pássaros saem juntos, escalonados);
      nível 3+  : mergulhos que PERSEGUEM a nave e chefes de fileira que atiram
                  em LEQUE (3 tiros; 5 tiros a partir do nível 6);
      nível 5+  : esquadrões de 3 e a formação ganha a 5ª linha;
      nível 10  : 5 mergulhando juntos, tiros rápidos e FÚRIA ligada com 40% dos
                  inimigos vivos.
    FÚRIA: quando restam poucos inimigos, os sobreviventes enlouquecem:
    mergulham e atiram bem mais depressa (com um anel vermelho em volta).
    Depois da formação vem o CHEFÃO (veja ChefeGalaga).
    """
    n = max(0, min(NIVEL_MAXIMO - 1, nivel))
    return {
        'linhas': (3, 3, 4, 4, 4, 5, 5, 5, 5, 5)[n],
        'max_mergulhos': 2 + (n + 1)//3,                # mergulhando ao mesmo tempo
        'intervalo_mergulho': max(0.9, 1.8 - 0.10*n),   # s entre mergulhos (base)
        'duracao_mergulho': max(1.6, 2.6 - 0.12*n),     # s por mergulho (menos = mais rápido)
        'multiplicador_tiro': max(0.6, 1 - 0.045*n),    # encurta o intervalo (0,7 a 1,6 s) entre tiros
        'velocidade_tiro': min(400, VELOCIDADE_TIRO_INIMIGO + 13*n),
        'max_tiros': 5 + (2*n)//3,                      # tiros inimigos na tela
        'esquadrao': min(3, 1 + (n + 2)//3),            # 1, 2, 2, 2, 3...
        'persegue': 0.0 if n < 2 else min(0.8, 0.12*(n - 1)),
        'leque': 0 if n < 2 else (3 if n < 5 else 5),   # tiros do leque dos chefes de fileira
        'furia': min(0.4, 0.2 + 0.025*n),               # fração restante que liga a fúria
        'balanco': min(60, 30 + 4*n),                   # amplitude do balanço (px)
        'freq_balanco': min(1.6, 0.9 + 0.08*n),
        'tempo': TEMPO_GALAGA + 3*n,                    # limite de tempo da formação (s)
        # --- chefão (Boss Galaga) ---
        'chefe_hp': 24 + 4*n,                           # 24 PV no nível 1 ... 60 no nível 10
        'chefe_intervalo': max(0.9, 2.4 - 0.15*n),      # s entre ataques (x0,75 na 2ª metade da vida)
        'chefe_leque': 5 + n//3,                        # tiros do ataque em LEQUE
        'chefe_aviso_raio': max(0.8, 1.2 - 0.04*n),     # s de aviso antes do RAIO TRATOR
        'chefe_escoltas': 3 + n//4,                     # escoltas convocadas a 66% e 33% da vida
        'chefe_velocidade': 150 + 10*n,                 # px/s do vai e vem
        'chefe_freq_movimento': 0.55 + 0.04*n,          # frequência do vai e vem
        'chefe_vel_tiro': 250 + 12*n,                   # px/s dos tiros do chefão
        'escolta_duracao_mergulho': max(1.6, 2.6 - 0.1*n),
    }

def parametros_donkey(nivel):
    """Parâmetros de dificuldade do Donkey Kong para o nível do jogo
    (nivel = 0 no nível 1 ... 9 no nível 10).

    Travessia (barris entre as pilhas):
      - a rolagem fica mais rápida e a abertura entre as pilhas, menor;
      - Kong passa a arremessar SALVAS: 1 barril nos níveis 1-2; 2 barris nos
        níveis 3-5; 2 ou 3 barris (cada vez mais 3) do nível 6 em diante;
      - quase todo intervalo tem barril (a chance sobe até 100%) e Kong ergue o
        barril mais depressa (menos quadros de preparo): o "disparo" acelera;
      - nas salvas de 2 ou 3 barris, o pássaro passa por um TÚNEL livre entre os
        barris (altura 'faixa'), que estreita de 130 para 85 px.
    Chefão (Kong furioso): barris mais rápidos, bolas de fogo (a partir do nível 2)
    e mais rebites para coletar.
    """
    n = max(0, min(NIVEL_MAXIMO - 1, nivel))
    return {
        'velocidade': VELOCIDADE_DONKEY + 0.18*n,           # 5,0 -> 6,6 px/quadro
        'abertura': ABERTURA_DONKEY - 6*n,                  # 300 -> 246 px
        'chance_barril': min(1.0, CHANCE_BARRIL + 0.1*n),   # 50% -> 100%
        'salva_min': 1 if n < 2 else 2,
        'salva_max': 1 if n < 2 else (2 if n < 5 else 3),
        'chance_tres': 0.0 if n < 5 else (0.5 if n < 7 else 0.8),
        'faixa': 130 - 5*n,                                 # túnel livre (px) entre os barris
        'antecipacao': max(8, FRAMES_ANTECIPACAO_KONG - n//2),   # quadros de preparo (14 -> 10)
        # --- chefão ---
        'rebites': 4 + n//4,                                # 4, 4, 4, 4, 5, 5, 5, 5, 6, 6
        'chefe_intervalo': max(1.4, 3.2 - 0.2*n),           # s entre ataques
        'chefe_barris': 2 if n < 3 else 3,
        'chefe_vel_barril': 5.5 + 0.2*n,                    # px/quadro
        'chefe_vel_fogo': 8.0 + 0.3*n,
        'fogo': n >= 1,                                     # chamas no chefão a partir do nível 2
        'fogo_chamas': 1 + (1 if n >= 3 else 0) + (1 if n >= 7 else 0),   # chamas por ataque
    }


class DificuldadeOriginal:
    """Provedor de dificuldade com as tabelas do jogo original (níveis 1 a 10).

    A sessão pede os parâmetros pelo nível do jogo (sempre 1, 2, 3...); a
    conversão para o índice interno das tabelas (0 a 9) fica aqui.
    """
    nivel_maximo = NIVEL_MAXIMO

    def flappy(self, nivel):
        return parametros_nivel(nivel)

    def galaga(self, nivel):
        return parametros_galaga(nivel - 1)

    def donkey(self, nivel):
        return parametros_donkey(nivel - 1)
