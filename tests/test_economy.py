"""Fase 5: carteira, loja, catálogo de skins, moedas no jogo e telas."""
import random

import pygame
import pytest

import snapshot
from scenarios import FakeClock

from flappy_arcade.config.constants import ALTURA, LARGURA, Y_NAVE
from flappy_arcade.config.economy import BONUS_POR_ESTRELA_NOVA
from flappy_arcade.config.skins import COMUM, POR_ID, RADICAL, RARA, SKIN_PADRAO, SKINS
from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.gameplay.coins import ColetorMoedas
from flappy_arcade.gameplay.free_mode import FreeSession
from flappy_arcade.gameplay.level_session import criar_sessao
from flappy_arcade.gameplay.skins import SkinVisual, trocar_paleta
from flappy_arcade.scenes.game_scene import GameScene
from flappy_arcade.scenes.level_scene import LevelScene
from flappy_arcade.scenes.main_menu import MainMenuScene
from flappy_arcade.scenes.shop_scene import ShopScene
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.economy import Carteira
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore
from flappy_arcade.systems.shop import DESCONHECIDA, JA_POSSUI, OK, SEM_MOEDAS, Loja


# ---------------------------------------------------------------- carteira e loja
@pytest.fixture
def save(tmp_path):
    s = SaveManager(tmp_path / 'save.json')
    s.load()
    return s


def test_carteira_deposita_gasta_e_persiste(save, tmp_path):
    c = Carteira(save)
    c.depositar(120)
    c.depositar(-5)                                 # ignorado
    assert c.saldo == 120
    assert c.gastar(200) is False and c.saldo == 120
    assert c.gastar(70) is True and c.saldo == 50
    assert SaveManager(tmp_path / 'save.json').load()['wallet']['coins'] == 50


def test_loja_compra_equipa_e_valida(save):
    carteira = Carteira(save)
    loja = Loja(save, carteira)
    assert loja.possui(SKIN_PADRAO) and loja.equipada == SKIN_PADRAO
    assert loja.comprar('azul') == SEM_MOEDAS
    assert loja.equipar('azul') is False
    carteira.depositar(60)
    assert loja.comprar('azul') == OK and carteira.saldo == 10
    assert loja.comprar('azul') == JA_POSSUI and carteira.saldo == 10
    assert loja.comprar('nao_existe') == DESCONHECIDA
    assert loja.equipar('azul') and loja.equipada == 'azul'


def test_save_estragado_nas_skins_volta_ao_padrao(save):
    save.section('skins').update(owned=['lixo'], equipped='lixo')
    loja = Loja(save, Carteira(save))
    assert loja.possui(SKIN_PADRAO) and not loja.possui('lixo')
    assert loja.equipada == SKIN_PADRAO


# ---------------------------------------------------------------- catálogo
def test_precos_seguem_a_raridade():
    faixas = {COMUM: (0, 100), RARA: (250, 500), RADICAL: (1000, 10_000)}
    assert len(POR_ID) == len(SKINS)
    for s in SKINS:
        minimo, maximo = faixas[s.raridade]
        assert minimo <= s.preco <= maximo, s.id
    assert POR_ID[SKIN_PADRAO].preco == 0
    assert sorted(SKINS, key=lambda s: s.preco) == sorted(SKINS, key=lambda s: (list(faixas).index(s.raridade), s.preco))


@pytest.mark.parametrize('skin', [s for s in SKINS if s.cores], ids=lambda s: s.id)
def test_troca_de_paleta_muda_mesmo_as_cores(recursos, skin):
    original = recursos.passaros['dia'][0]
    trocado = trocar_paleta(original, skin.cores)
    diferentes = sum(original.get_at((x, y)) != trocado.get_at((x, y))
                     for x in range(original.get_width()) for y in range(original.get_height()))
    assert diferentes > 200, f'{skin.id}: só {diferentes} pixels mudaram'


@pytest.mark.parametrize('efeitos', [True, False])
def test_todas_as_skins_desenham(recursos, efeitos):
    from flappy_arcade.gameplay.flappy import Passaro
    tela = pygame.Surface((LARGURA, ALTURA))
    for s in SKINS:
        visual = SkinVisual(s.id, recursos)
        visual.efeitos = efeitos
        p = Passaro(recursos)
        p.skin = visual
        for i in range(12):
            p.vy = (i % 5) - 2
            p.desenhar(tela)


