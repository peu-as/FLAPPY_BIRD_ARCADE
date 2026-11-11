"""Fase 15: modo Estilingue (física de arremesso) e os novos botões do menu."""
import math
import random

import pygame
import pytest

from flappy_arcade.config import estilingue as cfg
from flappy_arcade.config.constants import ALTURA, LARGURA, Y_CHAO
from flappy_arcade.config.levels import CASAS, MAPAS, ORDEM_MAPAS, tem_chefe
from flappy_arcade.gameplay.estilingue.mundo import Mundo
from flappy_arcade.gameplay.estilingue.sessao import ANCORA, MIRA, SOBREVOO, VOO, EstilingueSession

DT = 1 / 30


def _vazia(**extras):
    return cfg.CasaEstilingue(('comum',), (), **extras)


def rodar(mundo, segundos):
    for _ in range(round(segundos / DT)):
        mundo.passo(DT)


# ---------------------------------------------------------------- tabela das casas
def test_vinte_e_cinco_casas_com_chefoes_no_lugar():
    assert len(cfg.CASAS_ESTILINGUE) == CASAS == 25
    for numero, casa in enumerate(cfg.CASAS_ESTILINGUE, 1):
        assert bool(casa.chefe) == tem_chefe(numero), numero
        assert 3 <= len(casa.passaros) <= 5
        assert all(p in cfg.PASSAROS for p in casa.passaros)
        fortalezas = sum(m[0] == 'fortaleza' for m in casa.modulos)
        assert len([c for c in casa.chefe.split('+') if c]) <= fortalezas


def test_habilidades_aparecem_aos_poucos():
    primeira = {}
    for numero, casa in enumerate(cfg.CASAS_ESTILINGUE, 1):
        for tipo in casa.passaros:
            primeira.setdefault(tipo, numero)
    assert primeira == {'comum': 1, 'pena': 4, 'foguete': 8, 'ovo': 12}


@pytest.mark.parametrize('numero', range(1, 26))
def test_fortalezas_ficam_de_pe_sozinhas(numero):
    """Sem lançar nada, nada cai nem quebra (a casa começa estável)."""
    mundo = Mundo(cfg.casa_estilingue(numero))
    posicoes = {id(p): tuple(p.posicao) for p in mundo.pecas}
    rodar(mundo, 3)
    assert not [e for e in mundo.consumir_eventos() if e[0] == 'quebrou']
    assert not mundo.em_movimento()
    for p in mundo.pecas:
        x0, y0 = posicoes[id(p)]
        assert math.hypot(p.posicao.x - x0, p.posicao.y - y0) < 3, (numero, p.tipo)
        assert 600 < p.posicao.x < cfg.LARGURA_MUNDO - 100 and p.posicao.y < Y_CHAO


def test_estrelas_pelos_passaros_que_sobraram():
    assert [cfg.estrelas_estilingue(3, u) for u in (1, 2, 3)] == [3, 2, 1]
    assert [cfg.estrelas_estilingue(5, u) for u in (1, 3, 4, 5)] == [3, 3, 2, 1]


# ---------------------------------------------------------------- dano e materiais
def _bater(material, velocidade):
    mundo = Mundo(_vazia())
    bloco = mundo.bloco(material, 600, 0, 40, 80)
    rodar(mundo, 0.5)
    mundo.lancar('comum', (480, Y_CHAO - 40), (velocidade, 0))
    rodar(mundo, 1.0)
    return bloco


def test_materiais_tem_resistencias_diferentes():
    assert _bater('gelo', 500).morta
    assert not _bater('madeira', 500).morta and _bater('madeira', 750).morta
    pedra = _bater('pedra', 1000)
    assert not pedra.morta and 0.2 < pedra.dano < 0.6         # pedra racha, mas aguenta umas 3 batidas


def test_encostar_devagar_nao_quebra():
    assert not _bater('gelo', 150).morta


def test_barril_explode_e_derruba_em_volta():
    mundo = Mundo(_vazia())
    barril = mundo.barril(600)
    inseto = mundo.inseto(680, 0)
    outro = mundo.barril(720)                                  # explosão em cadeia
    longe = mundo.inseto(1300, 0)
    rodar(mundo, 0.5)
    mundo.ferir(barril, 999)
    rodar(mundo, 0.5)
    assert barril.morta and inseto.morta and outro.morta
    assert not longe.morta
    assert sum(1 for e in mundo.consumir_eventos() if e[0] == 'explodiu') == 2


def test_peca_que_sai_do_mundo_conta_como_derrubada():
    mundo = Mundo(_vazia())
    inseto = mundo.inseto(700, 0)
    inseto.corpo.position = (-400, 300)
    mundo.passo(DT)
    assert inseto.morta


# ---------------------------------------------------------------- habilidades
def test_pena_dupla_vira_tres():
    mundo = Mundo(_vazia())
    p = mundo.lancar('pena', ANCORA, (700, -500))
    mundo.passo(DT)
    assert mundo.ativar(p)
    filhotes = mundo.passaros_no_ar
    assert len(filhotes) == 3 and p.morta and all(f.filhote for f in filhotes)
    direcoes = sorted(math.degrees(math.atan2(f.corpo.velocity.y, f.corpo.velocity.x)) for f in filhotes)
    assert direcoes[2] - direcoes[0] == pytest.approx(2 * cfg.PENA_ABERTURA, abs=1)
    assert not any(mundo.ativar(f) for f in filhotes)            # filhotes não repetem


