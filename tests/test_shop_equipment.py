"""Fase 12: loja com abas e filtros, prévia combinada e tela Equipamentos."""
import pygame
import pytest

from flappy_arcade.config.constants import ALTURA, LARGURA
from flappy_arcade.config.scenarios import CENARIOS, MAX_PLAYLIST, MODO_ALEATORIO, MODO_FIXO
from flappy_arcade.config.skins import POR_CATEGORIA
from flappy_arcade.scenes.equipment_scene import EquipmentScene
from flappy_arcade.scenes.main_menu import MainMenuScene
from flappy_arcade.scenes.shop_scene import CENARIOS_ABA, SKINS_ABA, ShopScene
from flappy_arcade.scenes.vitrine import MINIATURA, MINIATURAS_POR_QUADRO, TAMANHO_PREVIA, VISTAS, FilaMiniaturas
from flappy_arcade.systems.save_manager import SaveManager


@pytest.fixture
def ctx(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    return modulo_app.App().ctx


def tecla(cena, key):
    cena.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode='', mod=0, scancode=0))


def quadros(cena, n, dt=1 / 60):
    tela = pygame.Surface((LARGURA, ALTURA))
    for _ in range(n):
        cena.update(dt)
        cena.draw(tela)
    return tela


def clicar(cena, pos):
    for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        cena.handle_event(pygame.event.Event(tipo, pos=pos, button=1))


def comprar_cenarios(ctx, ids):
    ctx.wallet.depositar(sum(c.preco for c in CENARIOS if c.id in ids))
    for i in ids:
        ctx.scenarios.comprar(i)


# ---------------------------------------------------------------- loja
def test_abas_e_filtros(ctx):
    loja = ShopScene(ctx)
    ctx.scenes.push(loja)
    assert loja.aba == SKINS_ABA and loja.filtro[SKINS_ABA] == 'classicas'
    assert [b.rotulo for b in loja.botoes_filtro] == ['CLÁSSICAS (18)', 'FANTASIAS (35)', 'TIMES (32)']
    tecla(loja, pygame.K_e)
    assert loja.itens == POR_CATEGORIA['fantasias'] and loja.indice == 0
    tecla(loja, pygame.K_e)
    assert loja.itens == POR_CATEGORIA['times']
    tecla(loja, pygame.K_TAB)
    assert loja.aba == CENARIOS_ABA
    assert [b.rotulo for b in loja.botoes_filtro] == ['ORIGINAIS (11)', 'NOVOS (20)']
    assert loja.item.id == 'bg'                                  # começa no cenário em uso
    tecla(loja, pygame.K_TAB)
    assert loja.aba == SKINS_ABA and loja.itens == POR_CATEGORIA['times']   # lembra o filtro
    quadros(loja, 3)


def test_clicar_nas_abas_e_filtros(ctx):
    loja = ShopScene(ctx)
    ctx.scenes.push(loja)
    clicar(loja, loja.abas[CENARIOS_ABA].rect.center)
    assert loja.aba == CENARIOS_ABA
    clicar(loja, loja.botoes_filtro[1].rect.center)
    assert loja.filtro[CENARIOS_ABA] == 'novos' and loja.item.id == 'parque'
    clicar(loja, loja.botoes_vista[2].rect.center)
    assert loja.vitrine.vista == 'donkey'
    tecla(loja, pygame.K_v)
    assert loja.vitrine.vista == 'flappy'


def test_comprar_cenario_no_modo_fixo_ja_usa(ctx):
    ctx.wallet.depositar(700)
    loja = ShopScene(ctx, aba=CENARIOS_ABA)
    ctx.scenes.push(loja)
    loja.trocar_filtro('novos')                                  # Parque, 600
    quadros(loja, 2)
    assert loja.acao.rotulo == 'COMPRAR 600'
    tecla(loja, pygame.K_RETURN)
    quadros(loja, 2)
    assert loja.acao.rotulo == 'CONFIRMAR?' and not ctx.scenarios.possui('parque')
    tecla(loja, pygame.K_RETURN)
    quadros(loja, 2)
    assert ctx.scenarios.possui('parque') and ctx.wallet.saldo == 100
    assert ctx.scenarios.fixo == 'parque' and loja.acao.rotulo == 'EM USO'
    tecla(loja, pygame.K_RIGHT)                                  # Praia: faltam 500
    quadros(loja, 2)
    assert loja.acao.rotulo == 'FALTAM 500' and not loja.acao.habilitado


def test_no_aleatorio_a_loja_poe_e_tira_da_playlist(ctx):
    comprar_cenarios(ctx, ['night'])
    ctx.scenarios.definir_modo(MODO_ALEATORIO)
    loja = ShopScene(ctx, aba=CENARIOS_ABA)
    ctx.scenes.push(loja)
    loja._selecionar([c.id for c in loja.itens].index('night'))
    quadros(loja, 2)
    assert loja.acao.rotulo == 'TIRAR DA PLAYLIST'
    tecla(loja, pygame.K_RETURN)
    assert not ctx.scenarios.na_playlist('night')
    quadros(loja, 2)
    assert loja.acao.rotulo == 'PÔR NA PLAYLIST'
    loja._selecionar(0)                                          # bg, o único que sobrou
    tecla(loja, pygame.K_RETURN)
    assert ctx.scenarios.playlist == ['bg'] and 'pelo menos 1' in loja.aviso[0]


def test_skins_continuam_comprando_e_equipando(ctx):
    ctx.wallet.depositar(200)
    loja = ShopScene(ctx)
    ctx.scenes.push(loja)
    loja.trocar_filtro('times')
    tecla(loja, pygame.K_RIGHT)                                  # Flamengo
    tecla(loja, pygame.K_RETURN)
    tecla(loja, pygame.K_RETURN)
    assert ctx.shop.equipada == 'time_flamengo' and ctx.wallet.saldo == 0
    reaberta = ShopScene(ctx)
    assert reaberta.filtro[SKINS_ABA] == 'times' and reaberta.item.id == 'time_flamengo'


