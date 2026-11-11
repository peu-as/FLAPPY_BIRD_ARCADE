"""Modo Combina 3: medidas do tabuleiro, objetivos, chefões e as 25 casas.

Cada casa tem um número de jogadas e um ou mais OBJETIVOS (todos precisam ser
cumpridos):
    (PONTOS, 3000)            fazer 3.000 pontos
    (COLETAR, 'pena', 15)     limpar 15 penas (por combinação ou por efeito)
    (GELO,)                   quebrar todo o gelo (cada camada conta)
    (CAIXAS,)                 quebrar todas as caixas (cada golpe conta)
    (CHEFE,)                  zerar a vida do chefão da casa (veja CHEFES)

O tabuleiro de cada casa é desenhado em texto, 8 linhas de 7 casas:
    .  casa comum        #  pedra (não existe)
    c  caixa (1 golpe)   C  caixa reforçada (2 golpes)
    g  gelo (1 camada)   G  gelo grosso (2 camadas)

Chefões: cada peça limpa tira 1 de vida (gelo e caixas também), e cada peça
especial disparada tira DANO_POR_EFEITO a mais. A cada `a_cada` jogadas ele
ataca: o Rei-Inseto prende peças em casulos (caixas de 1 golpe) e o Kong
arremessa barris (caixas de 2 golpes). Com metade da vida, fica bravo e
ataca uma casa a mais.

Estrelas: quanto mais jogadas sobram quando o último objetivo é cumprido,
mais estrelas (como as vidas nos outros mapas). Metas calibradas com
tools/playtest_combina3.py --casas (veja docs/balanceamento.md).
"""
import math
from dataclasses import dataclass

LINHAS, COLUNAS = 8, 7
CELULA = 70                           # px
TIPOS_DE_PECA = 6

PONTOS, COLETAR, GELO, CAIXAS, CHEFE = 'pontos', 'coletar', 'gelo', 'caixas', 'chefe'

FRACAO_3_ESTRELAS = 0.30              # sobrando 30% das jogadas (ou mais)
FRACAO_2_ESTRELAS = 0.12

DANO_POR_EFEITO = 3                   # cada Pena-Raio, Ovo Nova ou Arco-íris disparado
MAX_CAIXAS_DO_CHEFE = 12              # o chefão não cobre o tabuleiro inteiro

# Moedas (Fase 18): uma vitória típica rende ~25, como uma casa dos mapas antigos.
MOEDAS_POR_ESPECIAL = 2               # cada peça especial criada
JOGADAS_POR_MOEDA = 1                 # na vitória: 1 moeda por jogada que sobrou
MOEDAS_POR_VITORIA = 10
MOEDAS_POR_CHEFE = 15                 # vitória numa casa de chefão

NOMES_PLURAL = {'pena': 'penas', 'folha': 'folhas', 'ovo': 'ovos', 'moeda': 'moedas',
                'semente': 'sementes', 'fruta': 'frutas'}


@dataclass(frozen=True)
class ChefeCombina3:
    nome: str                 # 'rei_inseto' | 'kong' | 'dupla' (os dois juntos)
    titulo: str               # no HUD
    texto: str                # nas frases ("derrote o Kong")
    vida: int
    a_cada: int               # ataca a cada N jogadas
    casulos: int = 0          # Rei-Inseto: peças presas em casulo por ataque
    barris: int = 0           # Kong: barris (caixas de 2 golpes) por ataque


@dataclass(frozen=True)
class CasaCombina3:
    jogadas: int
    objetivos: tuple
    mapa: tuple = ()
    chefao: ChefeCombina3 = None
    tipos: int = TIPOS_DE_PECA

    @property
    def chefe(self):
        return self.chefao is not None

    def obstaculos(self):
        """(pedras, caixas, gelo) lidos do desenho do tabuleiro."""
        pedras, caixas, gelo = set(), {}, {}
        for l, linha in enumerate(self.mapa):
            for c, ch in enumerate(linha):
                if ch == '#':
                    pedras.add((l, c))
                elif ch in 'cC':
                    caixas[(l, c)] = 1 if ch == 'c' else 2
                elif ch in 'gG':
                    gelo[(l, c)] = 1 if ch == 'g' else 2
        return pedras, caixas, gelo


def chefe(nome, vida, a_cada, casulos=0, barris=0):
    titulo, texto = {'rei_inseto': ('REI-INSETO', 'o Rei-Inseto'), 'kong': ('KONG', 'o Kong'),
                     'dupla': ('REI-INSETO E KONG', 'o Rei-Inseto e o Kong')}[nome]
    return ChefeCombina3(nome, titulo, texto, vida, a_cada, casulos, barris)


def _casa(jogadas, *objetivos, mapa=(), chefao=None):
    if chefao is not None:
        objetivos = ((CHEFE,),) + objetivos
    assert not mapa or (len(mapa) == LINHAS and all(len(linha) == COLUNAS for linha in mapa)), mapa
    return CasaCombina3(jogadas, tuple(objetivos), tuple(mapa), chefao)


LIVRE = ('.......',) * LINHAS

