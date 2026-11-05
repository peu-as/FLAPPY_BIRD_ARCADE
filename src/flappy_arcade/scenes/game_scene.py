"""Cena que conduz uma sessão de jogo (clássico ou Modo Livre).

A sessão tem as regras e a física; esta cena só faz a ponte com a
arquitetura: repassa eventos, avança o tempo na mesma ordem do loop
original e copia o quadro para a tela lógica.
"""
from ..config.constants import FPS
from ..core.scene import Scene
from ..gameplay.classic_session import ClassicSession
from ..gameplay.free_mode import FreeSession

MODOS = {
    'classico': lambda ctx: ClassicSession(ctx.resources, ctx.audio, ctx.clock),
    'livre': lambda ctx: FreeSession(ctx.resources, ctx.audio, ctx.clock, ctx.save),
}


class GameScene(Scene):
    fps = FPS   # a física é por quadro e foi calibrada a 30 FPS

    def __init__(self, ctx, modo='classico'):
        super().__init__(ctx)
        self.modo = modo
        self.session = MODOS[modo](ctx)

    def on_exit(self):
        encerrar = getattr(self.session, 'encerrar', None)
        if encerrar:
            encerrar()

    def handle_event(self, event):
        if not self.session.tratar_evento(event):
            self.manager.pop()

    def update(self, dt):
        self.session.atualizar(dt, self.ctx.clock.ticks())
        self.session.pos_atualizar()

    def draw(self, surface):
        self.session.desenhar()
        surface.blit(self.session.tela, (0, 0))
