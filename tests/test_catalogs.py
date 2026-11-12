"""Fase 9: catálogos de skins (categorias e preços) e de cenários, save v2 e coleção de cenários."""
import json

import pygame
import pytest

from flappy_arcade.config import scenarios as cfg_cen
from flappy_arcade.config.constants import ALTURA, LARGURA, TEMAS
from flappy_arcade.config.scenarios import (CENARIO_PADRAO, CENARIOS, FAIXAS_PRECO_NOVOS, MAX_PLAYLIST,
                                            MODO_ALEATORIO, MODO_FIXO, NOITE, ORIGINAL, PERIODOS)
from flappy_arcade.config.skins import (CATEGORIAS, CLASSICAS, FANTASIAS, POR_CATEGORIA, POR_ID, RADICAL, SKINS,
                                        TIMES)
from flappy_arcade.core.paths import ARTES_CENARIOS, ARTES_SKINS, IMAGENS
from flappy_arcade.gameplay.flappy import Passaro
from flappy_arcade.gameplay.skins import SkinVisual
from flappy_arcade.systems.economy import Carteira
from flappy_arcade.systems.save_manager import PADRAO, VERSAO_ATUAL, SaveManager
from flappy_arcade.systems.scenarios import (NAO_POSSUI, PLAYLIST_CHEIA, ULTIMO_DA_PLAYLIST, ColecaoCenarios)
from flappy_arcade.systems.shop import JA_POSSUI, OK, SEM_MOEDAS


# ---------------------------------------------------------------- skins
def test_categorias_de_skins():
    assert {c: len(POR_CATEGORIA[c]) for c in CATEGORIAS} == {CLASSICAS: 18, FANTASIAS: 36, TIMES: 32}
    assert len(SKINS) == len(POR_ID) == 86
    # Fantasias e Times são artes; a única exceção é a lendária (personagem com poses, Fase 22)
    assert [s.id for s in POR_CATEGORIA[FANTASIAS] + POR_CATEGORIA[TIMES] if s.tipo != 'arte'] == ['wilson']


def test_toda_arte_do_catalogo_existe_e_toda_arte_esta_no_catalogo():
    no_catalogo = {s.sprite for s in SKINS if s.tipo == 'arte'}
    assert no_catalogo == {p.stem for p in ARTES_SKINS.glob('*.png')}


def test_precos_aprovados_das_skins_novas():
    assert {s.preco for s in POR_CATEGORIA[TIMES]} == {200}
    simples = {'gato', 'cachorro', 'sapo', 'panda', 'abelha', 'joaninha', 'ninja', 'esportista',
               'gamer', 'inverno', 'verao'}
    radicais = {'unicornio': 'rastro_arco_iris', 'fada': 'brilho', 'futurista': 'neon', 'dinossauro': 'poeira'}
    for s in POR_CATEGORIA[FANTASIAS]:
        if s.id == 'wilson':                 # a lendária tem testes próprios (test_lendaria.py)
            continue
        if s.id in simples:
            assert s.preco == 120, s.id
        elif s.id in radicais:
            assert s.raridade == RADICAL and 1200 <= s.preco <= 2000 and s.efeito == radicais[s.id], s.id
        else:
            assert 350 <= s.preco <= 500 and not s.efeito, s.id


def test_personagens_de_terceiros_nao_estao_a_venda():
    nomes = {s.nome.lower() for s in SKINS}
    for proibido in ('link', 'cavaleiro', 'super herói', 'herói vermelho', 'batman', 'superman'):
        assert proibido not in nomes


@pytest.mark.parametrize('skin', [s for s in SKINS if s.tipo == 'arte'], ids=lambda s: s.id)
def test_skin_de_arte_nao_muda_a_colisao(recursos, skin):
    """A arte é maior que o pássaro original, mas a colisão continua a do original."""
    sem, com = Passaro(recursos), Passaro(recursos)
    com.skin = SkinVisual(skin.id, recursos)
    tela = pygame.Surface((LARGURA, ALTURA))
    for _ in range(3):
        com.desenhar(tela)
    assert com.retangulo() == sem.retangulo()
    assert com.sprite is sem.sprite          # a máscara de colisão sai deste sprite


@pytest.mark.parametrize('efeitos', [True, False])
@pytest.mark.parametrize('skin_id', ['unicornio', 'dinossauro', 'fada', 'futurista'])
def test_efeitos_novos_desenham_e_somem_sem_efeitos(recursos, skin_id, efeitos):
    visual = SkinVisual(skin_id, recursos)
    visual.efeitos = efeitos
    p = Passaro(recursos)
    p.skin = visual
    tela = pygame.Surface((LARGURA, ALTURA))
    for i in range(30):
        p.vy = (i % 5) - 2
        p.desenhar(tela)
    if skin_id == 'unicornio':
        assert len(visual.rastro) > 0
    if skin_id == 'dinossauro':
        assert bool(visual.poeira) == efeitos
    if skin_id == 'fada':
        assert bool(visual.brilhos) == efeitos


# ---------------------------------------------------------------- cenários
def test_catalogo_de_cenarios():
    assert len(CENARIOS) == len(cfg_cen.POR_ID) == 31
    gratis = [c.id for c in CENARIOS if c.preco == 0]
    assert gratis == [CENARIO_PADRAO]
    originais = [c for c in CENARIOS if c.tipo == ORIGINAL]
    assert {c.id for c in originais} == set(TEMAS)                # todos os fundos do original
    for c in originais[1:]:
        assert 150 <= c.preco <= 400, c.id
    assert max(originais, key=lambda c: c.preco).periodo == NOITE
    novos = [c for c in CENARIOS if c.tipo != ORIGINAL]
    assert len(novos) == 20 and {c.preco for c in novos} == set(FAIXAS_PRECO_NOVOS)
    assert all(c.periodo in PERIODOS for c in CENARIOS)


