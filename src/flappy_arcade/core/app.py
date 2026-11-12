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
from ..ui.theme import Motion
from ..gameplay.resources import Recursos
from ..scenes.main_menu import MainMenuScene
from ..systems.audio_manager import AudioManager
from ..systems.economy import Carteira
from ..systems.progress import ProgressStore
from ..systems.save_manager import SaveManager
from ..systems.scenarios import ColecaoCenarios
from ..systems.settings_store import SettingsStore
from ..systems.shop import Loja
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
    wallet: Carteira
    shop: Loja
    scenarios: ColecaoCenarios


class App:
    def __init__(self):
        pygame.init()
        self.window = Window(TITULO)
        recursos = Recursos()           # precisa da janela criada (convert_alpha)
        self.window.set_icon(recursos.icone_janela())
        bus = EventBus()
        save = SaveManager(ARQUIVO_SAVE)
        save.load()
        settings = SettingsStore(save, bus)
        carteira = Carteira(save, bus)
        self.ctx = AppContext(
            window=self.window, resources=recursos, save=save, settings=settings,
            audio=AudioManager(settings, recursos.sons, bus), bus=bus,
            clock=GameClock(), scenes=SceneManager(), progress=ProgressStore(save, bus),
            wallet=carteira, shop=Loja(save, carteira, bus),
            scenarios=ColecaoCenarios(save, carteira, bus))
        self.tela = pygame.Surface((LARGURA, ALTURA))
        self._topo = None              # cena do topo no quadro anterior
        self._foto = None              # último quadro da cena anterior (transição)
        self._foto_inicio = 0

    def run(self, cena_inicial=None, max_quadros=None):
        """Roda até a pilha de cenas esvaziar. max_quadros serve aos testes."""
        cenas = self.ctx.scenes
        cenas.push(cena_inicial or MainMenuScene(self.ctx))
        relogio = pygame.time.Clock()
        quadros = 0
        try:
            while not cenas.empty and (max_quadros is None or quadros < max_quadros):
                dt = min(relogio.tick(cenas.top.fps) / 1000, DT_MAXIMO)
                self._tratar_eventos()
                if cenas.empty:
                    break
                cenas.update(dt)
                if cenas.empty:
                    break
                self._iniciar_transicao_se_mudou()
                cenas.draw(self.tela)
                self._desenhar_transicao()
                self.window.present(self.tela)
                quadros += 1
        finally:
            cenas.clear()
            pygame.quit()
        return quadros

    def _iniciar_transicao_se_mudou(self):
        """A tela do topo mudou: guarda o último quadro (ainda em self.tela) para dissolver."""
        topo = self.ctx.scenes.top
        if topo is not self._topo:
            if self._topo is not None and self.ctx.settings.visual_fx_enabled:
                self._foto = self.tela.copy()
                self._foto_inicio = pygame.time.get_ticks()
            self._topo = topo

    def _desenhar_transicao(self):
        if self._foto is None:
            return
        t = (pygame.time.get_ticks() - self._foto_inicio) / Motion.SCENE_FADE_MS
        if t >= 1:
            self._foto = None
            return
        self._foto.set_alpha(round(255 * (1 - t)))
        self.tela.blit(self._foto, (0, 0))

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