CASAS_COMBINA3 = (
    # 1-4: aprender (pontos, coletar, gelo)
    _casa(20, (PONTOS, 2500)),
    _casa(20, (COLETAR, 'pena', 16)),
    _casa(20, (GELO,), mapa=('.......', '.......', '.......', '.ggggg.',
                             '.ggggg.', '.......', '.......', '.......')),
    _casa(20, (COLETAR, 'folha', 14), (COLETAR, 'fruta', 14)),
    # 5: chefão
    _casa(22, chefao=chefe('rei_inseto', 160, 4, casulos=2)),
    # 6-9: caixas e pedras
    _casa(20, (CAIXAS,), mapa=('.......', '.......', '.......', '.......',
                               'cc.c.cc', '.......', '.......', '.......')),
    _casa(20, (PONTOS, 3800), mapa=('#.....#', '.......', '.......', '.......',
                                    '.......', '.......', '.......', '#.....#')),
    _casa(20, (GELO,), mapa=('.......', '.......', '..ggg..', '.gGgGg.',
                             '.gGgGg.', '..ggg..', '.......', '.......')),
    _casa(20, (COLETAR, 'ovo', 14), (COLETAR, 'moeda', 14),
          mapa=('.......', '.......', '...#...', '...#...', '...#...', '...#...', '.......', '.......')),
    # 10: chefão
    _casa(22, chefao=chefe('kong', 165, 4, barris=2)),
    # 11-14: misturas
    _casa(20, (CAIXAS,), (GELO,), mapa=('.......', '.......', 'c.....c', 'cc...cc',
                                        '.......', '.ggggg.', '.......', '.......')),
    _casa(20, (PONTOS, 4200), mapa=('##...##', '#.....#', '.......', '.......',
                                    '.......', '.......', '#.....#', '##...##')),
    _casa(20, (COLETAR, 'semente', 15), (COLETAR, 'pena', 15), (COLETAR, 'ovo', 15)),
    _casa(22, (GELO,), mapa=('.......', '.......', '.......', '.ggggg.',
                             'gGGGGGg', '.ggggg.', '.......', '.......')),
    # 15: chefão
    _casa(22, chefao=chefe('rei_inseto', 180, 3, casulos=3),
          mapa=('#.....#', '.......', '.......', '.......', '.......', '.......', '.......', '#.....#')),
    # 16-19: mais difíceis
    _casa(20, (CAIXAS,), mapa=('.......', '.......', '.......', 'C.C.C.C',
                               '.......', 'cCcCcCc', '.......', '.......')),
    _casa(20, (GELO,), mapa=('.......', '.#...#.', '.#ggg#.', '.ggggg.',
                             '.ggggg.', '.#ggg#.', '.#...#.', '.......')),
    _casa(20, (COLETAR, 'fruta', 18), (COLETAR, 'moeda', 18),
          mapa=('.......', '.......', 'c.....c', '.c...c.', '..c.c..', '.......', '.......', '.......')),
    _casa(20, (CAIXAS,), (GELO,), mapa=('.......', '.......', 'cC...Cc', '.......',
                                        'ggggggg', 'ggggggg', '.......', '.......')),
    # 20: chefão
    _casa(22, chefao=chefe('kong', 190, 3, barris=2),
          mapa=('.......', '.......', '.......', '.......', 'c.....c', '.......', '.......', '.......')),
    # 21-24: reta final
    _casa(20, (PONTOS, 5400), mapa=('#.#.#.#', '.......', '.......', '.......',
                                    '.......', '.......', '.......', '#.#.#.#')),
    _casa(20, (COLETAR, 'folha', 13), (GELO,), mapa=('.......', '.......', '.......', 'ggg.ggg',
                                                     'ggg.ggg', 'ggg.ggg', '.......', '.......')),
    _casa(20, (CAIXAS,), mapa=('.......', '.......', 'CCCCCCC', '.......',
                               'CcC.CcC', '.......', '.......', '.......')),
    _casa(20, (GELO,), (CAIXAS,), mapa=('.......', 'c.....c', 'Cc...cC', 'gGgGgGg',
                                        'ggggggg', '.......', '.......', '.......')),
    # 25: os dois chefões juntos
    _casa(24, chefao=chefe('dupla', 235, 3, casulos=2, barris=1),
          mapa=('#.....#', '.......', '.......', '.......', '.......', '.......', '.......', '#.....#')),
)


def casa_combina3(numero):
    return CASAS_COMBINA3[numero - 1]


def jogadas_para_estrelas(total):
    """(sobrando para 3 estrelas, sobrando para 2 estrelas)."""
    return math.ceil(total * FRACAO_3_ESTRELAS), math.ceil(total * FRACAO_2_ESTRELAS)


def estrelas_combina3(total, usadas):
    tres, duas = jogadas_para_estrelas(total)
    sobrando = total - usadas
    return 3 if sobrando >= tres else 2 if sobrando >= duas else 1


def _milhar(n):
    return f'{n:,}'.replace(',', '.')


def _juntar(partes):
    return partes[0] if len(partes) == 1 else ', '.join(partes[:-1]) + ' e ' + partes[-1]


def descrever(casa):
    """Texto do cartão de abertura: o que fazer, em quantas jogadas e as 3 estrelas."""
    partes, coletas, quebrar = [], [], []
    for objetivo in casa.objetivos:
        tipo = objetivo[0]
        if tipo == PONTOS:
            partes.append(f'faça {_milhar(objetivo[1])} pontos')
        elif tipo == COLETAR:
            coletas.append(f'{objetivo[2]} {NOMES_PLURAL[objetivo[1]]}')
        elif tipo == GELO:
            quebrar.append('todo o gelo')
        elif tipo == CAIXAS:
            quebrar.append('todas as caixas')
        elif tipo == CHEFE:
            partes.append(f'derrote {casa.chefao.texto}')
    if quebrar:
        partes.append('quebre ' + _juntar(quebrar))
    if coletas:
        partes.append('junte ' + _juntar(coletas))
    tres, _ = jogadas_para_estrelas(casa.jogadas)
    frase = _juntar(partes)
    return f'{frase[0].upper()}{frase[1:]} em {casa.jogadas} jogadas. 3 estrelas: sobrando {tres}.'
