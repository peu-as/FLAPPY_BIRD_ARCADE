"""Fase 16: Combina 3 — regras do tabuleiro, peças especiais, cascatas e a sessão."""
import random

import pygame
import pytest

from flappy_arcade.config import combina3 as cfg
from flappy_arcade.config.constants import ALTURA, LARGURA
from flappy_arcade.config.levels import MAPAS, ORDEM_MAPAS, etapa_arcade
from flappy_arcade.gameplay.combina3.partida import BARRIL, CASULO, Partida, dano_da_onda
from flappy_arcade.gameplay.combina3.sessao import ATAQUE, ESTOURO, PRONTO, TROCA, Combina3Session
from flappy_arcade.gameplay.combina3.tabuleiro import ARCO, LINHA_H, LINHA_V, OVO, TIPOS, Tabuleiro
from flappy_arcade.gameplay.combina3.visual import casa_em, centro_da_casa

FUNDO = ('semente', 'fruta', 'moeda')          # peças de fundo: nunca formam sequência sozinhas


def montar(pecas=None, linhas=8, colunas=7, **obstaculos):
    """Tabuleiro sem nenhuma combinação pronta; `pecas` = {(l, c): tipo ou (tipo, especial)}."""
    tab = Tabuleiro(linhas, colunas, semente=1, **obstaculos)
    for l in range(linhas):
        for c in range(colunas):
            tab.grade[l][c] = tab.nova_peca(FUNDO[(2 * l + c) % 3]) if tab.livre(l, c) else None
    for (l, c), valor in (pecas or {}).items():
        tipo, especial = valor if isinstance(valor, tuple) else (valor, '')
        tab.grade[l][c] = tab.nova_peca(tipo, especial)
    assert not tab._sequencias(), 'o tabuleiro de teste já começa com combinação'
    return tab


def ids(tab):
    return [[p.id if p else None for p in linha] for linha in tab.grade]


def cheio_e_calmo(tab):
    return all(tab.peca(casa) is not None for casa in tab.casas()) and not tab._sequencias()


# ---------------------------------------------------------------- começo
@pytest.mark.parametrize('semente', range(25))
def test_comeca_sem_combinacao_e_com_jogada(semente):
    tab = Tabuleiro(semente=semente)
    assert cheio_e_calmo(tab) and tab.dica() is not None
    assert {p.tipo for linha in tab.grade for p in linha} <= set(TIPOS)


def test_mesma_semente_mesma_partida_e_nada_do_random_do_jogo():
    random.seed(8)
    estado = random.getstate()

    def partida():
        tab = Tabuleiro(semente=42)
        for _ in range(15):
            tab.jogar(*tab.dica())
        return tab.pontos, [[(p.tipo, p.especial) for p in linha] for linha in tab.grade]
    assert partida() == partida()
    assert random.getstate() == estado


# ---------------------------------------------------------------- combinações
def test_troca_que_nao_combina_nao_muda_nada():
    tab = montar()
    antes = ids(tab)
    assert tab.trocar((0, 0), (0, 1)) is None
    assert ids(tab) == antes and tab.pontos == 0
    assert tab.trocar((0, 0), (2, 2)) is None            # não são vizinhas


