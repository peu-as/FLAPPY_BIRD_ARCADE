"""Cena que conduz uma sessão de jogo (clássico ou Modo Livre).

A sessão tem as regras e a física; esta cena só faz a ponte com a
arquitetura: repassa eventos, avança o tempo na mesma ordem do loop
original e copia o quadro para a tela lógica.
"""
import pygame

from ..config.constants import ESTADOS_ATIVOS, FPS
from ..core.paths import MUSICA_JOGO
from ..core.scene import Scene
from ..gameplay.classic_session import ClassicSession
from ..gameplay.free_mode import FreeSession
from ..gameplay.scenery import DiretorCenarios
from ..gameplay.skins import SkinVisual
from .pause_scene import PauseScene

TEXTO_ATALHOS = 'P ou ESC: Pausa'

MODOS = {
    'classico': lambda ctx: ClassicSession(ctx.resources, ctx.audio, ctx.clock),
    'livre': lambda ctx: FreeSession(ctx.resources, ctx.audio, ctx.clock, ctx.save),
}


def preparar_recompensas(sessao, ctx):
    """Veste a skin equipada, mostra o saldo atual e põe os cenários do
    jogador (fixo ou playlist) nas sessões novas. O clássico não passa por aqui."""
    efeitos = ctx.settings.visual_fx_enabled
    sessao.preparar_recompensas(skin=SkinVisual(ctx.shop.equipada, ctx.resources),
                                saldo=ctx.wallet.saldo, efeitos=efeitos)
    sessao.preparar_cenarios(DiretorCenarios(ctx.scenarios.ativos(), ctx.resources.cenarios), efeitos)


def quer_pausar(event, sessao):
    """P, ESC ou a janela perdendo o foco, com a partida em andamento."""
    if sessao.estado not in ESTADOS_ATIVOS or sessao.pausado or getattr(sessao, 'resultado', None):
        return False
    if event.type == pygame.WINDOWFOCUSLOST:
        return True
    return event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p)


class GameScene(Scene):
    fps = FPS   # a física é por quadro e foi calibrada a 30 FPS

    def __init__(self, ctx, modo='classico'):
        super().__init__(ctx)
        self.modo = modo
        self.session = MODOS[modo](ctx)
        self.session.TEXTO_ATALHOS = TEXTO_ATALHOS
        self.depositadas = 0          # moedas desta sessão já levadas à carteira
        if modo == 'livre':
            preparar_recompensas(self.session, ctx)

    def on_enter(self):
        if self.modo == 'classico':
            self.ctx.audio.stop_music()          # o original não tem música de fundo
        else:
            self.ctx.audio.play_music(MUSICA_JOGO, volume=0.45)

    def _pausar(self):
        self.manager.push(PauseScene(
            self.ctx, 'MENU PRINCIPAL', ao_sair=self.manager.pop,
            ao_recomecar=lambda: self.manager.replace(GameScene(self.ctx, self.modo))))

    def on_exit(self):
        encerrar = getattr(self.session, 'encerrar', None)
        if encerrar:
            encerrar()
        if self.modo == 'livre':
            # deposita só o que ainda não foi depositado: seguro mesmo que
            # on_exit rode mais de uma vez (ex.: um menu de pausa por cima)
            novas = self.session.moedas_coletadas - self.depositadas
            self.depositadas += novas
            self.ctx.wallet.depositar(novas)

    def handle_event(self, event):
        if quer_pausar(event, self.session):
            self._pausar()
        elif not self.session.tratar_evento(event):
            self.manager.pop()

    def update(self, dt):
        self.session.atualizar(dt, self.ctx.clock.ticks())
        self.session.pos_atualizar()

    def draw(self, surface):
        self.session.desenhar()
        surface.blit(self.session.tela, (0, 0))
