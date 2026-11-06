"""Fase 10: cenários comprados dentro das fases Flappy (Modo Livre, mapas, jornada).

O clássico não muda (golden master). Nas sessões novas, o cenário só muda o
desenho e a cor dos canos e do pássaro: a física é a mesma.
"""
import random
import time

import pygame
import pytest

import snapshot
from scenarios import FakeClock

from flappy_arcade.config.constants import LARGURA, TEMPO_TEMA
from flappy_arcade.config.scenarios import CENARIOS, MAX_PLAYLIST, POR_ID
from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.gameplay.classic_session import ClassicSession
from flappy_arcade.gameplay.free_mode import FreeSession
from flappy_arcade.gameplay.scenery import (LIMITE_MEMORIA, QUADROS_TRANSICAO, DiretorCenarios,
                                            GerenciadorCenarios, SessaoComCenarios)
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore

PLAYLIST_CHEIA = [c.id for c in CENARIOS[-MAX_PLAYLIST:]]


@pytest.fixture
def gerenciador(recursos):
    return GerenciadorCenarios(recursos)


def criar_livre(recursos, tmp_path, diretor=None, arquivo='livre.json'):
    bus = EventBus()
    sv = SaveManager(tmp_path / arquivo)
    sv.load()
    clock = FakeClock()
    s = FreeSession(recursos, AudioManager(SettingsStore(sv, bus), recursos.sons, bus), clock, sv)
    s.preparar_recompensas(moedas=False)
    if diretor is not None:
        s.preparar_cenarios(diretor)
    return s, clock


def passo(sessao, clock):
    clock.avancar()
    sessao.atualizar(1 / 30, clock.ticks())
    sessao.desenhar()


# ---------------------------------------------------------------- gerenciador
def test_gerenciador_monta_todos_e_guarda_so_tres(gerenciador):
    for c in CENARIOS:
        fundo = gerenciador.fundo(c.id)
        assert fundo.get_size() == (575, 860)
        assert len(gerenciador.em_memoria) <= LIMITE_MEMORIA
    assert gerenciador.montagens == len(CENARIOS)
    assert gerenciador.fundo(CENARIOS[-1].id) is gerenciador.fundo(CENARIOS[-1].id)
    assert gerenciador.montagens == len(CENARIOS)       # o que está na memória não é remontado


# ---------------------------------------------------------------- diretor
def test_fixo_nunca_troca(gerenciador):
    d = DiretorCenarios(['sakura'], gerenciador)
    tela = pygame.Surface((575, 860))
    for t in range(0, 400, 3):
        d.atualizar(t)
        d.desenhar(tela)
        assert d.atual == 'sakura'
    assert d.trocas == 0 and gerenciador.montagens == 1


def test_aleatorio_troca_a_cada_20s_sem_repetir_e_sem_engasgar(gerenciador):
    d = DiretorCenarios(PLAYLIST_CHEIA, gerenciador, semente=4)
    tela = pygame.Surface((575, 860))
    vistos, anterior = [d.atual], d.atual
    d.desenhar(tela)
    for quadro in range(30 * 20 * 30):                 # 30 trocas, a 30 FPS
        t = quadro / 30
        if d.atualizar(t):
            assert t % TEMPO_TEMA < 1 / 30 + 1e-9      # troca na virada dos 20 s
            assert d.atual != anterior                 # nunca repete o que acabou de passar
            assert d.atual in gerenciador.em_memoria   # já estava pronto: a troca não monta nada
            anterior = d.atual
            vistos.append(d.atual)
        antes = gerenciador.montagens
        d.desenhar(tela)
        assert gerenciador.montagens == antes          # desenhar nunca monta fundo
        assert len(gerenciador.em_memoria) <= LIMITE_MEMORIA
    assert d.trocas == 29 and set(vistos) <= set(PLAYLIST_CHEIA)
    assert len(set(vistos)) >= 10                      # sorteio de verdade, não um vaivém