def test_arquivos_dos_cenarios_existem():
    for c in CENARIOS:
        pasta = IMAGENS if c.tipo == ORIGINAL else ARTES_CENARIOS
        assert (pasta / c.arquivo).exists(), c.id
    assert {c.arquivo for c in CENARIOS if c.tipo != ORIGINAL} == {p.name for p in ARTES_CENARIOS.glob('*.png')}


def test_periodos_do_original_batem_com_o_jogo():
    from flappy_arcade.config.constants import TEMAS_DIA, TEMAS_TARDE
    for c in CENARIOS:
        if c.tipo == ORIGINAL:
            esperado = 'dia' if c.id in TEMAS_DIA else 'tarde' if c.id in TEMAS_TARDE else 'noite'
            assert c.periodo == esperado, c.id


# ---------------------------------------------------------------- save v2
def test_save_novo_comeca_so_com_o_cenario_basico(tmp_path):
    dados = SaveManager(tmp_path / 'save.json').load()
    assert dados['version'] == VERSAO_ATUAL == 2
    assert dados['scenarios'] == {'owned': ['bg'], 'mode': 'fixo', 'fixed': 'bg', 'playlist': ['bg']}


def test_save_da_versao_1_migra_sem_perder_nada(tmp_path):
    antigo = {'version': 1, 'settings': {'music': False, 'sfx': True, 'visual_fx': True},
              'wallet': {'coins': 777}, 'skins': {'owned': ['classico', 'azul'], 'equipped': 'azul'},
              'progress': {'flappy': {'estrelas': [3, 2]}}, 'records': {'free_best_streak': 41}}
    caminho = tmp_path / 'save.json'
    caminho.write_text(json.dumps(antigo), encoding='utf-8')
    save = SaveManager(caminho)
    dados = save.load()
    assert dados['version'] == 2
    for chave in ('settings', 'wallet', 'skins', 'progress', 'records'):
        assert dados[chave] == antigo[chave]
    assert dados['scenarios'] == PADRAO['scenarios']
    save.save()
    assert json.loads(caminho.read_text(encoding='utf-8'))['version'] == 2


# ---------------------------------------------------------------- coleção
@pytest.fixture
def colecao(tmp_path):
    save = SaveManager(tmp_path / 'save.json')
    save.load()
    carteira = Carteira(save)
    carteira.depositar(20_000)
    return ColecaoCenarios(save, carteira), save, carteira


def test_comprar_cenario(colecao):
    col, save, carteira = colecao
    assert col.possui('bg') and not col.possui('praia')
    assert col.comprar('praia') == OK
    assert carteira.saldo == 20_000 - 600
    assert col.possui('praia') and col.na_playlist('praia')
    assert col.comprar('praia') == JA_POSSUI
    carteira.gastar(carteira.saldo)
    assert col.comprar('galaxia') == SEM_MOEDAS and not col.possui('galaxia')
    assert SaveManager(save.caminho).load()['scenarios']['owned'] == ['bg', 'praia']


def test_fixo_e_aleatorio(colecao):
    col, *_ = colecao
    assert col.ativos() == ['bg']
    assert col.usar_fixo('praia') == NAO_POSSUI
    col.comprar('praia')
    col.comprar('night')
    assert col.usar_fixo('praia') == OK and col.ativos() == ['praia']
    col.definir_modo(MODO_ALEATORIO)
    assert col.ativos() == ['bg', 'praia', 'night']
    col.definir_modo(MODO_FIXO)
    assert col.ativos() == ['praia']


def test_playlist_tem_limite_e_nunca_fica_vazia(colecao):
    col, *_ = colecao
    for c in CENARIOS[1:20]:
        col.carteira.depositar(c.preco)
        col.comprar(c.id)
    assert len(col.playlist) == MAX_PLAYLIST            # os comprados depois do 15º não entram sozinhos
    fora = next(c for c in col.comprados if not col.na_playlist(c))
    assert col.alternar_na_playlist(fora) == PLAYLIST_CHEIA
    assert col.alternar_na_playlist(col.playlist[0]) == OK
    assert col.alternar_na_playlist(fora) == OK and col.na_playlist(fora)
    for c in col.playlist[:-1]:
        col.alternar_na_playlist(c)
    assert col.alternar_na_playlist(col.playlist[0]) == ULTIMO_DA_PLAYLIST
    assert col.alternar_na_playlist('galaxia') == NAO_POSSUI


def test_dados_estragados_sao_consertados(colecao):
    col, save, _ = colecao
    save.section('scenarios').update(owned=['lixo', 'praia', 'praia'], mode='???', fixed='galaxia',
                                     playlist=['galaxia', 'lixo'] + ['praia'] * 30)
    assert col.comprados == ['bg', 'praia']
    assert col.modo == MODO_FIXO and col.fixo == 'bg'
    assert col.playlist == ['praia']


def test_resetar_progresso_zera_os_cenarios(colecao):
    col, save, _ = colecao
    col.comprar('praia')
    col.usar_fixo('praia')
    save.reset_progress()
    assert col.comprados == ['bg'] and col.fixo == 'bg'


def test_app_tem_a_colecao():
    from flappy_arcade.core.app import App
    colecao = App().ctx.scenarios
    assert isinstance(colecao, ColecaoCenarios) and colecao.possui(CENARIO_PADRAO)
