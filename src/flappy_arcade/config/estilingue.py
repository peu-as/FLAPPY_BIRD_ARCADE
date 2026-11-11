"""Modo Estilingue: materiais, pássaros, física e as 25 casas.

História: os insetos da Esquadrilha Galaga roubaram os ovos e se esconderam
em fortalezas de madeira, gelo e pedra, com barris do Kong. O pássaro lança
a si mesmo (e aos amigos) com o estilingue para derrubar tudo.

Coordenadas do mundo em pixels, como na tela: x cresce para a direita e y
para baixo; o chão fica em Y_CHAO. As casas são descritas por "módulos"
(torre, casinha, pirâmide, muro, barril...) que viram peças em
gameplay/estilingue/mundo.py. Para mudar uma casa, edite a tabela CASAS_ESTILINGUE
e rode: python tools/playtest_estilingue.py --casas N
"""
from dataclasses import dataclass, field

# ---------------------------------------------------------------- mundo
LARGURA_MUNDO = 1500
X_ESTILINGUE = 150                # base do estilingue
ALTURA_ESTILINGUE = 118           # do chão até o ponto de lançamento
GRAVIDADE = 900.0                 # px/s²
SUBPASSOS = 3                     # passos de física por quadro (30 FPS -> 90 Hz)
ITERACOES = 25                    # precisão do empilhamento
PUXADA_MAXIMA = 110               # px que dá para puxar o elástico
FORCA_LANCAMENTO = 9.2            # velocidade = puxada x força (até ~1000 px/s)

# ---------------------------------------------------------------- dano
IMPULSO_MINIMO = 260              # impulsos menores (repouso, roçar) não causam dano
DANO_POR_IMPULSO = 0.028
RAIO_EXPLOSAO = 140
DANO_EXPLOSAO = 100               # no centro; cai até 0 na borda
IMPULSO_EXPLOSAO = 2600

# ---------------------------------------------------------------- materiais
@dataclass(frozen=True)
class Material:
    nome: str
    vida: float
    densidade: float              # massa por px² (x 1000)
    atrito: float
    elasticidade: float
    pontos: int


MATERIAIS = {
    # vida calibrada pela batida de um pássaro comum (tools/playtest_estilingue.py e testes):
    # gelo quebra com um toque médio (~500 px/s), madeira com um bom acerto (~700 px/s),
    # pedra só com 3 batidas fortes ou explosões
    'gelo': Material('Gelo', 12, 0.7, 0.25, 0.10, 300),
    'madeira': Material('Madeira', 48, 1.0, 0.75, 0.08, 500),
    'pedra': Material('Pedra', 380, 2.4, 0.85, 0.04, 800),
}
VIDA_BARRIL = 18
PONTOS_BARRIL = 600

# ---------------------------------------------------------------- pássaros
@dataclass(frozen=True)
class TipoPassaro:
    id: str
    nome: str
    sprite: str                   # '' = skin equipada; senão, nome em recursos.especiais
    item: str                     # ícone do bônus (gameplay/bonus_visuals.py)
    raio: float
    massa: float
    dica: str


PASSAROS = {
    'comum': TipoPassaro('comum', 'Pássaro', '', '', 22, 5.0, 'o seu pássaro (a skin equipada)'),
    'pena': TipoPassaro('pena', 'Pena Dupla', 'Blue', 'GEMEO', 21, 4.0,
                        'clique no ar: vira três'),
    'foguete': TipoPassaro('foguete', 'Semente-Foguete', 'Speed', 'TURBO', 20, 4.5,
                           'clique no ar: dispara reto e fura madeira'),
    'ovo': TipoPassaro('ovo', 'Ovo Nova', 'Purple', 'BOMBA', 24, 7.0,
                       'clique (ou bata): explode'),
}
FOGUETE_VELOCIDADE = 1500         # px/s depois do disparo
FOGUETE_MULTIPLICADOR_MADEIRA = 2.2
PENA_ABERTURA = 11                # graus entre os três pássaros
PENA_ESCALA = 0.72                # os três são menores
OVO_ESPERA_APOS_BATER = 1.2       # s: explode sozinho depois de bater
ESCALA_EXPLOSAO_OVO = 1.0         # 1.0 = igual à de um barril

