"""Fase 6: menu principal, pausa, configurações, reset, música e transições."""
import wave

import pygame
import pytest

from flappy_arcade.config.constants import ALTURA, LARGURA
from flappy_arcade.core.paths import MUSICA_JOGO, MUSICA_MENU
from flappy_arcade.gameplay.classic_session import ClassicSession
from flappy_arcade.scenes.game_scene import TEXTO_ATALHOS, GameScene
from flappy_arcade.scenes.level_scene import JOGANDO, LevelScene
from flappy_arcade.scenes.main_menu import MainMenuScene
from flappy_arcade.scenes.map_scene import MapScene
from flappy_arcade.scenes.pause_scene import PauseScene
from flappy_arcade.scenes.settings_scene import SettingsScene
from flappy_arcade.systems.save_manager import SaveManager


@pytest.fixture
def app(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    return modulo_app.App()


@pytest.fixture
def ctx(app):
    return app.ctx


def tecla(cena, key, unicode=''):
    cena.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=0, scancode=0))


def quadros(cenas, n, dt=1 / 60):
    """Avança a pilha como a App faz: só o topo é atualizado; todas desenham."""
    tela = pygame.Surface((LARGURA, ALTURA))
    for _ in range(n):
        cenas.update(dt)
        cenas.draw(tela)


def rotulos(cena):
    return [b.rotulo for b in cena.grupo.botoes]


# ---------------------------------------------------------------- pausa
def test_esc_pausa_o_modo_livre_e_congela_a_partida(ctx):
    cenas = ctx.scenes
    jogo = GameScene(ctx, 'livre')
    cenas.push(jogo)
    tecla(jogo, pygame.K_SPACE)                                  # MENU -> JOGO
    quadros(cenas, 10, 1 / 30)
    tecla(jogo, pygame.K_ESCAPE)
    pausa = cenas.top
    assert isinstance(pausa, PauseScene)
    assert rotulos(pausa) == ['CONTINUAR', 'CONFIGURAÇÕES', 'RECOMEÇAR', 'MENU PRINCIPAL']
    antes = (jogo.session.passaro.y, jogo.session.tempo_livre)
    quadros(cenas, 60)
    assert (jogo.session.passaro.y, jogo.session.tempo_livre) == antes
    tecla(pausa, pygame.K_p)                                     # P também continua
    assert cenas.top is jogo
    quadros(cenas, 5, 1 / 30)
    assert jogo.session.passaro.y != antes[0]


def test_perder_o_foco_pausa(ctx):
    jogo = GameScene(ctx, 'livre')
    ctx.scenes.push(jogo)
    tecla(jogo, pygame.K_SPACE)
    jogo.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert isinstance(ctx.scenes.top, PauseScene)


def test_esc_fora_da_partida_volta_e_letras_do_cadastro_nao_pausam(ctx):
    cenas = ctx.scenes
    cenas.push(MainMenuScene(ctx))
    classico = GameScene(ctx, 'classico')
    cenas.push(classico)
    tecla(classico, pygame.K_SPACE)                              # MENU -> CADASTRO
    tecla(classico, pygame.K_p, 'p')
    assert cenas.top is classico and classico.session.nome_digitado.endswith('p')
    tecla(classico, pygame.K_ESCAPE)                             # sai do cadastro (volta ao MENU do clássico)
    tecla(classico, pygame.K_ESCAPE)                             # no MENU, ESC volta ao menu principal
    assert isinstance(cenas.top, MainMenuScene)


def test_recomecar_e_sair_pela_pausa(ctx):
    cenas = ctx.scenes
    cenas.push(MainMenuScene(ctx))
    jogo = GameScene(ctx, 'livre')
    cenas.push(jogo)
    tecla(jogo, pygame.K_SPACE)
    tecla(jogo, pygame.K_ESCAPE)
    cenas.top.grupo.botoes[2].ativar()                           # RECOMEÇAR
    novo = cenas.top
    assert isinstance(novo, GameScene) and novo is not jogo and novo.session.estado == 'MENU'
    tecla(novo, pygame.K_SPACE)
    tecla(novo, pygame.K_ESCAPE)
    cenas.top.grupo.botoes[3].ativar()                           # MENU PRINCIPAL
    assert isinstance(cenas.top, MainMenuScene)


