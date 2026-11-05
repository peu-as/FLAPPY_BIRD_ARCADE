"""A aplicação completa sobe, joga, responde ao mouse e à janela, e fecha."""
import pygame

from flappy_arcade.core.app import App


def test_app_roda_e_fecha(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    app = App()
    eventos = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=' ', mod=0, scancode=0),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode='A', mod=0, scancode=0),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode='\r', mod=0, scancode=0),
        pygame.event.Event(pygame.VIDEORESIZE, w=1200, h=700, size=(1200, 700)),
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(600, 400)),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, unicode='s', mod=0, scancode=0),
    ]
    for e in eventos:
        pygame.event.post(e)
    sessao = None

    from flappy_arcade.scenes.game_scene import GameScene

    class Espiao(GameScene):
        def update(self, dt):
            nonlocal sessao
            sessao = self.session
            super().update(dt)

    quadros = app.run(Espiao(app.ctx), max_quadros=40)
    assert quadros == 40
    assert sessao.estado == 'JOGO' and sessao.jogador == 'A'
    assert app.window.viewport.h == 700                     # letterbox aplicado
    assert app.ctx.settings.sfx_enabled is False            # tecla S gravou no save
    assert (tmp_path / 'save.json').exists()


def test_esc_na_tela_de_modos_fecha_o_jogo(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    app = App()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode='', mod=0, scancode=0))
    assert app.run(max_quadros=500) == 0
