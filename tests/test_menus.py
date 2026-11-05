"""Telas da Fase 3: escolha de modo, mapa e casa (fluxo completo)."""
import pygame
import pytest

from flappy_arcade.config.constants import ALTURA, LARGURA
from flappy_arcade.config.levels import CASAS
from flappy_arcade.scenes.level_scene import ABERTURA, JOGANDO, RESULTADO, LevelScene
from flappy_arcade.scenes.map_scene import MapScene, posicao_casa
from flappy_arcade.scenes.main_menu import MainMenuScene


@pytest.fixture
def ctx(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    return modulo_app.App().ctx


def tecla(cena, key):
    cena.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode='', mod=0, scancode=0))


def clique(cena, pos):
    cena.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    cena.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))


def quadros(cena, n, dt=1 / 60):
    tela = pygame.Surface((LARGURA, ALTURA))
    for _ in range(n):
        cena.update(dt)
        cena.draw(tela)


def na_tela(mapa_cena, casa):
    x, y = posicao_casa(casa)
    return (x, y - mapa_cena.rolagem)


# ---------------------------------------------------------------- escolha de modo
def test_tela_de_modos(ctx):
    cenas = ctx.scenes
    cenas.push(MainMenuScene(ctx))
    menu = cenas.top
    quadros(menu, 5)
    rotulos = [b.rotulo for b in menu.grupo.botoes]
    assert rotulos[6:] == ['CONFIGURAÇÕES', 'SAIR', 'LOJA']
    assert all(b.habilitado for b in menu.grupo.botoes)
    tecla(menu, pygame.K_RETURN)                                           # 1º botão: Donkey Kong
    assert isinstance(cenas.top, MapScene) and cenas.top.mapa == 'donkey'
    tecla(cenas.top, pygame.K_ESCAPE)
    assert cenas.top is menu
    for _ in range(3):
        tecla(menu, pygame.K_DOWN)
    assert menu.grupo.botoes[menu.grupo.indice].rotulo == 'ARCADE (HISTÓRIA)'
    tecla(menu, pygame.K_RETURN)
    assert isinstance(cenas.top, MapScene) and cenas.top.mapa == 'arcade'


# ---------------------------------------------------------------- mapa
def test_casas_do_mapa_cabem_na_tela_e_sobem_em_ordem():
    posicoes = [posicao_casa(c) for c in range(1, CASAS + 1)]
    assert all(45 <= x <= LARGURA - 45 for x, _ in posicoes)
    assert all(b[1] < a[1] for a, b in zip(posicoes, posicoes[1:]))


@pytest.mark.parametrize('mapa', ['donkey', 'galaga', 'flappy', 'arcade'])
def test_mapa_abre_so_casas_liberadas(ctx, mapa):
    ctx.scenes.push(MapScene(ctx, mapa))
    cena = ctx.scenes.top
    quadros(cena, 90)                                                      # rolagem assenta
    clique(cena, na_tela(cena, 2))                                         # bloqueada
    assert ctx.scenes.top is cena
    tecla(cena, pygame.K_UP)                                               # não seleciona bloqueada
    assert cena.selecionada == 1
    clique(cena, na_tela(cena, 1))
    assert isinstance(ctx.scenes.top, LevelScene) and ctx.scenes.top.casa == 1


def test_arrastar_rola_sem_abrir_casa(ctx):
    ctx.scenes.push(MapScene(ctx, 'flappy'))
    cena = ctx.scenes.top
    quadros(cena, 90)
    x, y = na_tela(cena, 1)
    antes = cena.rolagem
    cena.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y)))
    cena.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(x, y + 200), rel=(0, 200), buttons=(1, 0, 0)))
    cena.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(x, y + 200)))
    assert ctx.scenes.top is cena and cena.rolagem != antes


# ---------------------------------------------------------------- casa
def test_vitoria_grava_estrelas_libera_e_segue(ctx):
    cenas = ctx.scenes
    cenas.push(MapScene(ctx, 'flappy'))
    mapa = cenas.top
    cenas.push(LevelScene(ctx, 'flappy', 1))
    casa = cenas.top
    assert casa.fase == ABERTURA
    quadros(casa, 10, 1 / 30)
    assert casa.session.pontos == 0                                        # parado na abertura
    tecla(casa, pygame.K_SPACE)
    assert casa.fase == JOGANDO
    casa.session.pontos = casa.session.meta
    quadros(casa, 40, 1 / 30)
    assert casa.fase == RESULTADO and casa.session.estrelas == 3
    assert ctx.progress.estrelas('flappy', 1) == 3 and ctx.progress.liberada('flappy', 2)
    assert [b.rotulo for b in casa.grupo.botoes] == ['MAPA', 'DE NOVO', 'PRÓXIMA']
    tecla(casa, pygame.K_RETURN)                                           # ENTER = próxima
    assert isinstance(cenas.top, LevelScene) and cenas.top.casa == 2
    tecla(cenas.top, pygame.K_ESCAPE)                                      # volta ao mapa
    assert cenas.top is mapa and mapa.casa_atual == 2 and 2 in mapa.pop
    quadros(mapa, 30)


def test_derrota_nao_grava_e_oferece_de_novo(ctx):
    cenas = ctx.scenes
    cenas.push(LevelScene(ctx, 'galaga', 1))
    casa = cenas.top
    tecla(casa, pygame.K_SPACE)
    casa.session.galaga.tempo = casa.session.galaga.tempo_limite
    quadros(casa, 90, 1 / 30)
    assert casa.fase == RESULTADO and casa.session.resultado == 'DERROTA'
    assert ctx.progress.estrelas('galaga', 1) == 0
    assert [b.rotulo for b in casa.grupo.botoes] == ['MAPA', 'DE NOVO']
    tecla(casa, pygame.K_r)
    assert cenas.top is not casa and cenas.top.casa == 1 and cenas.top.fase == ABERTURA


@pytest.mark.parametrize('efeitos', [True, False])
@pytest.mark.parametrize('mapa', ['donkey', 'galaga', 'flappy', 'arcade'])
def test_todas_as_telas_desenham(ctx, mapa, efeitos):
    ctx.settings.set('visual_fx', efeitos)
    ctx.progress.registrar(mapa, 1, 2)
    for cena in (MainMenuScene(ctx), MapScene(ctx, mapa), LevelScene(ctx, mapa, 5)):
        ctx.scenes.push(cena)
        quadros(cena, 3)
    casa = ctx.scenes.top
    tecla(casa, pygame.K_SPACE)
    quadros(casa, 60, 1 / 30)