def test_pausa_na_casa_guarda_moedas_sem_contar_duas_vezes(ctx):
    cenas = ctx.scenes
    cenas.push(MapScene(ctx, 'flappy'))
    casa = LevelScene(ctx, 'flappy', 1)
    cenas.push(casa)
    tecla(casa, pygame.K_SPACE)
    assert casa.fase == JOGANDO
    casa.session.coletor.coletadas = 4
    tecla(casa, pygame.K_ESCAPE)
    pausa = cenas.top
    assert rotulos(pausa)[-1] == 'VOLTAR AO MAPA'
    assert ctx.wallet.saldo == 4                                 # a pausa já guardou
    tecla(pausa, pygame.K_ESCAPE)                                # continua
    casa.session.coletor.coletadas = 6
    tecla(casa, pygame.K_ESCAPE)
    cenas.top.grupo.botoes[-1].ativar()                          # VOLTAR AO MAPA
    assert isinstance(cenas.top, MapScene)
    assert ctx.wallet.saldo == 6


def test_barra_do_topo_mostra_o_atalho_certo(ctx):
    assert ClassicSession.TEXTO_ATALHOS == 'P: Pausa | ESC: Sair'    # o original intacto
    assert GameScene(ctx, 'classico').session.TEXTO_ATALHOS == TEXTO_ATALHOS
    assert LevelScene(ctx, 'galaga', 1).session.TEXTO_ATALHOS == TEXTO_ATALHOS


# ---------------------------------------------------------------- configurações
def test_interruptores_mudam_e_gravam(ctx, tmp_path):
    cfg = SettingsScene(ctx)
    ctx.scenes.push(cfg)
    tecla(cfg, pygame.K_RETURN)                                  # Música
    tecla(cfg, pygame.K_DOWN)
    tecla(cfg, pygame.K_RETURN)                                  # Efeitos sonoros
    tecla(cfg, pygame.K_DOWN)
    tecla(cfg, pygame.K_SPACE)                                   # Efeitos visuais
    quadros(ctx.scenes, 30)
    s = ctx.settings
    assert not s.music_enabled and not s.sfx_enabled and not s.visual_fx_enabled
    gravado = SaveManager(tmp_path / 'save.json').load()['settings']
    assert gravado == {'music': False, 'sfx': False, 'visual_fx': False}
    tecla(cfg, pygame.K_ESCAPE)
    assert ctx.scenes.empty


def _com_progresso(ctx):
    ctx.wallet.depositar(500)
    ctx.shop.comprar('azul')
    ctx.shop.equipar('azul')
    ctx.progress.registrar('galaga', 1, 3)
    ctx.save.section('records')['free_best_streak'] = 40
    ctx.settings.set('music', False)


def test_reset_pede_confirmacao_com_foco_em_cancelar(ctx):
    _com_progresso(ctx)
    cfg = SettingsScene(ctx)
    ctx.scenes.push(cfg)
    resetar = rotulos(cfg).index('RESETAR PROGRESSO')
    for _ in range(resetar):
        tecla(cfg, pygame.K_DOWN)
    tecla(cfg, pygame.K_RETURN)
    assert cfg.confirmando
    tecla(cfg, pygame.K_RETURN)                                  # ENTER apressado = CANCELAR
    assert not cfg.confirmando and ctx.wallet.saldo > 0
    tecla(cfg, pygame.K_RETURN)
    tecla(cfg, pygame.K_ESCAPE)                                  # ESC também cancela
    assert not cfg.confirmando and ctx.scenes.top is cfg and ctx.wallet.saldo > 0
    tecla(cfg, pygame.K_RETURN)
    tecla(cfg, pygame.K_RIGHT)
    tecla(cfg, pygame.K_RETURN)                                  # APAGAR
    assert ctx.wallet.saldo == 0
    assert ctx.shop.equipada == 'classico' and not ctx.shop.possui('azul')
    assert ctx.progress.total('galaga') == 0
    assert ctx.save.section('records')['free_best_streak'] == 0
    assert ctx.settings.music_enabled is False                   # configurações mantidas
    quadros(ctx.scenes, 5)


