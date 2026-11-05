"""Aplicação: cria os serviços uma única vez e roda o loop principal.

Ordem de cada quadro (a mesma do jogo original):
    1. limita a taxa de quadros da cena do topo e mede dt
    2. trata os eventos (sair, redimensionar, mouse convertido, teclado)
    3. atualiza a cena do topo
    4. desenha a pilha de cenas na tela lógica e apresenta na janela
"""
from dataclasses import dataclass

import pygame

from ..config.constants import ALTURA, LARGURA
from ..gameplay.resources import Recursos
from ..scenes.mode_select import ModeSelectScene
from ..systems.audio_manager import AudioManager
from ..systems.progress import ProgressStore
from ..systems.save_manager import SaveManager
from ..systems.settings_store import SettingsStore
from .clock import GameClock
from .display import Window
from .event_bus import EventBus
from .paths import ARQUIVO_SAVE
from .scene import SceneManager

TITULO = 'Flappy Arcade'
DT_MAXIMO = 0.1   # evita "saltos" de física depois de arrastar a janela


@dataclass
class AppContext:
    """Serviços compartilhados, entregues a todas as cenas."""
    window: Window
    resources: Recursos
    save: SaveManager
    settings: SettingsStore
    audio: AudioManager
    bus: EventBus
    clock: GameClock
    scenes: SceneManager
    progress: ProgressStore


class App:
    def __init__(self):
        pygame.init()
        self.window = Window(TITULO)
        recursos = Recursos()           # precisa da janela criada (convert_alpha)
        self.window.set_icon(recursos.passaros['dia'][0])
        bus = EventBus()
        save = SaveManager(ARQUIVO_SAVE)
        save.load()
        settings = SettingsStore(save, bus)
        self.ctx = AppContext(
            window=self.window, resources=recursos, save=save, settings=settings,
            audio=AudioManager(settings, recursos.sons, bus), bus=bus,
            clock=GameClock(), scenes=SceneManager(), progress=ProgressStore(save, bus))
        self.tela = pygame.Surface((LARGURA, ALTURA))

    def run(self, cena_inicial=None, max_quadros=None):
        """Roda até a pilha de cenas esvaziar. max_quadros serve aos testes."""
        cenas = self.ctx.scenes
        cenas.push(cena_inicial or ModeSelectScene(self.ctx))
        relogio = pygame.time.Clock()
        quadros = 0
        try:
            while not cenas.empty and (max_quadros is None or quadros < max_quadros):
                dt = min(relogio.tick(cenas.top.fps) / 1000, DT_MAXIMO)
                self._tratar_eventos()
                if cenas.empty:
                    break
                cenas.update(dt)
                cenas.draw(self.tela)
                self.window.present(self.tela)
                quadros += 1
        finally:
            cenas.clear()
            pygame.quit()
        return quadros

    def _tratar_eventos(self):
        cenas = self.ctx.scenes
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                cenas.clear()
                return
            if evento.type == pygame.VIDEORESIZE:
                self.window.resize(evento.w, evento.h)
                continue
            evento = self.window.translate_event(evento)
            if evento is None:
                continue
            cenas.handle_event(evento)
            if cenas.empty:
                return