def test_semente_foguete_dispara_e_fura_madeira():
    mundo = Mundo(_vazia())
    p = mundo.lancar('foguete', ANCORA, (500, -300))
    mundo.passo(DT)
    assert mundo.ativar(p) and p.disparou
    assert p.corpo.velocity.length == pytest.approx(cfg.FOGUETE_VELOCIDADE, rel=0.02)
    assert not mundo.ativar(p)                                   # uma vez só


def test_ovo_nova_explode_no_clique_ou_sozinho_depois_de_bater():
    mundo = Mundo(_vazia())
    p = mundo.lancar('ovo', (600, Y_CHAO - 200), (0, 0))
    rodar(mundo, 0.3)
    assert mundo.ativar(p) and p.morta
    mundo.passo(DT)
    assert any(e[0] == 'explodiu' for e in mundo.consumir_eventos())
    mundo = Mundo(_vazia())
    p = mundo.lancar('ovo', (600, Y_CHAO - 60), (0, 300))       # cai no chão e não clica
    rodar(mundo, 0.4)
    assert p.bateu and not p.morta
    rodar(mundo, cfg.OVO_ESPERA_APOS_BATER + 0.2)
    assert p.morta and any(e[0] == 'explodiu' for e in mundo.consumir_eventos())


def test_pena_e_foguete_so_antes_de_bater():
    mundo = Mundo(_vazia())
    p = mundo.lancar('pena', (600, Y_CHAO - 60), (0, 300))
    rodar(mundo, 0.4)
    assert p.bateu and not mundo.ativar(p)


# ---------------------------------------------------------------- regras gerais
def test_mesma_jogada_mesmo_resultado_e_nada_do_random_do_jogo():
    def jogada():
        mundo = Mundo(cfg.casa_estilingue(6))
        mundo.lancar('comum', ANCORA, (850, -420))
        rodar(mundo, 6)
        return [(p.tipo, round(p.posicao.x, 3), round(p.posicao.y, 3), p.morta) for p in mundo.pecas]
    random.seed(3)
    estado = random.getstate()
    primeira = jogada()
    assert random.getstate() == estado
    assert jogada() == primeira


def test_pontos_dos_materiais():
    for material in cfg.MATERIAIS:
        assert cfg.MATERIAIS[material].pontos > 0
    assert cfg.MATERIAIS['gelo'].vida < cfg.MATERIAIS['madeira'].vida < cfg.MATERIAIS['pedra'].vida


# ---------------------------------------------------------------- sessão
class _AudioMudo:
    def play_sfx(self, *a, **k):
        pass


def _sessao(recursos, casa=1):
    return EstilingueSession(recursos, _AudioMudo(), None, casa)


def test_sessao_cumpre_o_contrato_da_casa(recursos):
    s = _sessao(recursos, 5)
    assert s.chefe and s.resultado is None and s.estrelas == 0 and s.moedas_coletadas == 0
    assert 'chefão' in s.objetivo and '4 pássaros' in s.objetivo
    assert s.estado == 'JOGO' and not s.pausado
    s.desenhar()
    assert s.tela.get_size() == (LARGURA, ALTURA)
    assert s.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, mod=0, unicode='', scancode=0))


def test_sobrevoo_e_pular(recursos):
    s = _sessao(recursos)
    assert s.etapa == SOBREVOO and s.camera > 0                  # começa mostrando a fortaleza
    s.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(100, 100), button=1))
    assert s.etapa == MIRA
    for _ in range(40):
        s.atualizar()
    assert s.camera < 5                                          # volta para o estilingue


def _ate_acabar(s, limite=900):
    for _ in range(limite):
        s.atualizar()
        if s.resultado or s.etapa == MIRA:
            return


def test_arrastar_com_o_mouse_lanca(recursos):
    s = _sessao(recursos)
    s.etapa = MIRA
    s.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(300, 500), button=1))
    s.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=(210, 560), rel=(0, 0), buttons=(1, 0, 0)))
    assert s.puxada == (-90, 60) and s.trajetoria(s.puxada)
    s.desenhar()
    s.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(210, 560), button=1))
    assert s.etapa == VOO and s.usados == 1 and len(s.fila) == 2
    v = s.atual.corpo.velocity
    assert v.x > 0 and v.y < 0                                   # puxou para trás e para baixo: vai para a frente e para cima


