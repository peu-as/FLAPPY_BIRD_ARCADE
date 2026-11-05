"""Configuração comum: pygame sem janela e sem placa de som, dados em pasta temporária."""
import os
import tempfile

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ.setdefault('FLAPPY_DATA_DIR', tempfile.mkdtemp(prefix='flappy-test-'))

import pygame  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(scope='session')
def pygame_pronto():
    pygame.init()
    pygame.display.set_mode((575, 860))
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def pygame_religado():
    """Os testes do App fecham o pygame ao sair (como o jogo real faz);
    os testes seguintes o encontram ligado de novo."""
    yield
    if not pygame.get_init() or not pygame.font.get_init() or pygame.display.get_surface() is None:
        pygame.init()
        pygame.display.set_mode((575, 860))


@pytest.fixture(scope='session')
def recursos(pygame_pronto):
    from flappy_arcade.gameplay.resources import Recursos
    return Recursos()
