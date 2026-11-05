"""Perfis da curva de 25 níveis: como cada parâmetro cresce do nível 1 ao 25.

Para balancear o jogo, mexa só neste arquivo.

Regras gerais (garantidas por testes em tests/test_difficulty_curve.py):
  * nível 1 = exatamente o nível 1 do jogo original (o valor inicial nunca é
    escrito aqui: vem sempre da tabela original);
  * nível 25 = o nível 10 do jogo original, o teto que o jogo já tinha
    (exceto onde 'fim' diz outro valor, como no Flappy);
  * cada parâmetro só anda numa direção (nunca "alivia" no meio do caminho);
  * nenhuma passagem do Flappy fica impossível de alcançar.

Tipos de especificação:
  Rampa(...)    cresce suavemente entre o valor inicial e 'fim'.
                curva < 1 sobe mais cedo; curva > 1 sobe mais tarde.
                desde=N mantém o valor inicial até o nível N e então começa
                (em 'inicio', se dado): bom para mecânicas que "ligam".
  Degraus({...}) muda de valor em níveis marcados: {1: a, 6: b, 14: c}
                significa a nos níveis 1-5, b nos 6-13 e c do 14 em diante.

Correspondência usada para os degraus: nível k do original ~ nível
1 + (k - 1) * 24/9 da curva (2 -> 4, 3 -> 6, 4 -> 9, 5 -> 12, 6 -> 14, 7 -> 17, 8 -> 20).
Onde o original ligava várias mecânicas no mesmo nível, a curva as separa
(uma novidade por casa): o playtest mostrou um degrau brusco quando três
entravam juntas na casa 6 da Galaga.
"""
from dataclasses import dataclass, field

NIVEIS = 25

# Modo Livre: a dificuldade sobe um nível a cada X segundos de jogo (sem pausas).
LIVRE_SEGUNDOS_POR_NIVEL = 40


@dataclass(frozen=True)
class Rampa:
    fim: float | None = None     # valor no nível 25 (None = nível 10 do original)
    curva: float = 1.0
    inteiro: bool = False
    desde: int = 1
    inicio: float | None = None


@dataclass(frozen=True)
class Degraus:
    valores: dict = field(default_factory=dict)


FLAPPY = {
    # O Flappy vai um pouco além do nível 10 original (1,64 | 191 px | 5,35),
    # mantendo a passagem justa (ver teste de justiça).
    'gravidade': Rampa(fim=1.70, curva=0.85),
    'abertura': Rampa(fim=175, curva=0.85, inteiro=True),
    'velocidade': Rampa(fim=6.20, curva=0.85),
    'pontos_passaros': Rampa(inteiro=True),                     # 15 -> 24
    'oscilacao_passaros': Rampa(fim=36, desde=9, inicio=9, inteiro=True, curva=0.7),
}

GALAGA = {
    'linhas': Degraus({1: 3, 6: 4, 13: 5}),
    'max_mergulhos': Rampa(inteiro=True),                       # 2 -> 5
    'intervalo_mergulho': Rampa(),                              # 1,8 s -> 0,9 s
    'duracao_mergulho': Rampa(),
    'multiplicador_tiro': Rampa(),
    'velocidade_tiro': Rampa(inteiro=True),
    'max_tiros': Rampa(inteiro=True),                           # 5 -> 11
    'esquadrao': Degraus({1: 1, 4: 2, 12: 3}),
    'persegue': Rampa(desde=7, inicio=0.12),                    # liga no nível 7
    'leque': Degraus({1: 0, 8: 3, 16: 5}),
    'furia': Rampa(),
    'balanco': Rampa(inteiro=True),
    'freq_balanco': Rampa(),
    'tempo': Rampa(inteiro=True),
    'chefe_hp': Rampa(inteiro=True),                            # 24 -> 60
    'chefe_intervalo': Rampa(),
    'chefe_leque': Rampa(inteiro=True),
    'chefe_aviso_raio': Rampa(),
    'chefe_escoltas': Rampa(inteiro=True),
    'chefe_velocidade': Rampa(inteiro=True),
    'chefe_freq_movimento': Rampa(),
    'chefe_vel_tiro': Rampa(inteiro=True),
    'escolta_duracao_mergulho': Rampa(),
}

DONKEY = {
    'velocidade': Rampa(),                                      # 5,0 -> 6,62 px/quadro
    'abertura': Rampa(inteiro=True),                            # 300 -> 246 px
    'chance_barril': Rampa(curva=0.6),                          # 50% -> 100%
    'salva_min': Degraus({1: 1, 6: 2}),
    'salva_max': Degraus({1: 1, 6: 2, 14: 3}),
    'chance_tres': Rampa(desde=14, inicio=0.5),                 # salvas de 3 a partir do 14
    'faixa': Rampa(inteiro=True),                               # túnel entre barris 130 -> 85 px
    'antecipacao': Rampa(inteiro=True),
    'rebites': Rampa(inteiro=True),
    'chefe_intervalo': Rampa(),
    'chefe_barris': Degraus({1: 2, 9: 3}),
    'chefe_vel_barril': Rampa(),
    'chefe_vel_fogo': Rampa(),
    'fogo': Degraus({1: False, 4: True}),
    'fogo_chamas': Degraus({1: 1, 9: 2, 19: 3}),
}

PERFIS = {'flappy': FLAPPY, 'galaga': GALAGA, 'donkey': DONKEY}