def test_o_voo_segue_a_mira(recursos):
    """Fase 18 (verificação independente): o pássaro sai pela forquilha, de onde a mira parte."""
    for puxada in ((-90, 60), (-20, 105), (-108, 10)):            # médio, quase vertical, quase reto
        s = _sessao(recursos)
        s.etapa = MIRA
        mira = s.trajetoria(puxada)
        assert s.lancar(puxada)
        corpo = s.atual.corpo
        assert (corpo.position.x, corpo.position.y) == pytest.approx(ANCORA)
        assert corpo.position.y < Y_CHAO - 100                     # longe do chão
        vx, vy = s.velocidade_da_puxada(puxada)

        def curva(t):                                             # a mesma conta da mira
            return ANCORA[0] + vx * t, ANCORA[1] + vy * t + cfg.GRAVIDADE * t * t / 2
        assert mira[0] == pytest.approx(curva(0.055))
        erros = []
        for quadro in range(1, 13):                               # ~0,4 s de voo
            s.mundo.passo(1 / 30)
            p = s.atual.corpo.position
            x, y = curva(quadro / 30)
            erros.append(((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5)
        assert max(erros) < 8, (puxada, erros)
        assert not s.atual.bateu                                  # não nasce encostado no chão


def test_soltar_o_botao_durante_a_pausa_cancela_o_arrasto(recursos):
    s = _sessao(recursos)
    s.etapa = MIRA
    s.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(300, 500), button=1))
    s.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=(240, 540), rel=(0, 0), buttons=(1, 0, 0)))
    assert s.arrastando
    s.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=(200, 560), rel=(0, 0), buttons=(0, 0, 0)))
    assert not s.arrastando and s.puxada is None and s.usados == 0


def test_fila_de_passaros_cabe_na_tela(recursos):
    s = _sessao(recursos, 25)                                      # 5 pássaros
    s.etapa = MIRA
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    s.visual.desenhar_fila(tela, 0, s.fila, None, preparado=True)
    colunas = [x for x in range(LARGURA) if any(tela.get_at((x, y)).a for y in range(ALTURA - 140, ALTURA - 60))]
    assert colunas and min(colunas) > 0                            # nada cortado na borda esquerda


def test_textos_das_casas_com_chefoes(recursos):
    s = _sessao(recursos, 25)
    assert s.objetivo.startswith('Derrube os dois chefões e os')
    s.desenhar()


def test_puxada_curta_nao_lanca(recursos):
    s = _sessao(recursos)
    s.etapa = MIRA
    s.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(300, 500), button=1))
    s.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(305, 503), button=1))
    assert s.etapa == MIRA and s.usados == 0


def test_vencer_uma_casa_pelo_teclado_da_estrelas_e_moedas(recursos):
    s = _sessao(recursos, 1)
    s.etapa = MIRA
    for tecla in (pygame.K_DOWN,) * 6 + (pygame.K_RIGHT,) * 5 + (pygame.K_SPACE,):
        s.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=tecla, mod=0, unicode='', scancode=0))
    assert s.usados == 1
    _ate_acabar(s)
    assert s.resultado == 'VITORIA' and s.estrelas == 3          # um tiro rasante derruba a torre da casa 1
    assert s.moedas_coletadas >= cfg.MOEDAS_POR_INSETO + 2 * cfg.MOEDAS_POR_PASSARO_SOBRANDO


def test_sem_passaros_e_com_insetos_e_derrota(recursos):
    s = _sessao(recursos, 1)
    s.etapa = MIRA
    while s.fila and not s.resultado:
        s.lancar(s.puxada_do_teclado(80, 0.3))                   # para cima, fraco: não acerta nada
        _ate_acabar(s)
    assert s.resultado == 'DERROTA' and s.estrelas == 0


@pytest.mark.parametrize('efeitos', [True, False])
def test_todas_as_casas_desenham(recursos, efeitos):
    for numero in range(1, 26):
        s = _sessao(recursos, numero)
        s.preparar_recompensas(efeitos=efeitos)
        s.etapa = MIRA
        s.lancar(s.puxada_do_teclado(25, 1.0))
        for _ in range(45):
            s.atualizar()
            s.desenhar()


# ---------------------------------------------------------------- menu e mapa
def test_mapa_do_estilingue_registrado():
    assert 'estilingue' in ORDEM_MAPAS and MAPAS['estilingue'].subtitulo == 'Estilingue'


def test_casa_do_estilingue_abre_pela_cena_de_casa(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    from flappy_arcade.scenes.level_scene import LevelScene
    from flappy_arcade.scenes.map_scene import MapScene
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    ctx = modulo_app.App().ctx
    ctx.scenes.push(MapScene(ctx, 'estilingue'))
    cena = LevelScene(ctx, 'estilingue', 1)
    ctx.scenes.push(cena)
    tela = pygame.Surface((LARGURA, ALTURA))
    cena.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=' ', scancode=44))
    s = cena.session
    s.etapa = MIRA
    s.lancar(s.puxada_do_teclado(-2 * 6 + 35, 0.8 + 5 * 0.04))
    for _ in range(600):
        cena.update(1 / 30)
        cena.draw(tela)
        if s.resultado:
            break
    for _ in range(5):
        cena.update(1 / 30)
    assert s.resultado == 'VITORIA'
    assert ctx.progress.estrelas('estilingue', 1) == 3 and ctx.progress.liberada('estilingue', 2)
    assert ctx.wallet.saldo == s.moedas_coletadas + cena.bonus > 0
