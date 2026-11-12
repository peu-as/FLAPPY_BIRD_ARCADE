"""Catálogo de skins do pássaro. Só aparência: a colisão nunca muda.

Tipos de skin:
  'paleta'    o pássaro original com as cores trocadas (mantém a animação das asas);
  'especial'  um dos sprites temáticos de assets/imgs (sem animação de asas);
  'arte'      uma das artes importadas para assets/skins (tools/importar_artes.py);
  'personagem' um personagem com várias poses em assets/personagens/<sprite>/
              (tools/importar_personagem.py): a pose muda com o voo (pulo, planar,
              mergulho, no chão) e o retrato aparece nos cartões e no Estilingue;
  efeitos     'brilho', 'fantasma', 'neon', 'arco_iris' (pássaro e rastro mudam de
              cor), 'rastro_arco_iris' (só o rastro), 'poeira' ou 'lendario' (aura,
              rastro dourado, faíscas, explosão ao bater asas e reflexo; animados,
              somem quando os efeitos visuais estão desligados).

Categorias: Clássicas (as 18 primeiras), Fantasias (35 artes + a lendária) e Times (32 artes).
Faixas de preço: comuns 50 a 200, raras 250 a 500, radicais 1000 a 2500, lendárias 5000 ou mais.
Times custam 200; fantasias simples 120; detalhadas 350 a 500; radicais com efeito.
A lendária (Wilson Luciano) é a mais cara do jogo: 5000 moedas.
"""
from dataclasses import dataclass, field

COMUM, RARA, RADICAL, LENDARIA = 'comum', 'rara', 'radical', 'lendaria'
NOMES_RARIDADE = {COMUM: 'COMUM', RARA: 'RARA', RADICAL: 'RADICAL', LENDARIA: 'LENDÁRIA'}
CORES_RARIDADE = {COMUM: (120, 168, 72), RARA: (72, 120, 220), RADICAL: (200, 84, 200), LENDARIA: (226, 160, 24)}

CLASSICAS, FANTASIAS, TIMES = 'classicas', 'fantasias', 'times'
CATEGORIAS = (CLASSICAS, FANTASIAS, TIMES)
NOMES_CATEGORIA = {CLASSICAS: 'CLÁSSICAS', FANTASIAS: 'FANTASIAS', TIMES: 'TIMES'}
FAIXAS_PRECO = {COMUM: (50, 200), RARA: (250, 500), RADICAL: (1000, 2500), LENDARIA: (5000, 20_000)}

# Cores do pássaro original que a troca de paleta substitui.
CORPO, CORPO_SOMBRA, BARRIGA, BICO = 'corpo', 'corpo_sombra', 'barriga', 'bico'
PALETA_ORIGINAL = {           # valores exatos dos pixels de bird1/2/3.png
    CORPO: (248, 183, 51),
    CORPO_SOMBRA: (224, 128, 44),
    BARRIGA: (250, 215, 140),
    BICO: (252, 56, 0),
}


@dataclass(frozen=True)
class Skin:
    id: str
    nome: str
    raridade: str
    preco: int
    tipo: str = 'paleta'          # 'paleta' | 'especial' | 'arte' | 'personagem'
    cores: dict = field(default_factory=dict)    # paleta: papel -> cor nova
    sprite: str = ''                             # especial: nome do PNG; arte: id do arquivo
    efeito: str = ''
    categoria: str = CLASSICAS


def _fantasia(ident, nome, raridade, preco, efeito=''):
    return Skin(ident, nome, raridade, preco, tipo='arte', sprite=ident, efeito=efeito, categoria=FANTASIAS)


def _time(ident, nome):
    return Skin(f'time_{ident}', nome, COMUM, PRECO_TIME, tipo='arte', sprite=f'time_{ident}', categoria=TIMES)


PRECO_TIME = 200
PRECO_FANTASIA_SIMPLES = 120


SKINS = (
    Skin('classico', 'Clássico', COMUM, 0),
    Skin('azul', 'Céu Azul', COMUM, 50, cores={CORPO: (72, 156, 232), CORPO_SOMBRA: (40, 104, 196), BARRIGA: (196, 228, 248)}),
    Skin('verde', 'Limão', COMUM, 60, cores={CORPO: (136, 216, 72), CORPO_SOMBRA: (88, 168, 48), BARRIGA: (220, 244, 168)}),
    Skin('vermelho', 'Pimenta', COMUM, 60, cores={CORPO: (232, 72, 64), CORPO_SOMBRA: (176, 40, 40), BARRIGA: (248, 184, 160), BICO: (248, 200, 40)}),
    Skin('rosa', 'Chiclete', COMUM, 75, cores={CORPO: (248, 136, 192), CORPO_SOMBRA: (216, 88, 152), BARRIGA: (252, 216, 232)}),
    Skin('roxo', 'Uva', COMUM, 80, cores={CORPO: (160, 96, 216), CORPO_SOMBRA: (112, 64, 176), BARRIGA: (220, 196, 244)}),
    Skin('neve', 'Neve', COMUM, 100, cores={CORPO: (236, 240, 248), CORPO_SOMBRA: (184, 196, 216), BARRIGA: (255, 255, 255), BICO: (248, 144, 40)}),
    Skin('oculos', 'Estiloso', RARA, 250, tipo='especial', sprite='Glasses'),
    Skin('peixe', 'Peixinho', RARA, 300, tipo='especial', sprite='Fishy'),
    Skin('helice', 'Hélice', RARA, 300, tipo='especial', sprite='Propellor'),
    Skin('policia', 'Patrulha', RARA, 350, tipo='especial', sprite='Police'),
    Skin('bolha', 'Bolha', RARA, 400, tipo='especial', sprite='Bubble'),
    Skin('selva', 'Camuflado', RARA, 450, tipo='especial', sprite='Jungle'),
    Skin('veloz', 'Turbo', RARA, 500, tipo='especial', sprite='Speed'),
    Skin('dourado', 'Dourado', RADICAL, 1000, efeito='brilho',
         cores={CORPO: (252, 212, 64), CORPO_SOMBRA: (216, 156, 24), BARRIGA: (255, 240, 176), BICO: (232, 120, 24)}),
    Skin('fantasma', 'Fantasma', RADICAL, 1200, efeito='fantasma',
         cores={CORPO: (216, 232, 248), CORPO_SOMBRA: (152, 176, 216), BARRIGA: (248, 252, 255), BICO: (120, 144, 200)}),
    Skin('neon', 'Neon', RADICAL, 1600, efeito='neon',
         cores={CORPO: (40, 32, 64), CORPO_SOMBRA: (24, 20, 40), BARRIGA: (64, 248, 232), BICO: (248, 64, 200)}),
    Skin('arco_iris', 'Arco-íris', RADICAL, 2500, efeito='arco_iris'),
)

