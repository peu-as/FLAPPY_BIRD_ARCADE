"""Cena que conduz o jogo clássico completo (ClassicSession).

A sessão continua com as mesmas regras e a mesma física do original; esta
cena só faz a ponte com a arquitetura nova: repassa eventos, avança o tempo
na mesma ordem do loop antigo e copia o quadro para a tela lógica.
"""
from ..config.constants import FPS
from ..core.scene import Scene
from ..gameplay.classic_session import ClassicSession


class GameScene(Scene):
    fps = FPS   # a física é por quadro e foi calibrada a 30 FPS

    def __init__(self, ctx):
        super().__init__(ctx)
        self.session = ClassicSession(ctx.resources, ctx.audio, ctx.clock)

    def handle_event(self, event):
        if not self.session.tratar_evento(event):
            self.manager.pop()

    def update(self, dt):
        self.session.atualizar(dt, self.ctx.clock.ticks())
        self.session.pos_atualizar()

    def draw(self, surface):
        self.session.desenhar()
        surface.blit(self.session.tela, (0, 0))
