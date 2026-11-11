"""Fase 18: dicas de tutorial nos modos novos (uma vez cada, guardadas no save)."""
import json

import pygame
import pytest

from flappy_arcade.config.tutorial import DICAS
from flappy_arcade.gameplay.tutorial import DURACAO, LARGURA_BALAO, LEITURA_MINIMA, GuiaDicas
from flappy_arcade.systems import apresentacao
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.tutorial import RegistroDicas

DT = 1 / 30


class Registro:
    def __init__(self, vistas=()):
        self.vistas = list(vistas)

    def vista(self, ident):
        return ident in self.vistas

    def marcar(self, ident):
        self.vistas.append(ident)


def passar(guia, segundos):
    for _ in range(round(segundos / DT)):
        guia.atualizar(DT)


def test_sem_registro_nenhuma_dica():
    guia = GuiaDicas()
    guia.pedir('c3_trocar')
    passar(guia, 1)
    assert guia.atual is None


def test_nome_errado_da_erro():
    with pytest.raises(KeyError):
        GuiaDicas(Registro()).pedir('c3_trocra')


def test_uma_por_vez_na_ordem_e_so_uma_vez():
    registro = Registro(['c3_gelo'])
    guia = GuiaDicas(registro)
    for ident in ('c3_trocar', 'c3_gelo', 'c3_chefe', 'c3_trocar'):
        guia.pedir(ident)
    passar(guia, DT)
    assert guia.atual == 'c3_trocar' and guia.fila == ['c3_chefe'] and 'c3_trocar' in registro.vistas
    passar(guia, DURACAO + 0.1)
    assert guia.atual == 'c3_chefe'
    passar(guia, DURACAO + 0.1)
    assert guia.atual is None
    guia.pedir('c3_trocar')
    passar(guia, DT)
    assert guia.atual is None                                    # já vista


def test_acao_do_jogador_fecha_so_depois_de_dar_tempo_de_ler(pygame_pronto):
    guia = GuiaDicas(Registro())
    guia.pedir('est_mirar')
    passar(guia, 1.0)
    guia.acao()
    passar(guia, 0.5)
    assert guia.atual == 'est_mirar'                             # cedo demais: continua
    passar(guia, LEITURA_MINIMA)
    guia.acao()
    passar(guia, 0.5)
    assert guia.atual is None


@pytest.mark.parametrize('ident', sorted(DICAS))
def test_balao_cabe_na_tela(pygame_pronto, ident):
    guia = GuiaDicas(Registro())
    guia.pedir(ident)
    passar(guia, 0.5)
    img = guia._imagem
    assert img.get_width() == LARGURA_BALAO <= 575 and img.get_height() <= 24 + 26 * 3 + 8, ident
    guia.desenhar(pygame.Surface((575, 860)), 190)


def test_registro_guarda_no_save_e_save_antigo_ganha_a_secao(tmp_path):
    caminho = tmp_path / 'save.json'
    caminho.write_text(json.dumps({'version': 2, 'wallet': {'coins': 7}}), encoding='utf-8')
    save = SaveManager(caminho)
    save.load()
    assert save.data['tutorial'] == {'vistas': []} and save.data['wallet']['coins'] == 7
    registro = RegistroDicas(save)
    registro.marcar('c3_gelo')
    registro.marcar('c3_gelo')
    outro = SaveManager(caminho)
    outro.load()
    assert outro.data['tutorial']['vistas'] == ['c3_gelo'] and RegistroDicas(outro).vista('c3_gelo')


# ---------------------------------------------------------------- nas casas de verdade
@pytest.fixture
def ctx(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    return modulo_app.App().ctx


def jogar_casa(ctx, mapa, casa, segundos):
    from flappy_arcade.scenes.level_scene import LevelScene
    cena = LevelScene(ctx, mapa, casa)
    ctx.scenes.push(cena)
    tela = pygame.Surface((575, 860))
    cena.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=' ', scancode=44))
    vistas = []
    for _ in range(round(segundos / DT)):
        cena.update(DT)
        cena.draw(tela)
        atual = cena.session.guia.atual
        if atual and atual not in vistas:
            vistas.append(atual)
    ctx.scenes.pop()
    return vistas


def test_combina3_ensina_na_primeira_vez_e_nao_repete(ctx):
    mostradas = jogar_casa(ctx, 'combina3', 11, 2 * DURACAO + 1)     # casa com caixas e gelo
    assert mostradas[:2] == ['c3_trocar', 'c3_gelo']                 # (as caixas vêm depois)
    assert ctx.save.data['tutorial']['vistas'][:2] == ['c3_trocar', 'c3_gelo']
    assert 'c3_trocar' not in jogar_casa(ctx, 'combina3', 11, 2)        # já vista
    assert jogar_casa(ctx, 'combina3', 5, 1) == ['c3_chefe']


def test_estilingue_ensina_a_mirar_e_o_passaro_especial(ctx):
    vistas = jogar_casa(ctx, 'estilingue', 2, 4)                       # depois do sobrevoo
    assert vistas[:1] == ['est_mirar']
    feitas = ctx.save.data['tutorial']['vistas']
    assert 'est_mirar' in feitas


def test_modo_apresentacao_mostra_de_novo_e_nao_mexe_no_save_real(ctx):
    jogar_casa(ctx, 'combina3', 1, 1)
    assert ctx.save.data['tutorial']['vistas'] == ['c3_trocar']
    apresentacao.ligar(ctx)
    assert jogar_casa(ctx, 'combina3', 1, 1) == ['c3_trocar']
    apresentacao.desligar(ctx)
    assert ctx.save.data['tutorial']['vistas'] == ['c3_trocar']