@pytest.mark.parametrize('vista', VISTAS)
def test_previa_combinada_de_todos_os_cenarios(ctx, vista):
    loja = ShopScene(ctx, aba=CENARIOS_ABA)
    loja.ver_em(vista)
    for c in CENARIOS:
        previa = loja.vitrine.fundo(c.id, vista)
        assert previa.get_size() == TAMANHO_PREVIA
    assert len(loja.vitrine._fundos) <= 6
    quadros(loja, 2)


def test_miniaturas_aos_poucos_sem_tirar_os_fundos_da_memoria(ctx):
    g = ctx.resources.cenarios
    g.fundo('bg')
    antes = g.em_memoria
    fila = FilaMiniaturas(g)
    ids = [c.id for c in CENARIOS[:7]]
    assert all(fila.pegar(i) is None for i in ids if not g.tem_miniatura(i, MINIATURA))
    fila.atualizar()
    feitas = sum(g.tem_miniatura(i, MINIATURA) for i in ids)
    assert feitas <= MINIATURAS_POR_QUADRO + 1                   # +1: 'bg' pode já estar pronto
    for _ in range(len(ids)):                                    # MINIATURAS_POR_QUADRO por vez
        fila.atualizar()
    assert all(fila.pegar(i).get_size() == MINIATURA for i in ids)
    assert g.em_memoria == antes


@pytest.mark.parametrize('efeitos', [True, False])
def test_loja_desenha_tudo(ctx, efeitos):
    ctx.settings.set('visual_fx', efeitos)
    comprar_cenarios(ctx, ['praia', 'galaxia'])
    loja = ShopScene(ctx)
    ctx.scenes.push(loja)
    for aba in (SKINS_ABA, CENARIOS_ABA):
        loja.trocar_aba(aba)
        for _ in range(3):
            for vista in VISTAS:
                loja.ver_em(vista)
                quadros(loja, 3)
            tecla(loja, pygame.K_e)


# ---------------------------------------------------------------- equipamentos
def test_menu_abre_os_equipamentos(ctx):
    menu = MainMenuScene(ctx)
    ctx.scenes.push(menu)
    next(b for b in menu.grupo.botoes if b.rotulo == 'EQUIPAMENTOS').ativar()
    assert isinstance(ctx.scenes.top, EquipmentScene)
    quadros(ctx.scenes.top, 5)


def test_fixo_escolhe_pelo_cartao(ctx):
    comprar_cenarios(ctx, ['praia', 'sakura'])
    ctx.scenarios.usar_fixo('bg')
    eq = EquipmentScene(ctx)
    ctx.scenes.push(eq)
    assert [c.id for c in eq.itens] == ['bg', 'praia', 'sakura']      # ordem do catálogo
    quadros(eq, 3)
    tecla(eq, pygame.K_RIGHT)
    tecla(eq, pygame.K_RETURN)
    assert ctx.scenarios.fixo == 'praia' and ctx.scenarios.ativos() == ['praia']
    from flappy_arcade.scenes.equipment_scene import retangulo_cartao
    clicar(eq, retangulo_cartao(2).move(0, -eq.rolagem).center)
    assert ctx.scenarios.fixo == 'sakura'


def test_aleatorio_marca_e_desmarca_e_fica_salvo(ctx, tmp_path):
    comprar_cenarios(ctx, ['praia', 'sakura', 'night'])
    eq = EquipmentScene(ctx)
    ctx.scenes.push(eq)
    tecla(eq, pygame.K_a)
    assert ctx.scenarios.modo == MODO_ALEATORIO
    assert ctx.scenarios.playlist == ['bg', 'praia', 'sakura', 'night']
    eq._selecionar([c.id for c in eq.itens].index('sakura'))
    tecla(eq, pygame.K_RETURN)
    assert not ctx.scenarios.na_playlist('sakura')
    quadros(eq, 3)
    salvo = SaveManager(tmp_path / 'save.json').load()['scenarios']
    assert salvo['mode'] == MODO_ALEATORIO and 'sakura' not in salvo['playlist']
    tecla(eq, pygame.K_f)
    assert ctx.scenarios.modo == MODO_FIXO


def test_playlist_cheia_avisa(ctx):
    comprar_cenarios(ctx, [c.id for c in CENARIOS[1:MAX_PLAYLIST + 2]])
    ctx.scenarios.definir_modo(MODO_ALEATORIO)
    eq = EquipmentScene(ctx)
    ctx.scenes.push(eq)
    assert len(ctx.scenarios.playlist) == MAX_PLAYLIST
    fora = next(i for i, c in enumerate(eq.itens) if not ctx.scenarios.na_playlist(c.id))
    eq.escolher(fora)
    assert len(ctx.scenarios.playlist) == MAX_PLAYLIST and str(MAX_PLAYLIST) in eq.aviso[0]
    quadros(eq, 3)


def test_equipamentos_e_loja_se_conversam(ctx):
    eq = EquipmentScene(ctx)
    ctx.scenes.push(eq)
    eq.loja.ativar()
    loja = ctx.scenes.top
    assert isinstance(loja, ShopScene) and loja.aba == CENARIOS_ABA
    comprar_cenarios(ctx, ['deserto'])
    loja._sair()
    ctx.scenes.top.on_enter()
    assert 'deserto' in [c.id for c in eq.itens]                 # a lista se atualiza na volta
    eq.trocar_skin.ativar()
    assert isinstance(ctx.scenes.top, ShopScene) and ctx.scenes.top.aba == SKINS_ABA
