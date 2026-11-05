"""Regras das casas dos mapas e do progresso salvo."""
import pygame
import pytest

from scenarios import FakeClock

from flappy_arcade.config.constants import TEMPO_DONKEY
from flappy_arcade.config.levels import CASAS, meta_flappy
from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.gameplay.difficulty_curve import CurvaDificuldade
from flappy_arcade.gameplay.level_session import SESSOES_POR_MAPA
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.progress import ProgressStore
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore

curva = CurvaDificuldade()


@pytest.fixture
def criar(recursos, tmp_path):
    def _criar(mapa, casa):
        bus = EventBus()
        save = SaveManager(tmp_path / 'save.json')
        save.load()
        audio = AudioManager(SettingsStore(save, bus), recursos.sons, bus)
        clock = FakeClock()
        sessao = SESSOES_POR_MAPA[mapa](recursos, audio, clock, casa)

        def passo(n=1):
            for _ in range(n):
                clock.avancar()
                sessao.atualizar(1 / 30, clock.ticks())
                sessao.desenhar()
        return sessao, passo, clock
    return _criar


# ---------------------------------------------------------------- Flappy
def test_flappy_comeca_jogando_com_a_dificuldade_da_casa(criar):
    s, _, _ = criar('flappy', 7)
    assert s.estado == 'JOGO' and s.vidas == 3
    assert s.params_nivel == curva.flappy(7)
    assert s.passaro.gravidade == curva.flappy(7)['gravidade']   # já com a física da casa
    assert s.meta == meta_flappy(7)
    assert 'canos' in s.objetivo


def test_flappy_vence_ao_atingir_a_meta(criar):
    s, passo, _ = criar('flappy', 3)
    s.pontos = s.meta
    passo()
    assert s.resultado == 'VITORIA' and s.estrelas == 3


def test_flappy_perde_com_tres_quedas_e_congela(criar):
    s, passo, _ = criar('flappy', 2)
    passo(900)                               # sem bater asas
    assert s.resultado == 'DERROTA' and s.estrelas == 0 and s.danos == 3
    antes = (s.passaro.y, s.pontos)
    passo(30)
    assert (s.passaro.y, s.pontos) == antes  # sessão congelada


def test_estrelas_pelas_vidas_perdidas(criar):
    s, passo, clock = criar('flappy', 4)
    s.perder_vida(clock.ticks() + 5000)
    s.pontos = s.meta
    passo()
    assert s.estrelas == 2


def test_flappy_casa_de_chefe_e_a_fase_dos_passaros(criar):
    s, _, _ = criar('flappy', 10)
    assert s.chefe and s.especial
    assert s.meta == curva.flappy(10)['pontos_passaros']
    assert 'pássaros' in s.objetivo


# ---------------------------------------------------------------- Galaga e Donkey
@pytest.mark.parametrize('mapa', ['galaga', 'donkey'])
def test_fase_usa_a_curva_da_casa(criar, mapa):
    s, _, _ = criar(mapa, 12)
    fase = s.galaga or s.donkey
    assert s.estado == mapa.upper()
    esperado = getattr(curva, mapa)(12)
    assert {k: v for k, v in fase.cfg.items() if k != 'chefe'} == esperado
    assert fase.cfg['chefe'] is False


def test_galaga_sem_chefe_vence_ao_derrubar_a_formacao(criar):
    s, passo, _ = criar('galaga', 3)
    s.galaga.inimigos = []
    passo(90)                                # mensagem de 2 s e fim
    assert s.resultado == 'VITORIA' and s.galaga.chefe is None


def test_galaga_casa_de_chefe_chama_o_boss(criar):
    s, passo, _ = criar('galaga', 5)
    s.galaga.inimigos = []
    passo()
    assert s.galaga.estagio == 'CHEFE' and s.resultado is None


def test_galaga_tempo_esgotado_perde(criar):
    s, passo, _ = criar('galaga', 2)
    s.galaga.tempo = s.galaga.tempo_limite
    passo(90)
    assert s.resultado == 'DERROTA'


def test_donkey_sem_chefe_vence_ao_atravessar(criar):
    s, passo, _ = criar('donkey', 4)
    s.donkey.tempo = TEMPO_DONKEY
    s.ultimo_dano = 10 ** 9                  # sem dano neste teste
    s.donkey.dano = False
    passo(70)
    assert s.resultado == 'VITORIA'
    assert s.vidas == 3                      # vitória não soma vida nos mapas


def test_donkey_casa_de_chefe_chama_o_kong(criar):
    s, passo, _ = criar('donkey', 15)
    s.donkey.pular_para_chefe()
    passo()
    assert s.donkey.estagio == 'CHEFE' and s.resultado is None


def test_esc_sai_da_casa(criar):
    s, _, _ = criar('donkey', 1)
    sair = s.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode='', mod=0, scancode=0))
    assert sair is False


# ---------------------------------------------------------------- progresso
@pytest.fixture
def progresso(tmp_path):
    save = SaveManager(tmp_path / 'save.json')
    save.load()
    return ProgressStore(save), save, tmp_path


def test_so_a_primeira_casa_comeca_liberada(progresso):
    p, _, _ = progresso
    assert p.liberada('flappy', 1) and not p.liberada('flappy', 2)
    assert not p.liberada('flappy', 0) and not p.liberada('flappy', CASAS + 1)
    assert p.casa_atual('flappy') == 1 and p.total('flappy') == 0


def test_vencer_libera_a_proxima_e_guarda_o_melhor(progresso):
    p, _, pasta = progresso
    assert p.registrar('galaga', 1, 2) == (True, 2)
    assert p.liberada('galaga', 2) and p.casa_atual('galaga') == 2
    assert p.registrar('galaga', 1, 1) == (False, None)      # pior: não troca
    assert p.registrar('galaga', 1, 3) == (True, None)       # melhor: troca, nada novo liberado
    novo = ProgressStore(SaveManager(pasta / 'save.json'))
    novo._save.load()
    assert novo.estrelas('galaga', 1) == 3
    assert not novo.liberada('flappy', 2)                    # mapas são independentes


def test_ultima_casa_nao_libera_alem_do_mapa(progresso):
    p, save, _ = progresso
    save.section('progress')['donkey'] = {'estrelas': [1] * (CASAS - 1) + [0]}
    assert p.registrar('donkey', CASAS, 3) == (True, None)
    assert p.casa_atual('donkey') == CASAS and p.total('donkey') == CASAS - 1 + 3


def test_dados_estragados_no_save_sao_consertados(progresso):
    p, save, _ = progresso
    save.section('progress')['flappy'] = {'estrelas': [3, 'x', 9, -1, True]}
    save.section('progress')['galaga'] = 'lixo'
    assert [p.estrelas('flappy', c) for c in range(1, 6)] == [3, 0, 3, 0, 0]
    assert p.total('galaga') == 0