# ---------------------------------------------------------------- moedas no jogo
def criar_livre(recursos, tmp_path, moedas=True, skin=None, arquivo='livre.json'):
    bus = EventBus()
    sv = SaveManager(tmp_path / arquivo)
    sv.load()
    audio = AudioManager(SettingsStore(sv, bus), recursos.sons, bus)
    clock = FakeClock()
    s = FreeSession(recursos, audio, clock, sv)
    s.preparar_recompensas(skin=SkinVisual(skin, recursos) if skin else None, moedas=moedas)
    return s, clock


def passo(sessao, clock, n=1):
    for _ in range(n):
        clock.avancar()
        sessao.atualizar(1 / 30, clock.ticks())
        sessao.desenhar()


def test_moeda_fica_no_centro_da_passagem_e_e_coletada(recursos, tmp_path):
    s, clock = criar_livre(recursos, tmp_path)
    s.acao_principal()
    s.coletor.aleatorio = random.Random(0)
    s.coletor.aleatorio.random = lambda: 0.0           # toda passagem com moeda
    passo(s, clock)
    o = s.obstaculos[0]
    x, y = s.coletor.posicao_na_passagem(o)
    assert x == o.x + o.largura / 2 and y == o.topo_passagem + o.abertura / 2
    s.passaro.x, s.passaro.y = x - 34, y - 24              # pássaro no centro da passagem
    s.passaro.vy = 0
    s.passaro.gravidade = 0
    s.coletor._passagens(s)
    assert s.moedas_coletadas == 1 and s.coletor.nas_passagens[id(o)] is False


def test_moeda_da_galaga_cai_e_e_coletada_pela_nave(recursos, tmp_path):
    s, clock = criar_livre(recursos, tmp_path)
    s.acao_principal()
    s.iniciar_fase_especial('GALAGA')
    s.coletor.espera_galaga = 0
    passo(s, clock)
    assert len(s.coletor.caindo) == 1
    s.coletor.caindo[0] = [s.galaga.nave_x, Y_NAVE - 40]
    passo(s, clock, 5)
    assert s.moedas_coletadas == 1 and not s.coletor.caindo


def test_bananas_do_donkey_viram_moedas(recursos, tmp_path):
    s, clock = criar_livre(recursos, tmp_path)
    s.acao_principal()
    s.iniciar_fase_especial('DONKEY')
    passo(s, clock)
    s.donkey.bananas_coletadas += 3
    passo(s, clock)
    assert s.moedas_coletadas == 3


def test_coletor_nao_mexe_no_random_do_jogo(recursos, tmp_path):
    s, clock = criar_livre(recursos, tmp_path)
    s.acao_principal()
    estado = random.getstate()
    c = ColetorMoedas()
    for _ in range(50):
        c.atualizar(s, 1 / 30)
    assert random.getstate() == estado


def test_moedas_e_skin_nao_mudam_a_jogabilidade(recursos, tmp_path, monkeypatch):
    """Regra de ouro: a mesma partida, com e sem moedas/skin, tem física idêntica."""
    monkeypatch.setattr(snapshot, 'IGNORADOS', snapshot.IGNORADOS | {
        'coletor', 'skin', 'saldo_inicial', 'moedas_ativas'})

    def partida(moedas, skin):
        random.seed(31)
        s, clock = criar_livre(recursos, tmp_path, moedas, skin, arquivo=f'{moedas}-{skin}.json')
        s.acao_principal()
        hashes = []
        for i in range(1500):
            alvo = next((o for o in s.obstaculos if o.x + o.largura > s.passaro.x), None)
            if alvo and s.passaro.y + 24 > alvo.topo_passagem + alvo.abertura / 2 and s.passaro.vy >= 0:
                s.acao_principal()
            if i == 600:
                s.iniciar_alerta('GALAGA')
            passo(s, clock)
            if i % 50 == 0:
                hashes.append(snapshot.hash_estado(s))
        return hashes, s

    sem, s_sem = partida(False, None)
    com, s_com = partida(True, 'arco_iris')
    assert s_com.moedas_coletadas > 0, 'o cenário precisa coletar moedas para valer'
    assert com == sem


# ---------------------------------------------------------------- telas
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


def vencer_casa(ctx, mapa, casa, moedas, danos=0):
    cena = LevelScene(ctx, mapa, casa)
    ctx.scenes.push(cena)
    tecla(cena, pygame.K_SPACE)
    cena.session.coletor.coletadas = moedas
    cena.session.danos = danos
    cena.session.pontos = cena.session.meta
    quadros(cena, 3, 1 / 30)
    return cena