# ---------------------------------------------------------------- alvos
VIDA_INSETO = 32
RAIO_INSETO = 18
CHEFES = {                        # vida, raio, pontos
    'rei_inseto': (240, 46, 20000),
    'kong': (240, 52, 20000),
}
PONTOS_INSETO = 5000
PONTOS_PASSARO_SOBRANDO = 10000

# ---------------------------------------------------------------- moedas
MOEDAS_POR_INSETO = 3
MOEDAS_POR_CHEFE = 15
MOEDAS_POR_PASSARO_SOBRANDO = 4
BLOCOS_POR_MOEDA = 4

# ---------------------------------------------------------------- tempo
SEGUNDOS_PARA_ACALMAR = 0.8       # mundo parado por este tempo = jogada terminou
LIMITE_JOGADA = 9.0               # s: uma jogada nunca dura mais que isto
TEMPO_DEPOIS_DE_BATER = 3.5       # s: o pássaro some depois de bater e rolar este tempo
VELOCIDADE_CALMA = 14             # px/s


# ---------------------------------------------------------------- casas
@dataclass(frozen=True)
class CasaEstilingue:
    passaros: tuple               # ordem de lançamento
    modulos: tuple                # ('torre', x, {...}), ('casinha', x, {...}), ...
    chefe: str = ''
    dica: str = ''
    extras: dict = field(default_factory=dict)


def _c(passaros, *modulos, chefe='', dica=''):
    return CasaEstilingue(tuple(passaros.split()), tuple(modulos), chefe, dica)