# ---------------------------------------------------------------- menu principal
def test_menu_principal_entra_em_cascata_e_assenta(ctx):
    menu = MainMenuScene(ctx)
    ctx.scenes.push(menu)
    quadros(ctx.scenes, 1)
    assert any(b.rect.x != b.base_x for b in menu.grupo.botoes)      # ainda entrando
    quadros(ctx.scenes, 90)
    assert all(b.rect.x == b.base_x for b in menu.grupo.botoes)


def test_menu_sem_efeitos_visuais_nao_anima(ctx):
    ctx.settings.set('visual_fx', False)
    menu = MainMenuScene(ctx)
    ctx.scenes.push(menu)
    quadros(ctx.scenes, 1)
    assert all(b.rect.x == b.base_x for b in menu.grupo.botoes)


def test_menu_abre_configuracoes_por_cima_e_sair_fecha(ctx):
    menu = MainMenuScene(ctx)
    ctx.scenes.push(menu)
    quadros(ctx.scenes, 90)
    next(b for b in menu.grupo.botoes if b.rotulo == 'CONFIGURAÇÕES').ativar()
    assert isinstance(ctx.scenes.top, SettingsScene) and ctx.scenes.top.is_overlay
    quadros(ctx.scenes, 3)
    tecla(ctx.scenes.top, pygame.K_ESCAPE)
    next(b for b in menu.grupo.botoes if b.rotulo == 'SAIR').ativar()
    assert ctx.scenes.empty


# ---------------------------------------------------------------- música e transição
@pytest.mark.parametrize('arquivo', [MUSICA_MENU, MUSICA_JOGO])
def test_musicas_existem_e_emendam_sem_estalo(arquivo):
    with wave.open(str(arquivo)) as w:
        assert w.getnchannels() == 1 and w.getframerate() == 22050
        assert w.getnframes() / w.getframerate() > 10
        quadros_ = w.readframes(w.getnframes())
    primeiro = int.from_bytes(quadros_[:2], 'little', signed=True)
    ultimo = int.from_bytes(quadros_[-2:], 'little', signed=True)
    assert abs(primeiro - ultimo) < 50


def test_cada_tela_pede_a_sua_musica(ctx):
    audio = ctx.audio
    MainMenuScene(ctx).on_enter()
    assert audio._faixa[0] == MUSICA_MENU
    LevelScene(ctx, 'donkey', 1).on_enter()
    assert audio._faixa[0] == MUSICA_JOGO
    GameScene(ctx, 'classico').on_enter()
    assert audio._faixa is None                                  # o clássico não tem música
    MapScene(ctx, 'galaga').on_enter()
    assert audio._faixa[0] == MUSICA_MENU


def test_transicao_entre_telas(app):
    ctx = app.ctx
    ctx.scenes.push(MainMenuScene(ctx))
    app._iniciar_transicao_se_mudou()
    assert app._foto is None                                     # primeira tela: sem transição
    ctx.scenes.push(MapScene(ctx, 'flappy'))
    app._iniciar_transicao_se_mudou()
    assert app._foto is not None
    app._foto_inicio -= 10_000                                   # o tempo da transição passou
    app._desenhar_transicao()
    assert app._foto is None
    ctx.settings.set('visual_fx', False)
    ctx.scenes.pop()
    app._iniciar_transicao_se_mudou()
    assert app._foto is None                                     # sem efeitos: troca seca
