"""Identidade visual: a única fonte de cores, medidas e tempos da interface.

As cores foram extraídas dos próprios sprites do jogo (céu, canos, chão, pássaro
e logotipo), para que menu, mapa, loja e configurações pareçam parte do mesmo
universo. Nenhuma tela deve usar uma cor RGB solta: use Palette.<NOME>.

Direção de arte para as próximas fases:
  * contorno escuro e grosso (INK), como nos sprites originais;
  * superfícies em creme (PANEL, mesma cor da moldura do placar) com sombra
    sólida deslocada, sem desfoque, no estilo pixel art;
  * verde do cano para ações principais, amarelo do pássaro para destaques e
    moedas, vermelho só para perigo e para o "Resetar progresso".
"""
import pygame


class Palette:
    # Céu e cenário
    SKY = (78, 192, 202)            # céu diurno (bg.png)
    SKY_DEEP = (40, 110, 130)
    SAND = (216, 216, 144)          # chão (base.png)
    GRASS = (112, 184, 40)
    GRASS_LIGHT = (152, 224, 88)

    # Canos: ação principal / botões
    PIPE = (80, 128, 32)
    PIPE_MID = (160, 192, 88)
    PIPE_LIGHT = (216, 240, 128)

    # Pássaro: destaques, moedas, seleção
    BIRD_YELLOW = (248, 176, 48)
    BIRD_ORANGE = (224, 128, 40)
    BIRD_CREAM = (248, 208, 136)
    COIN = (248, 200, 40)
    COIN_SHADE = (200, 140, 20)

    # Tipografia e contornos
    INK = (80, 56, 64)              # contorno de todos os sprites originais
    WHITE = (248, 248, 248)
    LOGO_GREEN = (88, 216, 88)

    # Painéis (moldura.png)
    PANEL = (208, 208, 128)
    PANEL_LIGHT = (240, 232, 144)
    PANEL_SHADE = (200, 152, 56)

    # Estados
    DANGER = (248, 56, 0)
    SUCCESS = (88, 216, 88)
    LOCKED = (120, 112, 120)

    # Fundos de sobreposição
    LETTERBOX = (34, 26, 30)        # faixas laterais quando a janela não tem a proporção do jogo
    DIM = (20, 14, 18, 160)         # escurecer o jogo atrás da pausa


class Metrics:
    OUTLINE = 3          # espessura do contorno (px lógicos)
    SHADOW = 5           # deslocamento da sombra sólida
    RADIUS = 10          # cantos arredondados de painéis e botões
    GUTTER = 24          # margem lateral padrão
    BUTTON_HEIGHT = 64


class Motion:
    HOVER_MS = 120       # crescer/clarear do botão sob o mouse
    PRESS_MS = 80
    SCENE_FADE_MS = 220  # transição entre telas
    HOVER_SCALE = 1.06


class Fonts:
    """Fontes em cache: criar Font a cada quadro é caro."""

    _cache = {}

    @classmethod
    def get(cls, tamanho):
        if tamanho not in cls._cache:
            cls._cache[tamanho] = pygame.font.Font(None, tamanho)
        return cls._cache[tamanho]
