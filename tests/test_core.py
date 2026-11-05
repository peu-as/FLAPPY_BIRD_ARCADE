import pygame
import pytest

from flappy_arcade.core.display import calcular_viewport
from flappy_arcade.core.scene import Scene, SceneManager


class CenaRegistro(Scene):
    def __init__(self, nome, log, overlay=False):
        super().__init__(ctx=None)
        self.nome, self.log, self.is_overlay = nome, log, overlay

    def on_enter(self):
        self.log.append(f'entra {self.nome}')

    def on_exit(self):
        self.log.append(f'sai {self.nome}')

    def update(self, dt):
        self.log.append(f'update {self.nome}')

    def draw(self, surface):
        self.log.append(f'draw {self.nome}')


def test_pilha_de_cenas():
    log = []
    m = SceneManager()
    m.push(CenaRegistro('jogo', log))
    m.push(CenaRegistro('pausa', log, overlay=True))
    m.update(0.03)
    m.draw(None)
    assert log == ['entra jogo', 'sai jogo', 'entra pausa',
                   'update pausa', 'draw jogo', 'draw pausa']
    log.clear()
    m.pop()
    assert log == ['sai pausa', 'entra jogo']
    log.clear()
    m.replace(CenaRegistro('menu', log))
    assert log == ['sai jogo', 'entra menu'] and m.top.nome == 'menu'
    m.clear()
    assert m.empty


def test_cena_opaca_esconde_as_de_baixo():
    log = []
    m = SceneManager()
    m.push(CenaRegistro('a', log))
    m.push(CenaRegistro('b', log))
    log.clear()
    m.draw(None)
    assert log == ['draw b']


def test_viewport_sem_distorcao():
    assert calcular_viewport((575, 860)) == pygame.Rect(0, 0, 575, 860)
    larga = calcular_viewport((1600, 860))          # janela larga: faixas nas laterais
    assert larga.h == 860 and larga.w == 575 and larga.x == (1600 - 575) // 2
    alta = calcular_viewport((575, 1200))           # janela alta: faixas em cima e embaixo
    assert alta.w == 575 and alta.y == (1200 - 860) // 2


def test_cache_de_fontes_sobrevive_a_religar_o_pygame():
    """Sem a limpeza automática, reusar uma fonte de antes do pygame.quit derruba o Python."""
    from flappy_arcade.ui.theme import Fonts
    from flappy_arcade.ui.widgets import _CACHE_TEXTO, texto
    pygame.init()
    texto('ANTES', 30)
    assert Fonts._cache and _CACHE_TEXTO
    pygame.quit()
    assert not Fonts._cache and not _CACHE_TEXTO
    pygame.init()
    pygame.display.set_mode((575, 860))
    assert texto('DEPOIS', 30).get_width() > 0


@pytest.mark.parametrize('plataforma, esperado', [
    ('win32', ('Local', 'FlappyBird', 'data', 'save.json')),
    ('darwin', ('Application Support', 'FlappyBird', 'data', 'save.json')),
    ('linux', ('share', 'FlappyBird', 'data', 'save.json')),
])
def test_executavel_guarda_o_save_na_pasta_do_usuario(monkeypatch, tmp_path, plataforma, esperado):
    """Empacotado (PyInstaller), o save vai para a pasta de dados do sistema, não para junto do .exe."""
    import importlib
    import sys
    from flappy_arcade.core import paths
    monkeypatch.delenv('FLAPPY_DATA_DIR', raising=False)
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path / 'pacote'), raising=False)
    monkeypatch.setattr(sys, 'platform', plataforma)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'AppData' / 'Local'))
    monkeypatch.delenv('XDG_DATA_HOME', raising=False)
    monkeypatch.setenv('HOME', str(tmp_path))
    try:
        recarregado = importlib.reload(paths)
        assert recarregado.ARQUIVO_SAVE.parts[-4:] == esperado
        assert recarregado.IMAGENS == tmp_path / 'pacote' / 'assets' / 'imgs'
    finally:
        monkeypatch.undo()
        importlib.reload(paths)