def test_transicao_dissolve_em_um_segundo_e_some_sem_efeitos(gerenciador):
    tela = pygame.Surface((575, 860))
    d = DiretorCenarios(['bg', 'night'], gerenciador, semente=1)
    d.desenhar(tela)
    d.atualizar(TEMPO_TEMA)
    assert d.transicao == QUADROS_TRANSICAO
    for _ in range(QUADROS_TRANSICAO // 2):
        d.desenhar(tela)
    meio = tela.get_at((LARGURA // 2, 100))
    assert meio not in (gerenciador.fundo('bg').get_at((LARGURA // 2, 100)),
                        gerenciador.fundo('night').get_at((LARGURA // 2, 100)))   # misturado
    for _ in range(QUADROS_TRANSICAO):
        d.desenhar(tela)
    assert d.transicao == 0
    assert tela.get_at((LARGURA // 2, 100)) == gerenciador.fundo(d.atual).get_at((LARGURA // 2, 100))
    d.atualizar(2 * TEMPO_TEMA)
    d.desenhar(tela, efeitos=False)                    # sem efeitos visuais: troca seca
    assert d.transicao == 0


def test_diretor_nao_mexe_no_random_do_jogo(gerenciador):
    random.seed(99)
    estado = random.getstate()
    d = DiretorCenarios(PLAYLIST_CHEIA, gerenciador)
    for t in range(0, 300, 20):
        d.atualizar(t)
    assert random.getstate() == estado


def test_ids_invalidos_viram_o_basico(gerenciador):
    assert DiretorCenarios(['nao_existe'], gerenciador).ids == ['bg']
    assert DiretorCenarios([], gerenciador).atual == 'bg'


# ---------------------------------------------------------------- sessões
def test_classico_nao_tem_cenarios_comprados(recursos):
    assert not issubclass(ClassicSession, SessaoComCenarios)
    assert issubclass(FreeSession, SessaoComCenarios)
    from flappy_arcade.gameplay.level_session import LevelSession
    assert issubclass(LevelSession, SessaoComCenarios)


def test_cenarios_nao_mudam_a_fisica(recursos, tmp_path, monkeypatch):
    """A mesma partida com o ciclo de fundos do original e com 15 cenários sorteados."""
    monkeypatch.setattr(snapshot, 'IGNORADOS', snapshot.IGNORADOS | {
        'diretor', 'efeitos_cenario', 'tema', 'familia', 'cima', 'baixo', 'coletor'})

    def partida(com_cenarios):
        random.seed(57)
        diretor = DiretorCenarios(PLAYLIST_CHEIA, GerenciadorCenarios(recursos), semente=3) if com_cenarios else None
        s, clock = criar_livre(recursos, tmp_path, diretor, arquivo=f'{com_cenarios}.json')
        s.acao_principal()
        hashes = []
        for i in range(1500):
            alvo = next((o for o in s.obstaculos if o.x + o.largura > s.passaro.x), None)
            if alvo and s.passaro.y + 24 > alvo.topo_passagem + alvo.abertura / 2 and s.passaro.vy >= 0:
                s.acao_principal()
            passo(s, clock)
            if i % 50 == 0:
                hashes.append(snapshot.hash_estado(s))
        return hashes, s

    sem, _ = partida(False)
    com, s = partida(True)
    assert s.diretor.trocas >= 2, 'a partida precisa atravessar trocas de cenário para valer'
    assert com == sem


@pytest.mark.parametrize('cenario_id', ['cidade_noturna', 'bg5', 'por_do_sol', 'sakura'])
def test_periodo_decide_canos_e_passaro(recursos, tmp_path, cenario_id):
    s, clock = criar_livre(recursos, tmp_path, DiretorCenarios([cenario_id], GerenciadorCenarios(recursos)))
    s.acao_principal()
    for _ in range(80):
        passo(s, clock)
    periodo = POR_ID[cenario_id].periodo
    assert s.passaro.familia == periodo
    cano = recursos.cano_noite if periodo == 'noite' else recursos.cano_dia
    assert all(o.baixo is cano for o in s.obstaculos if not o.especial)


def test_canos_que_ja_estavam_na_tela_ganham_a_cor_do_cenario(recursos, tmp_path):
    from flappy_arcade.gameplay.level_session import criar_sessao
    from flappy_arcade.systems.settings_store import SettingsStore as _S
    sv = SaveManager(tmp_path / 'casa.json')
    sv.load()
    bus = EventBus()
    s = criar_sessao('flappy', 2, recursos, AudioManager(_S(sv, bus), recursos.sons, bus), FakeClock())
    assert s.obstaculos and s.obstaculos[0].baixo is recursos.cano_dia
    s.preparar_cenarios(DiretorCenarios(['galaxia'], GerenciadorCenarios(recursos)))
    assert s.obstaculos[0].baixo is recursos.cano_noite


def test_nome_do_cenario_cabe_na_barra_do_topo(recursos, tmp_path):
    s, _ = criar_livre(recursos, tmp_path)
    espaco = (LARGURA - 220) - 165 - 8          # entre o rótulo do tema e o texto de pausa
    for c in CENARIOS:
        assert s.fonte.size(c.nome)[0] <= espaco, c.nome


def test_desempenho_com_15_cenarios(recursos, tmp_path):
    """Quadro inteiro do Modo Livre com 15 cenários e trocas: folgado para 30 FPS."""
    s, clock = criar_livre(recursos, tmp_path, DiretorCenarios(PLAYLIST_CHEIA, GerenciadorCenarios(recursos)))
    s.acao_principal()
    s.tempo_ativo = TEMPO_TEMA - 1
    inicio = time.perf_counter()
    for i in range(300):
        s.passaro.y, s.passaro.vy = 380, 0           # não deixa cair: só medir o desenho
        passo(s, clock)
    por_quadro = (time.perf_counter() - inicio) / 300
    assert s.diretor.trocas >= 1
    assert por_quadro < 1 / 30 / 2, f'{por_quadro * 1000:.1f} ms por quadro'


# ---------------------------------------------------------------- cenas
@pytest.fixture
def ctx(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    return modulo_app.App().ctx


def test_cenas_usam_os_cenarios_do_jogador(ctx):
    from flappy_arcade.scenes.game_scene import GameScene
    from flappy_arcade.scenes.level_scene import LevelScene
    ctx.wallet.depositar(5000)
    for c in ('praia', 'night', 'sakura'):
        ctx.scenarios.comprar(c)
    ctx.scenarios.usar_fixo('praia')
    assert GameScene(ctx, 'livre').session.diretor.ids == ['praia']
    ctx.scenarios.definir_modo('aleatorio')
    assert LevelScene(ctx, 'flappy', 1).session.diretor.ids == ['bg', 'praia', 'night', 'sakura']
    assert GameScene(ctx, 'classico').session.__class__ is ClassicSession
