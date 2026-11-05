"""Cena que conduz uma sessão de jogo (clássico ou Modo Livre).

A sessão tem as regras e a física; esta cena só faz a ponte com a
arquitetura: repassa eventos, avança o tempo na mesma ordem do loop
original e copia o quadro para a tela lógica.
"""
from ..config.constants import FPS
from ..core.scene import Scene
from ..gameplay.classic_session import ClassicSession
from ..gameplay.free_mode import FreeSession
from ..gameplay.skins import SkinVisual

MODOS = {
    'classico': lambda ctx: ClassicSession(ctx.resources, ctx.audio, ctx.clock),
    'livre': lambda ctx: FreeSession(ctx.resources, ctx.audio, ctx.clock, ctx.save),
}


def preparar_recompensas(sessao, ctx):
    """Veste a skin equipada e mostra o saldo atual (sessões com moedas)."""
    sessao.preparar_recompensas(skin=SkinVisual(ctx.shop.equipada, ctx.resources),
                                saldo=ctx.wallet.saldo,
                                efeitos=ctx.settings.visual_fx_enabled)


class GameScene(Scene):
    fps = FPS   # a física é por quadro e foi calibrada a 30 FPS

    def __init__(self, ctx, modo='classico'):
        super().__init__(ctx)
        self.modo = modo
        self.session = MODOS[modo](ctx)
        self.depositadas = 0          # moedas desta sessão já levadas à carteira
        if modo == 'livre':
            preparar_recompensas(self.session, ctx)

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
        if not self.session.tratar_evento(event):
            self.manager.pop()

    def update(self, dt):
        self.session.atualizar(dt, self.ctx.clock.ticks())
        self.session.pos_atualizar()

    def draw(self, surface):
        self.session.desenhar()
        surface.blit(self.session.tela, (0, 0))
