"""Catálogo de cenários de fundo (loja e Equipamentos).

Tipos:
  'original'  um dos fundos do jogo original (assets/imgs), já em tela inteira;
  'faixa'     uma paisagem importada (assets/cenarios): faixa de horizonte que
              gameplay/scenery.py transforma em fundo de tela.

O período (dia, tarde, noite) decide a cor dos canos e dos pássaros quando o
cenário estiver na tela, como o jogo original já faz com os seus fundos.
Só o 'bg' vem de graça; o resto se compra. O jogo clássico não usa nada daqui.

Preços: originais 150 a 400 (os de noite e entardecer custam mais);
novos em três faixas: 600, 900 e 1300.
"""
from dataclasses import dataclass

DIA, TARDE, NOITE = 'dia', 'tarde', 'noite'
PERIODOS = (DIA, TARDE, NOITE)
ORIGINAL, FAIXA = 'original', 'faixa'
ORIGINAIS, NOVOS = 'originais', 'novos'
NOMES_GRUPO = {ORIGINAIS: 'ORIGINAIS', NOVOS: 'NOVOS'}

CENARIO_PADRAO = 'bg'
MAX_PLAYLIST = 15
MODO_FIXO, MODO_ALEATORIO = 'fixo', 'aleatorio'
MODOS = (MODO_FIXO, MODO_ALEATORIO)
FAIXAS_PRECO_NOVOS = (600, 900, 1300)


@dataclass(frozen=True)
class Cenario:
    id: str
    nome: str
    preco: int
    periodo: str
    tipo: str = FAIXA
    arquivo: str = ''        # original: nome em assets/imgs; faixa: nome em assets/cenarios

    @property
    def grupo(self):
        return ORIGINAIS if self.tipo == ORIGINAL else NOVOS


def _original(ident, nome, preco, periodo):
    return Cenario(ident, nome, preco, periodo, ORIGINAL, f'{ident}.png')


def _novo(ident, nome, preco, periodo):
    return Cenario(ident, nome, preco, periodo, FAIXA, f'{ident}.png')


CENARIOS = (
    _original('bg', 'Clássico', 0, DIA),
    _original('bg2', 'Chuva', 150, DIA),
    _original('bg3', 'Nevasca', 150, DIA),
    _original('bg6', 'Degelo', 200, DIA),
    _original('background', 'Beira-Mar', 200, DIA),
    _original('bg1', 'Entardecer', 250, TARDE),
    _original('bg4', 'Neve Rosada', 250, TARDE),
    _original('bg8', 'Campo Dourado', 250, TARDE),
    _original('bg7', 'Sol Poente', 300, TARDE),
    _original('night', 'Noite Clássica', 300, NOITE),
    _original('bg5', 'Noite de Neve', 400, NOITE),
    _novo('parque', 'Parque', 600, DIA),
    _novo('praia', 'Praia', 600, DIA),
    _novo('deserto', 'Deserto', 600, DIA),
    _novo('outono', 'Outono', 600, DIA),
    _novo('por_do_sol', 'Pôr do Sol', 600, TARDE),
    _novo('sakura', 'Sakura', 900, DIA),
    _novo('oceano', 'Oceano', 900, DIA),
    _novo('castelo', 'Castelo', 900, DIA),
    _novo('doces', 'Doces', 900, DIA),
    _novo('floresta_magica', 'Floresta Mágica', 900, TARDE),
    _novo('cidade_noturna', 'Cidade Noturna', 900, NOITE),
    _novo('inverno', 'Inverno', 900, NOITE),
    _novo('templo', 'Templo', 900, NOITE),
    _novo('ilhas_flutuantes', 'Ilhas Flutuantes', 1300, DIA),
    _novo('halloween', 'Halloween', 1300, NOITE),
    _novo('estacao_espacial', 'Estação Espacial', 1300, NOITE),
    _novo('vulcao', 'Vulcão', 1300, NOITE),
    _novo('cyberpunk', 'Cyberpunk', 1300, NOITE),
    _novo('planeta', 'Planeta', 1300, NOITE),
    _novo('galaxia', 'Galáxia', 1300, NOITE),
)
POR_ID = {c.id: c for c in CENARIOS}
