"""Fase 14: decisões de balanceamento (chefões do Flappy) e economia recalibrada."""
import pytest
from scenarios import FakeClock

from flappy_arcade.config.difficulty_profiles import NIVEIS
from flappy_arcade.config.economy import (BONUS_POR_SEQUENCIA, SEQUENCIA_PARA_BONUS, bonus_por_estrela)
from flappy_arcade.config.levels import (CASAS, ORDEM_MAPAS, CHEFE_ABERTURA_A_FRENTE, OSCILACAO_CHEFE_MAXIMA, meta_chefe_flappy,
                                         meta_flappy, tem_chefe)
from flappy_arcade.config.scenarios import CENARIOS
from flappy_arcade.config.skins import SKINS
from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.gameplay.difficulty import desvio_maximo_passagem
from flappy_arcade.gameplay.difficulty_curve import CurvaDificuldade
from flappy_arcade.gameplay.free_mode import FreeSession
from flappy_arcade.gameplay.level_session import DificuldadeDaCasa
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore

CURVA = CurvaDificuldade()
CHEFOES = [c for c in range(1, CASAS + 1) if tem_chefe(c)]


# ---------------------------------------------------------------- chefões do Flappy
def test_casas_comuns_seguem_a_curva():
    comum = DificuldadeDaCasa(chefe=False)
    for n in range(1, NIVEIS + 1):
        assert comum.flappy(n) == CURVA.flappy(n)


@pytest.mark.parametrize('casa', CHEFOES)
def test_chefao_e_um_degrau_acima(casa):
    chefe, base = DificuldadeDaCasa(chefe=True).flappy(casa), CURVA.flappy(casa)
    assert chefe['abertura'] == CURVA.flappy(min(NIVEIS, casa + CHEFE_ABERTURA_A_FRENTE))['abertura']
    assert chefe['abertura'] <= base['abertura']
    assert base['oscilacao_passaros'] <= chefe['oscilacao_passaros'] <= OSCILACAO_CHEFE_MAXIMA
    for chave in ('gravidade', 'velocidade'):                 # o resto é o da própria casa
        assert chefe[chave] == base[chave]


@pytest.mark.parametrize('casa', CHEFOES)
def test_chefao_continua_justo(recursos, casa):
    """A mesma conta de justiça das casas comuns, com a passagem e a oscilação do chefão."""
    from flappy_arcade.gameplay.flappy import Passaro
    p = DificuldadeDaCasa(chefe=True).flappy(casa)
    sprite = recursos.passaros['dia'][0]
    passaro = Passaro(recursos)
    passaro.aplicar_dificuldade(p['gravidade'])
    desvio = desvio_maximo_passagem(p['abertura'], p['velocidade'], passaro.gravidade, passaro.impulso,
                                    recursos.cano_dia.get_width(), sprite.get_width(), sprite.get_height())
    assert desvio - 2 * p['oscilacao_passaros'] >= 100, f'casa {casa}: folga {desvio}'
    assert p['abertura'] >= 3.5 * sprite.get_height()


def test_meta_do_chefao_cresce_e_supera_as_vizinhas():
    metas = [meta_chefe_flappy(c) for c in CHEFOES]
    assert metas == sorted(metas)
    for c in CHEFOES:
        assert meta_chefe_flappy(c) > meta_flappy(min(CASAS, c + 1))


# ---------------------------------------------------------------- economia
def test_mapas_pagam_menos_da_metade_da_loja():
    """Fase 18: os cinco mapas do menu (com o Estilingue e o Combina 3) e a jornada Arcade, com 3
    estrelas, pagam ~39% da loja em bônus; com as moedas coletadas, ~45%. O resto vem do Modo Livre."""
    loja = sum(s.preco for s in SKINS) + sum(c.preco for c in CENARIOS)
    trilhas = len(ORDEM_MAPAS) + 1                                                   # + a jornada Arcade
    assert trilhas == 6
    estrelas = trilhas * sum(3 * bonus_por_estrela(c) for c in range(1, CASAS + 1))
    assert 0.3 <= estrelas / loja <= 0.42, f'{estrelas} de {loja}'


def test_primeiras_casas_ja_compram_uma_fantasia_simples():
    mais_barata = min(s.preco for s in SKINS if s.preco and s.categoria == 'fantasias')
    assert sum(3 * bonus_por_estrela(c) for c in (1, 2)) >= mais_barata


def _livre(recursos, tmp_path, moedas=True):
    sv = SaveManager(tmp_path / 'livre.json')
    sv.load()
    bus = EventBus()
    s = FreeSession(recursos, AudioManager(SettingsStore(sv, bus), recursos.sons, bus), FakeClock(), sv)
    s.preparar_recompensas(moedas=moedas)
    s.acao_principal()
    return s


def test_bonus_de_sequencia_no_modo_livre(recursos, tmp_path):
    s = _livre(recursos, tmp_path)
    for pontos in range(1, 2 * SEQUENCIA_PARA_BONUS + 1):
        s.pontos = pontos
        s.contar_pontos()
    assert s.moedas_coletadas == 2 * BONUS_POR_SEQUENCIA
    assert any('SEQUÊNCIA' in aviso[3] for aviso in s.coletor.avisos)
    s.sequencia = 0                                    # caiu: a contagem recomeça
    for pontos in range(s.pontos + 1, s.pontos + SEQUENCIA_PARA_BONUS):
        s.pontos = pontos
        s.contar_pontos()
    assert s.moedas_coletadas == 2 * BONUS_POR_SEQUENCIA


def test_sem_moedas_sem_bonus_de_sequencia(recursos, tmp_path):
    s = _livre(recursos, tmp_path, moedas=False)
    s.pontos = 3 * SEQUENCIA_PARA_BONUS
    s.contar_pontos()
    assert s.moedas_coletadas == 0


# ---------------------------------------------------------------- correções da verificação final
def test_vitoria_no_chefao_nao_promete_vida_nos_modos_novos(recursos, tmp_path, monkeypatch):
    from flappy_arcade.gameplay.classic_session import ClassicSession
    from flappy_arcade.gameplay.hud import texto_vidas_extras
    mostradas = []
    monkeypatch.setattr(ClassicSession, 'desenhar_mensagem_fase', lambda self, m: mostradas.append(m))
    mensagem = f'CHEFÃO DERROTADO!\n{texto_vidas_extras()}'
    _livre(recursos, tmp_path).desenhar_mensagem_fase(mensagem)
    assert mostradas[-1] == 'CHEFÃO DERROTADO!'
    sv = SaveManager(tmp_path / 'c.json')
    bus = EventBus()
    classico = ClassicSession(recursos, AudioManager(SettingsStore(sv, bus), recursos.sons, bus), FakeClock())
    classico.desenhar_mensagem_fase(mensagem)
    assert mostradas[-1] == mensagem                           # o clássico continua igual


def test_recorde_continua_sendo_gravado_depois_de_um_reset(recursos, tmp_path):
    s = _livre(recursos, tmp_path)
    s.pontos = 5
    s.contar_pontos()
    s.save.reset_progress()                                    # pausa -> configurações -> resetar
    s.sequencia = 0
    s.pontos = 12
    s.contar_pontos()
    s.gravar_recorde()
    assert SaveManager(tmp_path / 'livre.json').load()['records']['free_best_streak'] == 7
