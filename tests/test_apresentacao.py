"""Modo Apresentação (Ctrl + Shift + A no menu): tudo liberado, e o jogo de verdade intacto."""
import json

import pygame
import pytest

from flappy_arcade.config.levels import CASAS, MAPAS
from flappy_arcade.config.scenarios import CENARIOS
from flappy_arcade.config.skins import SKINS
from flappy_arcade.systems import apresentacao


@pytest.fixture
def app(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    import flappy_arcade.systems.ranking as ranking
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    monkeypatch.setattr(ranking, 'ARQUIVO_RANKING', tmp_path / 'ranking.json')
    return modulo_app.App()


def atalho(ctrl=True, shift=True, key=pygame.K_a):
    mod = (pygame.KMOD_LCTRL if ctrl else 0) | (pygame.KMOD_RSHIFT if shift else 0)
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod, unicode='a', scancode=4)


def no_disco(ctx):
    return json.loads(ctx.save.caminho.read_text(encoding='utf-8'))


def test_so_ctrl_shift_a_e_o_atalho():
    assert apresentacao.eh_atalho(atalho())
    assert not apresentacao.eh_atalho(atalho(ctrl=False))
    assert not apresentacao.eh_atalho(atalho(shift=False))
    assert not apresentacao.eh_atalho(atalho(key=pygame.K_b))
    assert not apresentacao.eh_atalho(pygame.event.Event(pygame.KEYUP, key=pygame.K_a, mod=pygame.KMOD_CTRL | pygame.KMOD_SHIFT))


def test_ligado_libera_tudo(app):
    ctx = app.ctx
    assert not ctx.progress.liberada('donkey', 2)
    apresentacao.ligar(ctx)
    assert apresentacao.ligado()
    for mapa in MAPAS:
        assert all(ctx.progress.liberada(mapa, casa) for casa in range(1, CASAS + 1))
        assert ctx.progress.total(mapa) == 0                       # abertas, mas sem estrelas
    assert ctx.wallet.saldo == apresentacao.MOEDAS
    assert all(ctx.shop.possui(s.id) for s in SKINS)
    assert all(ctx.scenarios.possui(c.id) for c in CENARIOS)


def test_o_jogo_de_verdade_fica_intacto(app):
    ctx = app.ctx
    ctx.wallet.depositar(37)
    ctx.progress.registrar('flappy', 1, 2)
    antes_memoria = json.dumps(ctx.save.data, sort_keys=True)
    antes_disco = no_disco(ctx)
    apresentacao.ligar(ctx)
    ctx.wallet.gastar(500)                                         # tudo isso só na memória
    ctx.progress.registrar('galaga', 7, 3)
    ctx.shop.equipar(SKINS[-1].id)
    ctx.scenarios.usar_fixo(CENARIOS[-1].id)
    ctx.save.reset_progress()
    assert no_disco(ctx) == antes_disco
    apresentacao.desligar(ctx)
    assert not apresentacao.ligado()
    assert json.dumps(ctx.save.data, sort_keys=True) == antes_memoria
    assert ctx.wallet.saldo == 37 and ctx.progress.estrelas('flappy', 1) == 2
    assert ctx.progress.estrelas('galaga', 7) == 0 and not ctx.progress.liberada('galaga', 8)
    assert no_disco(ctx) == antes_disco
    ctx.wallet.depositar(1)                                        # e o save real volta a gravar
    assert no_disco(ctx)['wallet']['coins'] == 38


def test_configuracoes_valem_nos_dois_perfis(app):
    ctx = app.ctx
    apresentacao.ligar(ctx)
    ctx.settings.set('music', False)
    apresentacao.desligar(ctx)
    assert ctx.settings.get('music') is False and no_disco(ctx)['settings']['music'] is False


def test_mantem_a_skin_e_os_cenarios_escolhidos(app):
    ctx = app.ctx
    ctx.wallet.depositar(100_000)
    ctx.shop.comprar(SKINS[5].id)
    ctx.shop.equipar(SKINS[5].id)
    ctx.scenarios.comprar(CENARIOS[3].id)
    modo, playlist = ctx.scenarios.modo, ctx.scenarios.playlist
    apresentacao.ligar(ctx)
    assert ctx.shop.equipada == SKINS[5].id
    assert ctx.scenarios.modo == modo and ctx.scenarios.playlist == playlist


def test_ranking_do_classico_nao_e_gravado(app, tmp_path):
    from flappy_arcade.systems import ranking
    apresentacao.ligar(app.ctx)
    assert ranking.salvar_ranking([{'nome': 'PROF', 'pontos': 99, 'data': '', 'nivel': 1, 'zerou': False}], 'PROF')
    assert not (tmp_path / 'ranking.json').exists()
    apresentacao.desligar(app.ctx)
    ranking.salvar_ranking([], 'ANA')
    assert (tmp_path / 'ranking.json').exists()


def test_ligar_e_desligar_duas_vezes_nao_faz_mal(app):
    ctx = app.ctx
    apresentacao.ligar(ctx)
    apresentacao.ligar(ctx)
    apresentacao.desligar(ctx)
    apresentacao.desligar(ctx)
    assert not apresentacao.ligado() and ctx.wallet.saldo == 0 and ctx.save.gravavel


def test_atalho_no_menu_liga_mostra_e_desliga(app):
    from flappy_arcade.scenes.main_menu import MainMenuScene
    ctx = app.ctx
    menu = MainMenuScene(ctx)
    ctx.scenes.push(menu)
    tela = pygame.Surface((575, 860))

    def combina3():
        return next(b for b in menu.grupo.botoes if b.rotulo == 'COMBINA 3')
    assert not combina3().habilitado
    menu.handle_event(atalho())
    assert apresentacao.ligado() and combina3().habilitado and 'TUDO LIBERADO' in menu.aviso[0]
    for _ in range(20):
        menu.update(1 / 60)
        menu.draw(tela)
    combina3().acao()
    assert ctx.scenes.top.mapa == 'combina3'
    ctx.scenes.pop()
    menu.handle_event(atalho())
    assert not apresentacao.ligado() and not combina3().habilitado and 'SEU JOGO' in menu.aviso[0]
    menu.handle_event(atalho(shift=False))                         # Ctrl + A sozinho não faz nada
    assert not apresentacao.ligado()


def test_mapa_mostra_todas_as_casas_abertas(app):
    from flappy_arcade.scenes.level_scene import LevelScene
    from flappy_arcade.scenes.map_scene import MapScene
    ctx = app.ctx
    apresentacao.ligar(ctx)
    mapa = MapScene(ctx, 'donkey')
    ctx.scenes.push(mapa)
    tela = pygame.Surface((575, 860))
    mapa.update(1 / 60)
    mapa.draw(tela)
    ctx.scenes.push(LevelScene(ctx, 'donkey', 25))                 # a última casa abre direto
    ctx.scenes.top.update(1 / 30)
    ctx.scenes.top.draw(tela)


def test_atalhos_de_teste_valem_no_modo_livre(app):
    from flappy_arcade.scenes.game_scene import GameScene

    def apertar_g():
        cena = GameScene(app.ctx, 'livre')
        app.ctx.scenes.push(cena)
        s = cena.session
        s.acao_principal()
        assert s.estado == 'JOGO'
        cena.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g, mod=0, unicode='g', scancode=10))
        app.ctx.scenes.pop()
        return s.estado
    assert apertar_g() == 'JOGO'                                   # jogador comum: G não faz nada
    apresentacao.ligar(app.ctx)
    assert apertar_g() == 'ALERTA'                                 # apresentação: G chama a Galaga
