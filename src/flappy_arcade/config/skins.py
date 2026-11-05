"""Catálogo de skins do pássaro. Só aparência: a colisão nunca muda.

Tipos de skin:
  'paleta'    o pássaro original com as cores trocadas (mantém a animação das asas);
  'especial'  um dos sprites temáticos de assets/imgs (sem animação de asas);
  efeitos     'brilho', 'fantasma', 'neon' ou 'arco_iris' (animados; o rastro
              some quando os efeitos visuais estão desligados).

Faixas de preço: comuns 50 a 100, raras 250 a 500, radicais 1000 ou mais.
"""
from dataclasses import dataclass, field

COMUM, RARA, RADICAL = 'comum', 'rara', 'radical'
NOMES_RARIDADE = {COMUM: 'COMUM', RARA: 'RARA', RADICAL: 'RADICAL'}
CORES_RARIDADE = {COMUM: (120, 168, 72), RARA: (72, 120, 220), RADICAL: (200, 84, 200)}

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
    tipo: str = 'paleta'
    cores: dict = field(default_factory=dict)    # paleta: papel -> cor nova
    sprite: str = ''                             # especial: nome do PNG
    efeito: str = ''


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
POR_ID = {s.id: s for s in SKINS}
SKIN_PADRAO = 'classico'