# Lendária: personagem com poses e o efeito mais caprichado do jogo (a mais cara da loja).
PRECO_LENDARIA = 5000
WILSON = Skin('wilson', 'Wilson Luciano', LENDARIA, PRECO_LENDARIA, tipo='personagem', sprite='wilson',
              efeito='lendario', categoria=FANTASIAS)

FANTASIAS_SKINS = (
    WILSON,                       # primeira da aba Fantasias: a vitrine da loja
    # simples: um acessório ou uma cor
    *(_fantasia(i, n, COMUM, PRECO_FANTASIA_SIMPLES) for i, n in (
        ('gato', 'Gato'), ('cachorro', 'Cachorro'), ('sapo', 'Sapo'), ('panda', 'Panda'),
        ('abelha', 'Abelha'), ('joaninha', 'Joaninha'), ('ninja', 'Ninja'), ('esportista', 'Esportista'),
        ('gamer', 'Gamer'), ('inverno', 'Inverno'), ('verao', 'Verão'))),
    # detalhadas
    _fantasia('chef', 'Chef', RARA, 350),
    _fantasia('cowboy', 'Cowboy', RARA, 350),
    _fantasia('abobora', 'Abóbora', RARA, 350),
    _fantasia('fantasminha', 'Fantasminha', RARA, 350),
    _fantasia('borboleta', 'Borboleta', RARA, 350),
    _fantasia('aniversario', 'Aniversário', RARA, 350),
    _fantasia('rena', 'Rena', RARA, 350),
    _fantasia('elfo', 'Elfo', RARA, 400),
    _fantasia('boneco_de_neve', 'Boneco de Neve', RARA, 400),
    _fantasia('papai_noel', 'Papai Noel', RARA, 400),
    _fantasia('vampiro', 'Vampiro', RARA, 400),
    _fantasia('pirata', 'Pirata', RARA, 400),
    _fantasia('rockstar', 'Rockstar', RARA, 400),
    _fantasia('mago', 'Mago', RARA, 450),
    _fantasia('bruxa', 'Bruxa', RARA, 450),
    _fantasia('alien', 'Alien', RARA, 450),
    _fantasia('robo', 'Robô', RARA, 450),
    _fantasia('rei', 'Rei', RARA, 500),
    _fantasia('rainha', 'Rainha', RARA, 500),
    _fantasia('astronauta', 'Astronauta', RARA, 500),
    # radicais: com efeito animado
    _fantasia('dinossauro', 'Dinossauro', RADICAL, 1200, 'poeira'),
    _fantasia('fada', 'Fada', RADICAL, 1500, 'brilho'),
    _fantasia('futurista', 'Futurista', RADICAL, 1800, 'neon'),
    _fantasia('unicornio', 'Unicórnio', RADICAL, 2000, 'rastro_arco_iris'),
)

TIMES_SKINS = tuple(_time(i, n) for i, n in (
    ('santos', 'Santos'), ('flamengo', 'Flamengo'), ('palmeiras', 'Palmeiras'), ('spfc', 'SPFC'),
    ('botafogo', 'Botafogo'), ('fluminense', 'Fluminense'), ('gremio', 'Grêmio'),
    ('internacional', 'Internacional'), ('vasco', 'Vasco'), ('athletico_pr', 'Athletico-PR'),
    ('corinthians', 'Corinthians'), ('cruzeiro', 'Cruzeiro'), ('bahia', 'Bahia'),
    ('fortaleza', 'Fortaleza'), ('ceara', 'Ceará'), ('sport', 'Sport'), ('goias', 'Goiás'),
    ('atletico_go', 'Atlético-GO'), ('cuiaba', 'Cuiabá'), ('botafogo_sp', 'Botafogo-SP'),
    ('novorizontino', 'Novorizontino'), ('paysandu', 'Paysandu'), ('remo', 'Remo'),
    ('chapecoense', 'Chapecoense'), ('abc', 'ABC'), ('criciuma', 'Criciúma'), ('operario', 'Operário'),
    ('avai', 'Avaí'), ('csa', 'CSA'), ('ituano', 'Ituano'), ('sampaio', 'Sampaio'),
    ('mirassol', 'Mirassol')))

SKINS = SKINS + FANTASIAS_SKINS + TIMES_SKINS
POR_ID = {s.id: s for s in SKINS}
POR_CATEGORIA = {c: tuple(s for s in SKINS if s.categoria == c) for c in CATEGORIAS}
SKIN_PADRAO = 'classico'