def test_casa_deposita_moedas_e_bonus_so_de_estrelas_novas(ctx):
    cena = vencer_casa(ctx, 'flappy', 1, moedas=7, danos=1)              # 2 estrelas
    assert cena.bonus == 2 * BONUS_POR_ESTRELA_NOVA
    assert ctx.wallet.saldo == 7 + 20
    cena.on_exit()                                                       # não deposita de novo
    assert ctx.wallet.saldo == 27
    vencer_casa(ctx, 'flappy', 1, moedas=4, danos=1)                     # repetiu: sem bônus
    assert ctx.wallet.saldo == 27 + 4
    melhor = vencer_casa(ctx, 'flappy', 1, moedas=0)                     # 2 -> 3: uma estrela nova
    assert melhor.bonus == BONUS_POR_ESTRELA_NOVA


def test_sair_no_meio_guarda_as_moedas(ctx):
    cena = LevelScene(ctx, 'galaga', 1)
    ctx.scenes.push(cena)
    tecla(cena, pygame.K_SPACE)
    cena.session.coletor.coletadas = 5
    tecla(cena, pygame.K_ESCAPE)                                         # volta ao mapa
    assert ctx.wallet.saldo == 5


def test_modo_livre_deposita_ao_sair_e_classico_nao_tem_moedas(ctx):
    livre = GameScene(ctx, 'livre')
    ctx.scenes.push(livre)
    livre.session.coletor.coletadas = 9
    ctx.scenes.pop()
    assert ctx.wallet.saldo == 9
    classico = GameScene(ctx, 'classico')
    assert not hasattr(classico.session, 'coletor')


def test_loja_comprar_pede_confirmacao_e_equipa(ctx):
    loja = ShopScene(ctx)
    ctx.scenes.push(loja)
    tecla(loja, pygame.K_RIGHT)                                          # Céu Azul (50)
    quadros(loja, 2)
    assert loja.acao.rotulo == 'FALTAM 50' and not loja.acao.habilitado
    ctx.wallet.depositar(80)
    quadros(loja, 2)
    tecla(loja, pygame.K_RETURN)
    quadros(loja, 2)
    assert loja.acao.rotulo == 'CONFIRMAR?' and ctx.wallet.saldo == 80
    tecla(loja, pygame.K_RETURN)
    quadros(loja, 2)
    assert ctx.shop.possui('azul') and ctx.shop.equipada == 'azul' and ctx.wallet.saldo == 30
    assert loja.acao.rotulo == 'EQUIPADA'
    tecla(loja, pygame.K_LEFT)                                           # volta ao Clássico
    quadros(loja, 2)
    assert loja.acao.rotulo == 'EQUIPAR'
    tecla(loja, pygame.K_RETURN)
    assert ctx.shop.equipada == SKIN_PADRAO


def test_confirmacao_expira(ctx):
    ctx.wallet.depositar(100)
    loja = ShopScene(ctx)
    ctx.scenes.push(loja)
    tecla(loja, pygame.K_RIGHT)
    tecla(loja, pygame.K_RETURN)
    quadros(loja, 200)                                                   # mais de 3 s
    tecla(loja, pygame.K_RETURN)
    assert not ctx.shop.possui('azul')                                   # pediu confirmação de novo


@pytest.mark.parametrize('efeitos', [True, False])
def test_loja_rola_ate_o_fim_e_desenha(ctx, efeitos):
    ctx.settings.set('visual_fx', efeitos)
    loja = ShopScene(ctx)
    ctx.scenes.push(loja)
    for _ in range(len(SKINS)):
        tecla(loja, pygame.K_DOWN)
        tecla(loja, pygame.K_RIGHT)
    quadros(loja, 60)
    assert loja.indice == len(SKINS) - 1 and loja.rolagem > 0


def test_tela_de_modos_abre_a_loja(ctx):
    menu = MainMenuScene(ctx)
    ctx.scenes.push(menu)
    loja = next(b for b in menu.grupo.botoes if b.rotulo == 'LOJA')
    loja.ativar()
    assert isinstance(ctx.scenes.top, ShopScene)


def test_skin_equipada_aparece_nas_casas(ctx):
    ctx.wallet.depositar(1000)
    ctx.shop.comprar('dourado')
    ctx.shop.equipar('dourado')
    cena = LevelScene(ctx, 'arcade', 1)
    assert cena.session.skin.id == 'dourado'
    s = criar_sessao('flappy', 1, ctx.resources, ctx.audio, FakeClock())
    assert s.skin is None                                                # sem preparar: pássaro original
