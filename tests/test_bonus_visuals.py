"""Fase 13: visual novo dos bônus nos modos novos. Lógica, raio e duração iguais."""
import random

import pygame
import pytest

import snapshot
from scenarios import FakeClock

from flappy_arcade.config.constants import ALTURA, LARGURA, TIPOS_BONUS
from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.gameplay.bonus_visuals import (DESENHOS, NOMES_NOVOS, EstiloBonus, SessaoComBonusNovos,
                                                  renomear)
from flappy_arcade.gameplay.classic_session import ClassicSession
from flappy_arcade.gameplay.free_mode import FreeSession
from flappy_arcade.gameplay.powerups import CapsulaBonus
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore


def criar(recursos, tmp_path, classe=FreeSession, arquivo='s.json'):
    sv = SaveManager(tmp_path / arquivo)
    sv.load()
    bus = EventBus()
    audio = AudioManager(SettingsStore(sv, bus), recursos.sons, bus)
    clock = FakeClock()
    s = classe(recursos, audio, clock, sv) if classe is FreeSession else classe(recursos, audio, clock)
    if classe is FreeSession:
        s.preparar_recompensas(moedas=False)
    return s, clock


def passo(s, clock, n=1):
    for _ in range(n):
        clock.avancar()
        s.atualizar(1 / 30, clock.ticks())
        s.desenhar()


def ate_a_fase(s, clock, fase):
    s.acao_principal()
    if s.estado == 'CADASTRO':                    # clássico: cadastro antes de jogar
        s.nome_digitado = 'TESTE'
        s.acao_principal()
    passo(s, clock, 5)
    s.iniciar_alerta(fase)
    for _ in range(400):
        if s.estado == fase:
            return
        passo(s, clock)
    raise AssertionError(f'não chegou à fase {fase}')


# ---------------------------------------------------------------- nomes e itens
@pytest.mark.parametrize('velho, novo', [
    ('CAÇA GÊMEO: tiro duplo (absorve 1 golpe)', 'PENA DUPLA: tiro duplo (absorve 1 golpe)'),
    ('BOMBA NOVA: tela limpa!', 'OVO NOVA: tela limpa!'),
    ('TURBO: rápido... e depois superaquece!', 'SEMENTE-FOGUETE: rápido... e depois superaquece!'),
    ('TURBO 7s', 'SEMENTE-FOGUETE 7s'),
    ('BANANA-RANG x3: aperte X para lançar', 'CACHO BUMERANGUE x3: aperte X para lançar'),
    ('PULO DE MOLA: salto maior por 7 s', 'FOLHA-TRAMPOLIM: salto maior por 7 s'),
    ('MOLA 6s', 'FOLHA-TRAMPOLIM 6s'),
    ('SUPERAQUECIDO!', 'SUPERAQUECIDO!'),
])
def test_nomes_novos(velho, novo):
    assert renomear(velho) == novo


def test_um_item_para_cada_bonus_e_cabe_na_area_de_coleta(recursos):
    assert set(DESENHOS) == set(TIPOS_BONUS) == set(NOMES_NOVOS)
    estilo = EstiloBonus(recursos)
    for tipo, item in estilo.itens.items():
        assert item.get_width() <= 2 * CapsulaBonus.RAIO and item.get_height() <= 2 * CapsulaBonus.RAIO, tipo
        assert pygame.mask.from_surface(item).count() > 150, tipo        # desenho de verdade


def test_logica_dos_bonus_nao_mudou():
    """Raio de coleta e durações continuam os do jogo original."""
    assert CapsulaBonus.RAIO == 17
    assert {t: v[2] for t, v in TIPOS_BONUS.items()} == {
        'GEMEO': None, 'BOMBA': None, 'TURBO': 8.0, 'BUMERANGUE': None, 'MOLA': 7.0}


# ---------------------------------------------------------------- quem recebe o visual novo
@pytest.mark.parametrize('fase', ['GALAGA', 'DONKEY'])
def test_classico_mantem_as_capsulas_e_os_novos_ganham_o_estilo(recursos, tmp_path, fase):
    assert not issubclass(ClassicSession, SessaoComBonusNovos)
    classico, c1 = criar(recursos, tmp_path, ClassicSession)
    ate_a_fase(classico, c1, fase)
    assert getattr(classico, fase.lower()).estilo_bonus is None
    livre, c2 = criar(recursos, tmp_path, arquivo='livre.json')
    ate_a_fase(livre, c2, fase)
    assert isinstance(getattr(livre, fase.lower()).estilo_bonus, EstiloBonus)


