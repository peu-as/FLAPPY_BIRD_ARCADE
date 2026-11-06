"""Jornada Arcade (história): tabela, sessões por casa, mapa e tela da casa."""
import pygame
import pytest

from scenarios import FakeClock

from flappy_arcade.config.constants import ALTURA, LARGURA
from flappy_arcade.config.levels import (
    CAPITULOS,
    CASAS,
    INTERVALO_CHEFE,
    JORNADA,
    NOMES_ESTILOS,
    cor_da_casa,
    etapa_arcade,
    tem_chefe,
)
from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.gameplay.difficulty_curve import CurvaDificuldade
from flappy_arcade.gameplay.level_session import (
    DificuldadeDaCasa,
    DonkeyLevelSession,
    FlappyLevelSession,
    GalagaLevelSession,
    criar_sessao,
)
from flappy_arcade.scenes.level_scene import LevelScene
from flappy_arcade.scenes.map_scene import ALTURA_MUNDO, MapScene
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore

curva = CurvaDificuldade()
ETAPAS = [etapa_arcade(c) for c in range(1, CASAS + 1)]


# ---------------------------------------------------------------- tabela
def test_jornada_tem_5_capitulos_de_5_casas():
    assert len(JORNADA) == len(CAPITULOS) == CASAS // INTERVALO_CHEFE
    assert all(len(linha) == INTERVALO_CHEFE for linha in JORNADA)
    assert [e.capitulo for e in ETAPAS] == [c // INTERVALO_CHEFE + 1 for c in range(CASAS)]


def test_chefao_exatamente_no_fim_de_cada_capitulo():
    assert [e.chefe for e in ETAPAS] == [tem_chefe(c) for c in range(1, CASAS + 1)]


def test_jornada_mistura_os_estilos():
    estilos = [e.estilo for e in ETAPAS]
    assert set(estilos) == set(NOMES_ESTILOS)
    for capitulo in range(1, len(CAPITULOS) + 1):
        assert len({e.estilo for e in ETAPAS if e.capitulo == capitulo}) >= 2
    for a, b, c in zip(estilos, estilos[1:], estilos[2:]):
        assert not (a == b == c), 'mesmo estilo três vezes seguidas'


def test_cor_da_casa_segue_o_capitulo():
    assert cor_da_casa('arcade', 1) == CAPITULOS[0].cor
    assert cor_da_casa('arcade', 25) == CAPITULOS[-1].cor


# ---------------------------------------------------------------- sessões
@pytest.fixture(scope='module')
def servicos(recursos, tmp_path_factory):
    save = SaveManager(tmp_path_factory.mktemp('arcade') / 'save.json')
    save.load()
    bus = EventBus()
    return recursos, AudioManager(SettingsStore(save, bus), recursos.sons, bus)


@pytest.mark.parametrize('casa', range(1, CASAS + 1))
def test_cada_casa_vira_a_sessao_do_seu_estilo(servicos, casa):
    recursos, audio = servicos
    etapa = etapa_arcade(casa)
    s = criar_sessao('arcade', casa, recursos, audio, FakeClock())
    assert s.chefe == etapa.chefe and s.nivel_dificuldade == casa and s.vidas == 3
    if etapa.estilo in ('flappy', 'passaros'):
        assert isinstance(s, FlappyLevelSession) and s.estado == 'JOGO'
        assert s.especial == (etapa.estilo == 'passaros')
        esperado = DificuldadeDaCasa(etapa.chefe).flappy(casa)    # chefão: um degrau acima (Fase 14)
        assert s.params_nivel == esperado
        if etapa.chefe:
            assert esperado['abertura'] <= curva.flappy(casa)['abertura']
        else:
            assert esperado == curva.flappy(casa)
    else:
        classe = {'donkey': DonkeyLevelSession, 'galaga': GalagaLevelSession}[etapa.estilo]
        assert isinstance(s, classe) and s.estado == etapa.estilo.upper()
        fase = s.galaga or s.donkey
        assert fase.cfg['chefe'] == etapa.chefe
        assert {k: v for k, v in fase.cfg.items() if k != 'chefe'} == getattr(curva, etapa.estilo)(casa)


def test_fase_dos_passaros_sem_chefao_na_jornada(servicos):
    recursos, audio = servicos
    casa = next(c for c, e in enumerate(ETAPAS, 1) if e.estilo == 'passaros' and not e.chefe)
    s = criar_sessao('arcade', casa, recursos, audio, FakeClock())
    assert s.passaros and not s.chefe and 'pássaros' in s.objetivo


# ---------------------------------------------------------------- telas
@pytest.fixture
def ctx(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    return modulo_app.App().ctx


def test_progresso_da_jornada_e_separado(ctx):
    ctx.progress.registrar('arcade', 1, 3)
    assert ctx.progress.liberada('arcade', 2)
    assert not ctx.progress.liberada('flappy', 2)


def test_mapa_da_jornada_desenha_do_inicio_ao_fim(ctx):
    for casa in range(1, 12):
        ctx.progress.registrar('arcade', casa, 2)
    cena = MapScene(ctx, 'arcade')
    ctx.scenes.push(cena)
    tela = pygame.Surface((LARGURA, ALTURA))
    alphas = set()
    for rolagem in range(0, ALTURA_MUNDO - ALTURA + 1, 97):          # varre o mapa todo
        cena.rolagem = cena.rolagem_alvo = rolagem
        cena.update(1 / 60)
        cena.draw(tela)
        alphas.add(cena.camada.get_alpha())
    assert any(a not in (None, 0, 255) for a in alphas), 'deveria haver transição entre capítulos'


def test_abertura_da_casa_mostra_capitulo_e_estilo(ctx):
    cena = LevelScene(ctx, 'arcade', 11)
    etapa = etapa_arcade(11)
    assert f'CAPÍTULO {etapa.capitulo}' in cena.subtitulo()
    assert NOMES_ESTILOS[etapa.estilo].upper() in cena.subtitulo()
    assert cena.cor == CAPITULOS[etapa.capitulo - 1].cor
    assert LevelScene(ctx, 'galaga', 3).subtitulo() == 'ESQUADRILHA GALAGA'