CASAS_ESTILINGUE = (
    # 1-4: aprender a mirar; gelo; a Pena Dupla
    _c('comum comum comum', ('torre', 920, {'andares': 1, 'material': 'madeira'}),
       dica='Puxe o pássaro para trás e solte!'),
    _c('comum comum comum', ('casinha', 880, {'material': 'gelo'}),
       ('torre', 1040, {'andares': 1, 'material': 'madeira'})),
    _c('comum comum comum', ('torre', 950, {'andares': 2, 'material': 'gelo'}),
       dica='Gelo quebra fácil.'),
    _c('pena comum comum', ('piramide', 900, {'niveis': 3, 'material': 'gelo', 'alvos': 2}),
       dica='Pena Dupla: clique no ar e ela vira três!'),
    _c('comum pena comum comum', ('muro', 800, {'altura': 2, 'material': 'madeira'}),
       ('fortaleza', 1010, {'material': 'madeira'}), chefe='rei_inseto',
       dica='O Rei-Inseto aguenta vários golpes.'),
    # 6-9: barris; muros; a Semente-Foguete
    _c('comum pena comum', ('torre', 880, {'andares': 2, 'material': 'madeira'}),
       ('barril', 990, {}), ('casinha', 1100, {'material': 'gelo'}),
       dica='Barris do Kong explodem!'),
    _c('pena comum pena', ('muro', 790, {'altura': 3, 'material': 'madeira'}),
       ('torre', 960, {'andares': 2, 'material': 'gelo'}), ('torre', 1130, {'andares': 1, 'material': 'gelo'})),
    _c('foguete comum foguete', ('torre', 900, {'andares': 3, 'material': 'madeira'}),
       dica='Semente-Foguete: clique no ar e ela dispara reto.'),
    _c('foguete pena comum', ('casinha', 860, {'material': 'pedra'}),
       ('torre', 1040, {'andares': 2, 'material': 'madeira'}), ('barril', 1160, {})),
    _c('comum foguete pena comum', ('barril', 820, {}), ('muro', 880, {'altura': 2, 'material': 'pedra'}),
       ('fortaleza', 1060, {'material': 'madeira', 'barris': True}), chefe='kong',
       dica='O Kong se escondeu atrás dos barris dele.'),
    # 11-14: misturas; o Ovo Nova
    _c('pena foguete comum comum', ('torre', 860, {'andares': 2, 'material': 'gelo'}),
       ('torre', 1010, {'andares': 2, 'material': 'madeira'}), ('casinha', 1160, {'material': 'gelo'})),
    _c('ovo comum ovo', ('casinha', 880, {'material': 'pedra'}), ('casinha', 1050, {'material': 'pedra'}),
       dica='Ovo Nova: clique (ou bata) e ele explode.'),
    _c('ovo foguete pena', ('piramide', 880, {'niveis': 4, 'material': 'pedra', 'alvos': 2}),
       ('barril', 1060, {}), ('torre', 1150, {'andares': 1, 'material': 'madeira'})),
    _c('pena pena foguete ovo', ('torre', 860, {'andares': 3, 'material': 'gelo'}),
       ('torre', 1030, {'andares': 2, 'material': 'pedra'}), ('barril', 1130, {})),
    _c('foguete pena ovo comum', ('muro', 800, {'altura': 3, 'material': 'pedra'}),
       ('fortaleza', 1020, {'material': 'pedra'}), chefe='rei_inseto'),
    # 16-19: fortalezas maiores
    _c('foguete ovo pena', ('torre', 850, {'andares': 3, 'material': 'madeira'}),
       ('barril', 960, {}), ('torre', 1060, {'andares': 3, 'material': 'madeira'})),
    _c('pena ovo foguete', ('muro', 780, {'altura': 4, 'material': 'gelo'}),
       ('piramide', 920, {'niveis': 4, 'material': 'madeira', 'alvos': 2}),
       ('casinha', 1150, {'material': 'pedra'})),
    _c('pena foguete ovo comum', ('casinha', 840, {'material': 'pedra'}),
       ('torre', 990, {'andares': 3, 'material': 'pedra'}), ('barril', 1100, {}),
       ('casinha', 1180, {'material': 'madeira'})),
    _c('foguete pena foguete', ('torre', 860, {'andares': 4, 'material': 'gelo'}),
       ('barril', 960, {}), ('barril', 1010, {}), ('torre', 1100, {'andares': 3, 'material': 'pedra'})),
    _c('foguete pena ovo', ('barril', 800, {}), ('muro', 860, {'altura': 3, 'material': 'pedra'}),
       ('fortaleza', 1040, {'material': 'pedra', 'barris': True}), chefe='kong'),
    # 21-25: o castelo final
    _c('pena foguete ovo comum', ('torre', 830, {'andares': 3, 'material': 'pedra'}),
       ('piramide', 980, {'niveis': 3, 'material': 'gelo', 'alvos': 2}),
       ('torre', 1180, {'andares': 2, 'material': 'madeira'})),
    _c('pena foguete comum ovo', ('muro', 790, {'altura': 4, 'material': 'pedra'}),
       ('torre', 930, {'andares': 4, 'material': 'madeira'}), ('barril', 1030, {}),
       ('casinha', 1130, {'material': 'pedra'})),
    _c('foguete comum ovo', ('casinha', 850, {'material': 'pedra'}), ('barril', 960, {}),
       ('torre', 1050, {'andares': 4, 'material': 'pedra'}), ('barril', 1150, {}),
       ('casinha', 1230, {'material': 'gelo'})),
    _c('ovo foguete pena ovo', ('piramide', 830, {'niveis': 5, 'material': 'pedra', 'alvos': 3}),
       ('torre', 1110, {'andares': 3, 'material': 'madeira'}), ('barril', 1200, {})),
    _c('pena foguete ovo comum pena', ('muro', 780, {'altura': 4, 'material': 'pedra'}),
       ('fortaleza', 960, {'material': 'pedra', 'barris': True}),
       ('fortaleza', 1230, {'material': 'pedra'}), chefe='rei_inseto+kong',
       dica='O castelo final: o Rei-Inseto e o Kong juntos.'),
)


def casa_estilingue(casa):
    return CASAS_ESTILINGUE[casa - 1]


def estrelas_estilingue(total_passaros, usados):
    """3 estrelas sobrando 2 pássaros (ou mais), 2 sobrando 1, 1 usando todos."""
    return max(1, min(3, 3 - max(0, usados - (total_passaros - 2))))