def test_dica_e_hud_com_o_nome_novo(recursos, tmp_path):
    s, clock = criar(recursos, tmp_path)
    ate_a_fase(s, clock, 'GALAGA')
    s.galaga._aplicar_bonus('GEMEO')
    passo(s, clock)
    assert s.galaga.dica.startswith('PENA DUPLA')
    assert s.galaga.aviso_bonus.startswith('CAÇA GÊMEO')          # a lógica guarda o texto original


# ---------------------------------------------------------------- regra de ouro
@pytest.mark.parametrize('fase', ['GALAGA', 'DONKEY'])
def test_visual_novo_nao_muda_a_fisica(recursos, tmp_path, monkeypatch, fase):
    monkeypatch.setattr(snapshot, 'IGNORADOS', snapshot.IGNORADOS | {'estilo_bonus', 'coletor'})

    def partida(visual_novo):
        if not visual_novo:
            monkeypatch.setattr(SessaoComBonusNovos, 'desenhar',
                                lambda self: super(SessaoComBonusNovos, self).desenhar())
        random.seed(77)
        s, clock = criar(recursos, tmp_path, arquivo=f'{visual_novo}.json')
        ate_a_fase(s, clock, fase)
        hashes = []
        for i in range(500):
            if fase == 'GALAGA' and s.galaga:
                g = s.galaga
                if i == 20:
                    g._aplicar_bonus('GEMEO')
                    g._aplicar_bonus('TURBO')
                if i == 120:
                    g.soltar_capsula(g.nave_x, 600, 'BOMBA')     # cai na nave: coleta de verdade
                g.nave_x += 3 if (i // 40) % 2 else -3
            if fase == 'DONKEY' and s.donkey:
                d = s.donkey
                if i == 20:
                    d.efeitos.ativar('MOLA', TIPOS_BONUS['MOLA'][2])
                    d.cargas = 3
                if i in (40, 140):
                    d.lancar_bumerangue(s.passaro)
                if s.passaro.y > 420 and i % 2:
                    s.acao_principal()
            passo(s, clock)
            if i % 25 == 0:
                hashes.append(snapshot.hash_estado(s))
        monkeypatch.undo()
        monkeypatch.setattr(snapshot, 'IGNORADOS', snapshot.IGNORADOS | {'estilo_bonus', 'coletor'})
        return hashes, s

    novo, s = partida(True)
    velho, _ = partida(False)
    fase_obj = s.galaga if fase == 'GALAGA' else s.donkey
    assert fase_obj is None or fase_obj.estilo_bonus is not None or s.estado != fase
    assert novo == velho


# ---------------------------------------------------------------- desenho
class _FaseFalsa:
    def __init__(self, recursos):
        from flappy_arcade.gameplay.powerups import EfeitosAtivos
        self.recursos = recursos
        self.gemeo = True
        self.nave_x = LARGURA / 2
        self.efeitos = EfeitosAtivos()
        self.efeitos.ativar('TURBO', 8.0)
        self.onda_bomba = 0.5
        self.centro_bomba = (LARGURA / 2, 700)

    def retangulo_nave(self):
        return self.recursos.nave.get_rect(center=(int(self.nave_x), 740))


@pytest.mark.parametrize('efeitos', [True, False])
def test_efeitos_desenham_e_somem_sem_efeitos_visuais(recursos, efeitos):
    from flappy_arcade.gameplay.flappy import Passaro
    estilo = EstiloBonus(recursos)
    estilo.efeitos = efeitos
    fase, tela = _FaseFalsa(recursos), pygame.Surface((LARGURA, ALTURA))
    passaro = Passaro(recursos)
    bumerangue = {'x': 200.0, 'y': 400.0, 'volta': False, 'angulo': 0.0}
    estado = random.getstate()
    for i in range(30):
        estilo.desenhar_naves(fase, tela)
        fase.onda_bomba = max(0.0, 0.5 - i / 30)
        if fase.onda_bomba:
            estilo.desenhar_onda(fase, tela)
        estilo.desenhar_cascas(tela)
        passaro.vy = -9 if i % 6 == 0 else 2
        estilo.desenhar_mola(tela, passaro)
        bumerangue['x'] += 10
        estilo.desenhar_bumerangues(tela, [bumerangue])
        for tipo in TIPOS_BONUS:
            estilo.desenhar_item(tela, CapsulaBonus(tipo, 100, 100), i / 30)
    assert random.getstate() == estado                          # partículas não mexem no random do jogo
    tem_particulas = bool(estilo.fogo or estilo.penas or estilo.cascas or estilo.aneis)
    assert tem_particulas == efeitos
    estilo.desenhar_bumerangues(tela, [])
    assert estilo.rastros == {}                                 # rastro some com o bumerangue