def test_tres_iguais_somem_e_pontuam():
    tab = montar({(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena'})
    onda = tab.trocar((5, 2), (4, 2))
    assert set(onda.limpas) == {(4, 0), (4, 1), (4, 2)} and not onda.criadas
    assert onda.pontos == 60 and onda.multiplicador == 1
    tab.aplicar(onda)
    assert tab.pontos == 60 and tab.contagem['pena'] == 3
    assert all(tab.grade[4][c] is None for c in range(3))


def test_quatro_em_linha_viram_pena_raio():
    tab = montar({(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena', (4, 3): 'pena'})
    onda = tab.trocar((5, 2), (4, 2))
    assert len(onda.limpas) == 4
    assert {casa: p.especial for casa, p in onda.criadas.items()} == {(4, 2): LINHA_H}   # nasce onde a peça chegou
    assert onda.criadas[(4, 2)].tipo == 'pena'
    tab = montar({(0, 3): 'pena', (1, 3): 'pena', (2, 4): 'pena', (3, 3): 'pena'})
    onda = tab.trocar((2, 4), (2, 3))
    assert [p.especial for p in onda.criadas.values()] == [LINHA_V]


def test_l_ou_t_vira_ovo_nova_e_cinco_vira_arco_iris():
    tab = montar({(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena', (3, 2): 'pena', (2, 2): 'pena'})
    onda = tab.trocar((5, 2), (4, 2))                    # canto do L em (4, 2)
    assert len(onda.limpas) == 5
    assert {casa: p.especial for casa, p in onda.criadas.items()} == {(4, 2): OVO}
    tab = montar({(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena', (4, 3): 'pena', (4, 4): 'pena'})
    onda = tab.trocar((5, 2), (4, 2))
    arco = onda.criadas[(4, 2)]
    assert arco.especial == ARCO and arco.tipo == ''


# ---------------------------------------------------------------- especiais
def test_pena_raio_limpa_a_linha_ou_a_coluna():
    tab = montar({(4, 0): ('pena', LINHA_H), (4, 1): 'pena', (5, 2): 'pena'})
    onda = tab.trocar((5, 2), (4, 2))
    assert set(onda.limpas) == {(4, c) for c in range(7)} and (LINHA_H, 4) in onda.efeitos
    tab = montar({(4, 0): ('pena', LINHA_V), (4, 1): 'pena', (5, 2): 'pena'})
    onda = tab.trocar((5, 2), (4, 2))
    assert set(onda.limpas) == {(4, 1), (4, 2)} | {(l, 0) for l in range(8)}


def test_ovo_nova_explode_3x3():
    tab = montar({(4, 3): ('pena', OVO), (4, 4): 'pena', (5, 5): 'pena'})
    onda = tab.trocar((5, 5), (4, 5))
    assert set(onda.limpas) == {(l, c) for l in (3, 4, 5) for c in (2, 3, 4)} | {(4, 5)}
    assert ('explosao', 4, 3, 1) in onda.efeitos


def test_arco_iris_com_uma_peca_limpa_todas_daquele_tipo():
    tab = montar({(4, 3): ('', ARCO)})
    alvo = tab.peca((4, 4)).tipo
    quantas = sum(p.tipo == alvo for linha in tab.grade for p in linha)
    onda = tab.trocar((4, 3), (4, 4))
    assert len(onda.limpas) == quantas + 1                # todas as do tipo + o próprio Arco-íris
    assert all(p.tipo in (alvo, '') for p in onda.limpas.values())


def test_especial_atingida_por_outra_dispara_em_cadeia():
    tab = montar({(4, 0): ('pena', LINHA_H), (4, 1): 'pena', (5, 2): 'pena', (4, 6): ('folha', LINHA_V)})
    onda = tab.trocar((5, 2), (4, 2))
    assert {(l, 6) for l in range(8)} <= set(onda.limpas)
    assert (LINHA_H, 4) in onda.efeitos and (LINHA_V, 6) in onda.efeitos


@pytest.mark.parametrize('a, b, esperado', [
    (LINHA_H, LINHA_V, lambda l, c: l == 4 or c == 3),                       # cruz
    (OVO, OVO, lambda l, c: abs(l - 4) <= 2 and abs(c - 3) <= 2),            # 5x5
    (LINHA_H, OVO, lambda l, c: abs(l - 4) <= 1 or abs(c - 3) <= 1),         # 3 linhas + 3 colunas
    (ARCO, ARCO, lambda l, c: True),                                         # o tabuleiro inteiro
])
def test_combos_entre_especiais(a, b, esperado):
    tab = montar({(4, 2): ('pena' if a != ARCO else '', a), (4, 3): ('folha' if b != ARCO else '', b)})
    onda = tab.trocar((4, 2), (4, 3))                     # a peça movida chega em (4, 3)
    assert set(onda.limpas) == {(l, c) for l in range(8) for c in range(7) if esperado(l, c)}


def test_arco_iris_com_especial_transforma_todas_e_dispara():
    tab = montar({(4, 2): ('', ARCO), (4, 3): ('pena', OVO), (0, 0): 'pena', (7, 6): 'pena'})
    onda = tab.trocar((4, 2), (4, 3))
    assert onda.transformadas == {(4, 2): OVO, (0, 0): OVO, (7, 6): OVO}   # a parceira foi para (4, 2)
    assert {(0, 1), (1, 0), (1, 1), (6, 5), (6, 6), (7, 5)} <= set(onda.limpas)


# ---------------------------------------------------------------- queda e cascata
def test_pecas_caem_e_entram_novas():
    tab = montar({(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena'})
    de_cima = tab.peca((3, 0))
    tab.aplicar(tab.trocar((5, 2), (4, 2)))
    movimentos = tab.cair()
    assert tab.peca((4, 0)) is de_cima                    # a de cima desceu uma casa
    novas = [(origem, destino) for _, origem, destino in movimentos if origem < 0]
    assert sorted(novas) == [(-1, (0, 0)), (-1, (0, 1)), (-1, (0, 2))]
    assert all(tab.peca(casa) is not None for casa in tab.casas())


def test_cascata_vale_em_dobro():
    # as penas da linha 5 somem; as folhas de cima descem e fecham um trio com a folha de (5, 3)
    tab = montar({(5, 0): 'pena', (5, 1): 'pena', (6, 2): 'pena',
                  (4, 1): 'folha', (4, 2): 'folha', (5, 3): 'folha'})
    primeira = tab.trocar((6, 2), (5, 2))
    assert set(primeira.limpas) == {(5, 0), (5, 1), (5, 2)} and primeira.multiplicador == 1
    tab.aplicar(primeira)
    tab.cair()
    segunda = tab.proxima_onda()
    assert {(5, 1), (5, 2), (5, 3)} <= set(segunda.limpas)
    assert segunda.multiplicador == 2 and segunda.pontos >= 2 * 60
    tab.aplicar(segunda)
    assert tab.pontos == primeira.pontos + segunda.pontos and tab.contagem['folha'] >= 3


def test_jogada_inteira_deixa_o_tabuleiro_cheio_e_calmo():
    for semente in range(12):
        tab = Tabuleiro(semente=semente)
        total = 0
        for _ in range(40):
            a, b = tab.dica()
            ganho = tab.jogar(a, b)
            assert ganho is not None and ganho >= 60
            total += ganho
            assert cheio_e_calmo(tab) and tab.dica() is not None
        assert tab.pontos == total


# ---------------------------------------------------------------- obstáculos
def test_gelo_some_quando_a_peca_de_cima_e_limpa():
    tab = montar({(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena'}, gelo={(4, 1): 2, (0, 0): 1})
    onda = tab.trocar((5, 2), (4, 2))
    assert onda.gelo == [(4, 1)] and onda.pontos == 60 + 30
    tab.aplicar(onda)
    assert tab.gelo[4][1] == 1 and tab.gelo_restante == 2


def test_caixa_ocupa_a_casa_e_quebra_com_limpeza_ao_lado():
    tab = montar({(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena'}, caixas={(4, 3): 2, (0, 6): 1})
    assert tab.peca((4, 3)) is None and not tab.livre(4, 3)
    onda = tab.trocar((5, 2), (4, 2))
    assert onda.caixas == [(4, 3)]
    tab.aplicar(onda)
    assert tab.caixa[4][3] == 1 and tab.caixas_restantes == 2
    tab.cair()
    assert tab.peca((4, 3)) is None                       # ainda é caixa: nada cai ali
    assert all(tab.peca(casa) is not None for casa in tab.casas())


def test_efeito_passa_por_cima_da_caixa_e_da_pedra():
    tab = montar({(4, 0): ('pena', LINHA_H), (4, 1): 'pena', (5, 2): 'pena'},
                 caixas={(4, 5): 1}, pedras={(4, 6)})
    onda = tab.trocar((5, 2), (4, 2))
    assert (4, 5) in onda.caixas and (4, 6) not in onda.limpas
    tab.aplicar(onda)
    assert tab.caixa[4][5] == 0 and tab.livre(4, 5) and not tab.livre(4, 6)
    tab.cair()
    assert tab.peca((4, 5)) is not None                   # a caixa quebrou: a casa volta a receber peça


def test_pecas_param_em_cima_da_caixa():
    tab = montar(caixas={(4, 0): 1})
    acima = tab.peca((3, 0))
    tab.grade[6][0] = None                                # buraco embaixo da caixa
    movimentos = tab.cair()
    assert tab.peca((3, 0)) is acima                      # o de cima não atravessa a caixa
    assert any(destino == (5, 0) and origem == 4 for _, origem, destino in movimentos)   # entra uma nova no trecho


# ---------------------------------------------------------------- sem jogadas
def test_embaralhar_usa_as_mesmas_pecas():
    tab = Tabuleiro(semente=5)
    antes = sorted(p.id for linha in tab.grade for p in linha)
    tab.embaralhar()
    assert sorted(p.id for linha in tab.grade for p in linha) == antes
    assert cheio_e_calmo(tab) and tab.dica() is not None


def test_jogadas_lista_so_trocas_que_combinam():
    tab = Tabuleiro(semente=9)
    jogadas = tab.jogadas()
    assert jogadas and tab.dica() == jogadas[0]
    for a, b in jogadas[:6]:
        copia_ids = ids(tab)
        assert tab._valida(a, b) and ids(tab) == copia_ids


# ---------------------------------------------------------------- casas
def test_25_casas_com_objetivos_variados():
    assert len(cfg.CASAS_COMBINA3) == 25
    assert [n for n, c in enumerate(cfg.CASAS_COMBINA3, 1) if c.chefe] == [5, 10, 15, 20, 25]
    tipos = {o[0] for c in cfg.CASAS_COMBINA3 for o in c.objetivos}
    assert tipos == {cfg.PONTOS, cfg.COLETAR, cfg.GELO, cfg.CAIXAS, cfg.CHEFE}
    assert {c.chefao.nome for c in cfg.CASAS_COMBINA3 if c.chefe} == {'rei_inseto', 'kong', 'dupla'}
    for n, casa in enumerate(cfg.CASAS_COMBINA3, 1):
        assert not casa.mapa or (len(casa.mapa) == 8 and all(len(x) == 7 and set(x) <= set('.#cCgG') for x in casa.mapa))
        p = Partida(casa, semente=n)
        assert cheio_e_calmo(p.tab) and p.tab.dica() is not None, n
        objetivos = {o[0] for o in casa.objetivos}
        assert (cfg.GELO in objetivos) == (p.gelo_total > 0), n            # gelo no tabuleiro só quando é objetivo
        assert cfg.CAIXAS not in objetivos or p.caixas_total > 0, n
        assert all(f == 0 for _, f, _ in p.progresso()), n
    vidas = [c.chefao.vida for c in cfg.CASAS_COMBINA3 if c.chefe]
    assert vidas == sorted(vidas)                                          # cada chefão é mais forte


def test_textos_de_abertura():
    assert cfg.descrever(cfg.casa_combina3(1)) == 'Faça 2.500 pontos em 20 jogadas. 3 estrelas: sobrando 6.'
    assert cfg.descrever(cfg.casa_combina3(4)).startswith('Junte 14 folhas e 14 frutas em 20 jogadas.')
    assert cfg.descrever(cfg.casa_combina3(11)).startswith('Quebre todas as caixas e todo o gelo em 20')
    assert cfg.descrever(cfg.casa_combina3(25)).startswith('Derrote o Rei-Inseto e o Kong em 24 jogadas.')


def test_estrelas_pelas_jogadas_que_sobraram():
    assert cfg.jogadas_para_estrelas(20) == (6, 3)
    assert [cfg.estrelas_combina3(20, u) for u in (10, 14, 15, 17, 18, 20)] == [3, 3, 2, 2, 1, 1]


# ---------------------------------------------------------------- objetivos e chefões (Partida)
def montada(casa, pecas=None):
    """Partida com o tabuleiro sem combinação pronta (como montar), respeitando os obstáculos da casa."""
    p = Partida(casa, semente=1)
    tab = p.tab
    for l in range(tab.linhas):
        for c in range(tab.colunas):
            tab.grade[l][c] = tab.nova_peca(FUNDO[(2 * l + c) % 3]) if tab.livre(l, c) else None
    for (l, c), valor in (pecas or {}).items():
        tipo, especial = valor if isinstance(valor, tuple) else (valor, '')
        tab.grade[l][c] = tab.nova_peca(tipo, especial)
    assert not tab._sequencias()
    return p


def jogar_onda(p, a, b):
    onda = p.tab.trocar(a, b)
    p.usar_jogada()
    return onda, p.aplicar(onda)


TRIO = {(4, 0): 'pena', (4, 1): 'pena', (5, 2): 'pena'}            # (5, 2) -> (4, 2) fecha o trio


def test_coletar_conta_as_pecas_limpas():
    p = montada(cfg.CasaCombina3(20, ((cfg.COLETAR, 'pena', 3), (cfg.COLETAR, 'folha', 2))), TRIO)
    jogar_onda(p, (5, 2), (4, 2))
    assert [(f, a) for _, f, a in p.progresso()] == [(3, 3), (0, 2)]
    assert not p.cumprida() and 0.4 < p.fracao() < 0.6


def test_gelo_e_caixas_contam_cada_camada_e_golpe():
    mapa = ('.......',) * 4 + ('.G.C...',) + ('.......',) * 3        # gelo grosso em (4, 1), caixa em (4, 3)
    p = montada(cfg.CasaCombina3(20, ((cfg.GELO,), (cfg.CAIXAS,)), mapa), TRIO)
    assert p.gelo_total == 2 and p.caixas_total == 2
    jogar_onda(p, (5, 2), (4, 2))                                   # o trio passa sobre o gelo e encosta na caixa
    assert [(f, a) for _, f, a in p.progresso()] == [(1, 2), (1, 2)]


def test_chefe_perde_vida_por_peca_e_por_efeito():
    casa = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('kong', 100, 5, barris=1))
    p = montada(casa, TRIO)
    onda, dano = jogar_onda(p, (5, 2), (4, 2))
    assert dano == dano_da_onda(onda) == 3 and p.vida == 97
    p = montada(casa, {(4, 0): ('pena', LINHA_H), (4, 1): 'pena', (5, 2): 'pena'})
    onda, dano = jogar_onda(p, (5, 2), (4, 2))
    assert dano == 7 + cfg.DANO_POR_EFEITO                           # a linha inteira + o efeito
    pequena = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('kong', 5, 5, barris=1))
    p = montada(pequena, {(4, 0): ('pena', LINHA_H), (4, 1): 'pena', (5, 2): 'pena'})
    _, dano = jogar_onda(p, (5, 2), (4, 2))
    assert dano == 5 and p.vida == 0 and p.cumprida()


def test_chefe_ataca_a_cada_n_jogadas():
    casa = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('kong', 9999, 2, barris=2))
    p = Partida(casa, semente=4)
    assert p.jogadas_para_ataque() == 2
    assert p.jogar(*p.tab.dica()) is None and p.jogadas_para_ataque() == 1
    ataque = p.jogar(*p.tab.dica())
    assert ataque and [tipo for _, tipo in ataque.casas] == [BARRIL, BARRIL] and not ataque.bravo
    for (l, c), _ in ataque.casas:
        assert p.tab.caixa[l][c] == 2 and p.tab.grade[l][c] is None and (l, c) in p.barris
    assert p.jogadas_para_ataque() == 2 and p.tab.dica() is not None


def test_rei_inseto_prende_em_casulos_e_bravo_ataca_mais():
    casa = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('rei_inseto', 100, 1, casulos=2))
    p = Partida(casa, semente=2)
    p.usar_jogada()
    p.dano = 50                                                       # metade da vida: bravo
    ataque = p.planejar_ataque()
    assert ataque.bravo and [t for _, t in ataque.casas] == [CASULO] * 3
    pecas = [p.tab.peca(casa) for casa, _ in ataque.casas]
    assert all(pc is not None and not pc.especial for pc in pecas)
    removidas = p.aplicar_ataque(ataque)
    assert [pc for _, pc in removidas] == pecas
    assert all(p.tab.caixa[l][c] == 1 and (l, c) in p.casulos for (l, c), _ in ataque.casas)


def test_chefe_nao_ataca_quando_acabou_ou_tabuleiro_cheio_de_caixas():
    casa = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('kong', 100, 1, barris=2))
    p = Partida(casa, semente=3)
    p.usar_jogada()
    p.dano = 100
    assert p.planejar_ataque() is None                                # vitória: sem ataque
    p = Partida(casa, semente=3)
    p.usar_jogada()
    p.jogadas = 0
    assert p.planejar_ataque() is None                                # acabou: sem ataque
    p = Partida(casa, semente=3)
    p.usar_jogada()
    for c in range(7):
        for l in (0, 1):
            p.tab.caixa[l][c] = 1
            p.tab.grade[l][c] = None
    assert p.planejar_ataque() is None                                # já há 14 caixas (máx. 12)


def test_quebrar_casulo_tira_da_lista():
    casa = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('rei_inseto', 999, 1, casulos=1))
    p = montada(casa, TRIO)
    p.tab.grade[4][3] = None
    p.tab.caixa[4][3] = 1
    p.casulos.add((4, 3))
    onda, _ = jogar_onda(p, (5, 2), (4, 2))
    assert (4, 3) in onda.caixas and (4, 3) not in p.casulos and p.tab.livre(4, 3)


def test_robo_e_jogo_usam_as_mesmas_regras():
    """A Partida faz a jogada inteira como a sessão faz por etapas."""
    p1, p2 = Partida(cfg.casa_combina3(10), semente=9), Partida(cfg.casa_combina3(10), semente=9)
    for _ in range(8):
        jogada = p1.tab.dica()
        p1.jogar(*jogada)
        onda = p2.tab.trocar(*jogada)
        p2.usar_jogada()
        while onda:
            p2.aplicar(onda)
            p2.tab.cair()
            onda = p2.tab.proxima_onda()
        ataque = p2.planejar_ataque()
        if ataque:
            p2.aplicar_ataque(ataque)
        elif p2.tab.dica() is None:
            p2.tab.embaralhar()
    assert ids(p1.tab) == ids(p2.tab) and p1.dano == p2.dano and p1.barris == p2.barris


# ---------------------------------------------------------------- sessão
class _AudioMudo:
    def play_sfx(self, *a, **k):
        pass


def _sessao(recursos, casa=1, semente=3):
    return Combina3Session(recursos, _AudioMudo(), None, casa, semente=semente)


def _ate_pronto(s, limite=400):
    for _ in range(limite):
        s.atualizar()
        if s.etapa == PRONTO or s.resultado:
            return
    raise AssertionError('a jogada não terminou')


def _clique(s, tipo, pos):
    extras = {'button': 1} if tipo != pygame.MOUSEMOTION else {'rel': (0, 0), 'buttons': (1, 0, 0)}
    s.tratar_evento(pygame.event.Event(tipo, pos=pos, **extras))


def test_sessao_cumpre_o_contrato_da_casa(recursos):
    s = _sessao(recursos, 5)
    assert s.chefe and s.resultado is None and s.estrelas == 0 and s.moedas_coletadas == 0
    assert s.estado == 'JOGO' and not s.pausado and s.objetivo.startswith('Derrote o Rei-Inseto em 22 jogadas')
    s.desenhar()
    assert s.tela.get_size() == (LARGURA, ALTURA)
    assert casa_em(centro_da_casa(3, 4)) == (3, 4) and casa_em((5, 5)) is None


def test_clicar_em_duas_vizinhas_troca(recursos):
    s = _sessao(recursos)
    a, b = s.tab.dica()
    _clique(s, pygame.MOUSEBUTTONDOWN, centro_da_casa(*a))
    _clique(s, pygame.MOUSEBUTTONUP, centro_da_casa(*a))
    assert s.selecao == a
    _clique(s, pygame.MOUSEBUTTONDOWN, centro_da_casa(*b))
    assert s.etapa == TROCA and s.jogadas == 19 and s.usadas == 1
    for _ in range(8):
        s.atualizar()
        s.desenhar()
    assert s.etapa in (ESTOURO, 'QUEDA', PRONTO)
    _ate_pronto(s)
    assert s.pontos >= 60


def test_arrastar_troca(recursos):
    s = _sessao(recursos)
    a, b = s.tab.dica()
    xa, ya = centro_da_casa(*a)
    _clique(s, pygame.MOUSEBUTTONDOWN, (xa, ya))
    _clique(s, pygame.MOUSEMOTION, (xa + (b[1] - a[1]) * 30, ya + (b[0] - a[0]) * 30))
    assert s.etapa == TROCA and s.usadas == 1


def test_soltar_o_botao_durante_a_pausa_cancela_o_arrasto(recursos):
    s = _sessao(recursos)
    a, b = s.tab.dica()
    xa, ya = centro_da_casa(*a)
    _clique(s, pygame.MOUSEBUTTONDOWN, (xa, ya))
    s.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=(xa + (b[1] - a[1]) * 30, ya + (b[0] - a[0]) * 30),
                                       rel=(0, 0), buttons=(0, 0, 0)))
    assert s.arrasto is None and s.usadas == 0 and s.etapa == PRONTO


def test_balao_de_dica_espera_o_aviso_do_ataque(recursos):
    from flappy_arcade.gameplay.tutorial import GuiaDicas

    class Registro:
        def vista(self, ident):
            return False

        def marcar(self, ident):
            pass
    s = _sessao(recursos)
    s.guia = GuiaDicas(Registro())
    s.guia.pedir('c3_chefe')
    s.aviso = ('OS CHEFÕES ATACARAM!', 1.0)
    for _ in range(20):
        s.atualizar()
    assert s.guia.atual is None                                   # esperou
    for _ in range(20):
        s.atualizar()
    assert s.guia.atual == 'c3_chefe'


def test_troca_que_nao_combina_nao_gasta_jogada(recursos):
    s = _sessao(recursos)
    validas = set(s.tab.jogadas())
    ruim = next(((l, c), (l, c + 1)) for l in range(8) for c in range(6) if ((l, c), (l, c + 1)) not in validas)
    assert not s.tentar(*ruim)
    assert s.jogadas == 20 and s.etapa == PRONTO and s.visual.vaivem is not None
    for _ in range(12):
        s.atualizar()
        s.desenhar()
    assert s.visual.vaivem is None


def test_teclado_move_o_cursor_segura_e_troca(recursos):
    s = _sessao(recursos)
    a, b = s.tab.dica()
    s.cursor = a
    s._tecla(pygame.K_SPACE)
    assert s.selecao == a
    s._tecla(pygame.K_RIGHT if b[1] > a[1] else pygame.K_DOWN)
    assert s.usadas == 1 and s.selecao is None


def test_bater_a_meta_da_vitoria_estrelas_e_moedas(recursos):
    s = _sessao(recursos)
    for _ in range(40):
        if s.resultado:
            break
        assert s.acao_principal()
        _ate_pronto(s)
    assert s.resultado in ('VITORIA', 'DERROTA')
    if s.resultado == 'VITORIA':
        assert s.partida.cumprida()
        assert s.estrelas == cfg.estrelas_combina3(20, s.usadas)
        assert s.moedas_coletadas >= cfg.MOEDAS_POR_VITORIA
    else:
        assert s.jogadas == 0 and s.estrelas == 0


def test_vitoria_e_derrota_garantidas(recursos, monkeypatch):
    facil = cfg.CasaCombina3(20, ((cfg.PONTOS, 60),))
    monkeypatch.setattr(cfg, 'casa_combina3', lambda n: facil)
    s = _sessao(recursos)
    s.acao_principal()
    _ate_pronto(s)
    assert s.resultado == 'VITORIA' and s.estrelas == 3 and s.usadas == 1
    assert s.moedas_coletadas >= cfg.MOEDAS_POR_VITORIA + 19 // cfg.JOGADAS_POR_MOEDA
    impossivel = cfg.CasaCombina3(2, ((cfg.PONTOS, 10 ** 9),))
    monkeypatch.setattr(cfg, 'casa_combina3', lambda n: impossivel)
    s = _sessao(recursos)
    for _ in range(2):
        s.acao_principal()
        _ate_pronto(s)
    assert s.resultado == 'DERROTA' and s.jogadas == 0


def test_nao_aceita_jogada_durante_a_animacao(recursos):
    s = _sessao(recursos)
    assert s.acao_principal()
    assert not s.acao_principal() and s.usadas == 1       # ainda trocando


def test_dica_aparece_depois_de_parado(recursos):
    s = _sessao(recursos)
    for _ in range(int(5.2 * 30)):
        s.atualizar()
    assert s.dica == s.tab.dica()
    s.desenhar()


@pytest.mark.parametrize('efeitos', [True, False])
def test_partida_inteira_desenha(recursos, efeitos):
    s = _sessao(recursos, 25, semente=7)
    s.preparar_recompensas(efeitos=efeitos)
    s.tab.grade[1][0].especial = LINHA_H                 # (a casa 25 tem pedras nos cantos)
    s.tab.grade[1][1].especial = OVO
    s.tab.grade[1][2].especial, s.tab.grade[1][2].tipo = ARCO, ''
    for _ in range(900):
        if s.resultado:
            break
        if s.etapa == PRONTO:
            s.acao_principal()
        s.atualizar()
        s.desenhar()
    assert s.resultado


def test_casa_de_chefe_anima_o_ataque(recursos, monkeypatch):
    casa = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('dupla', 9999, 1, casulos=1, barris=1))
    monkeypatch.setattr(cfg, 'casa_combina3', lambda n: casa)
    s = _sessao(recursos, 25)
    assert s.acao_principal()
    for _ in range(300):
        s.atualizar()
        s.desenhar()
        if s.etapa == ATAQUE:
            break
    assert s.etapa == ATAQUE and len(s.visual.voos) == 2 and 'ATACARAM' in s.aviso[0]
    assert not s.partida.casulos and not s.partida.barris               # ainda voando
    _ate_pronto(s)
    assert len(s.partida.casulos) == 1 and len(s.partida.barris) == 1 and s.partida.dano > 0
    s.desenhar()


@pytest.mark.parametrize('casa', [1, 2, 4, 5, 6, 11, 13, 14, 20, 25])
def test_painel_de_cada_tipo_de_casa_desenha(recursos, casa):
    s = _sessao(recursos, casa)
    for _ in range(3):
        s.acao_principal()
        _ate_pronto(s)
        s.desenhar()
    assert s.usadas == 3 or s.resultado
    assert len(s.partida.progresso()) == len(cfg.casa_combina3(casa).objetivos)


# ---------------------------------------------------------------- integração
def test_mapa_no_menu_mas_fora_do_arcade():
    assert 'combina3' in MAPAS and ORDEM_MAPAS[-1] == 'combina3'
    assert all(etapa_arcade(n).estilo != 'combina3' for n in range(1, 26))


def test_casa_abre_pela_cena_de_casa(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    from flappy_arcade.scenes.level_scene import LevelScene
    from flappy_arcade.scenes.map_scene import MapScene
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    facil = cfg.CasaCombina3(20, ((cfg.PONTOS, 60),))
    monkeypatch.setattr(cfg, 'casa_combina3', lambda n: facil)
    ctx = modulo_app.App().ctx
    mapa = MapScene(ctx, 'combina3')
    ctx.scenes.push(mapa)
    tela = pygame.Surface((LARGURA, ALTURA))
    mapa.update(1 / 60)
    mapa.draw(tela)
    cena = LevelScene(ctx, 'combina3', 1)
    ctx.scenes.push(cena)
    cena.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=' ', scancode=44))
    s = cena.session
    assert s.acao_principal()
    for _ in range(300):
        cena.update(1 / 30)
        cena.draw(tela)
        if s.resultado:
            break
    for _ in range(5):
        cena.update(1 / 30)
    assert s.resultado == 'VITORIA'
    assert ctx.progress.estrelas('combina3', 1) == 3 and ctx.progress.liberada('combina3', 2)
    assert ctx.wallet.saldo == s.moedas_coletadas + cena.bonus > 0
