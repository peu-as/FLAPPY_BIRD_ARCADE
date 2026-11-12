"""Fase 22: skin lendária (Wilson Luciano), efeitos lendários e ícone do executável."""
import random
import struct

import pygame
import pytest

from flappy_arcade.config.constants import ALTURA, LARGURA, Y_CHAO
from flappy_arcade.config.scenarios import CENARIOS
from flappy_arcade.config.skins import (CORES_RARIDADE, FAIXAS_PRECO, FANTASIAS, LENDARIA, NOMES_RARIDADE,
                                        POR_CATEGORIA, POR_ID, SKINS)
from flappy_arcade.core.paths import ICONES, PERSONAGENS
from flappy_arcade.gameplay.flappy import Passaro
from flappy_arcade.gameplay.lendaria import (POSES_VITRINE, QUADROS_POR_POSE_VITRINE, VY_MERGULHO, VY_PULO,
                                             escolher_pose)
from flappy_arcade.gameplay.skins import SkinVisual

POSES = {'idle', 'correr', 'pular', 'desviar', 'atacar', 'tomba', 'vitoria', 'morrer', 'retrato'}


# ---------------------------------------------------------------- catálogo e loja
def test_wilson_e_a_unica_lendaria_e_a_mais_cara_do_jogo():
    wilson = POR_ID['wilson']
    assert (wilson.nome, wilson.raridade, wilson.tipo, wilson.efeito) == \
        ('Wilson Luciano', LENDARIA, 'personagem', 'lendario')
    assert [s.id for s in SKINS if s.raridade == LENDARIA] == ['wilson']
    outros = [s.preco for s in SKINS if s.id != 'wilson'] + [c.preco for c in CENARIOS]
    assert wilson.preco > max(outros)                       # mais cara que qualquer skin ou cenário
    minimo, maximo = FAIXAS_PRECO[LENDARIA]
    assert minimo <= wilson.preco <= maximo


def test_lendaria_e_a_raridade_maxima():
    assert list(FAIXAS_PRECO)[-1] == LENDARIA                # a última (mais alta) das faixas
    assert NOMES_RARIDADE[LENDARIA] == 'LENDÁRIA' and LENDARIA in CORES_RARIDADE
    radical_max = FAIXAS_PRECO['radical'][1]
    assert FAIXAS_PRECO[LENDARIA][0] > radical_max


def test_lendaria_abre_a_aba_fantasias():
    assert POR_CATEGORIA[FANTASIAS][0].id == 'wilson'


# ---------------------------------------------------------------- artes
def test_todas_as_poses_foram_importadas(recursos):
    arquivos = {p.stem for p in (PERSONAGENS / 'wilson').glob('*.png')}
    assert arquivos == POSES
    poses = recursos.poses_personagem('wilson')
    for nome, img in poses.items():
        largura, altura = img.get_size()
        assert 20 <= largura <= 80 and 20 <= altura <= 90, f'{nome}: {largura}x{altura}'
        assert img.get_at((0, 0)).a == 0, f'{nome}: o fundo ciano não saiu'


def test_retrato_vai_nos_cartoes_e_no_estilingue(recursos):
    visual = SkinVisual('wilson', recursos)
    assert visual.sprite_para(0) is recursos.poses_personagem('wilson')['retrato']
    assert visual.sprite_para(2) is visual.sprite_para(0)


# ---------------------------------------------------------------- poses
@pytest.mark.parametrize('vy, no_chao, pose', [
    (-9.0, False, 'pular'), (VY_PULO - 0.1, False, 'pular'), (VY_PULO, False, 'correr'),
    (0.0, False, 'correr'), (VY_MERGULHO, False, 'correr'), (VY_MERGULHO + 0.1, False, 'desviar'),
    (16.0, False, 'desviar'), (16.0, True, 'morrer'), (-9.0, True, 'morrer')])
def test_pose_segue_o_voo(vy, no_chao, pose):
    assert escolher_pose(vy, no_chao) == pose


def test_pose_no_chao_e_deitada(recursos):
    p = Passaro(recursos)
    p.skin = SkinVisual('wilson', recursos)
    p.y = Y_CHAO - p.sprite.get_height()
    p.desenhar(pygame.Surface((LARGURA, ALTURA)))
    assert p.skin.lendaria.pose_atual == 'morrer'


def test_vitrine_reveza_as_poses(recursos):
    visual = SkinVisual('wilson', recursos)
    visual.vitrine = True
    p = Passaro(recursos)
    p.skin = visual
    tela = pygame.Surface((LARGURA, ALTURA))
    vistas = set()
    for _ in range(QUADROS_POR_POSE_VITRINE * len(POSES_VITRINE)):
        p.desenhar(tela)
        vistas.add(visual.lendaria.pose_atual)
    assert vistas == set(POSES_VITRINE)


# ---------------------------------------------------------------- regra de ouro: só aparência
def test_fisica_e_colisao_identicas_com_a_lendaria(recursos):
    """Mesmas batidas de asa, com e sem a skin: posição, velocidade e retângulo iguais a cada quadro."""
    sem, com = Passaro(recursos), Passaro(recursos)
    com.skin = SkinVisual('wilson', recursos)
    tela = pygame.Surface((LARGURA, ALTURA))
    for quadro in range(240):
        if quadro % 13 == 0:
            sem.pular()
            com.pular()
        sem.atualizar()
        com.atualizar()
        com.desenhar(tela)
        assert (com.x, com.y, com.vy, com.indice) == (sem.x, sem.y, sem.vy, sem.indice)
        assert com.retangulo() == sem.retangulo()
    assert com.sprite is sem.sprite                     # a máscara de colisão é a do pássaro original


def test_efeitos_nao_usam_o_random_do_jogo(recursos):
    p = Passaro(recursos)
    p.skin = SkinVisual('wilson', recursos)
    tela = pygame.Surface((LARGURA, ALTURA))
    random.seed(2026)
    antes = random.getstate()
    for quadro in range(90):
        if quadro % 10 == 0:
            p.pular()
        p.atualizar()
        p.desenhar(tela)
    assert random.getstate() == antes                   # o sorteio dos canos (golden master) não muda


# ---------------------------------------------------------------- efeitos lendários
def _voar(recursos, efeitos, quadros=60):
    visual = SkinVisual('wilson', recursos)
    visual.efeitos = efeitos
    p = Passaro(recursos)
    p.skin = visual
    tela = pygame.Surface((LARGURA, ALTURA))
    ondas = 0
    for quadro in range(quadros):
        if quadro % 15 == 0:
            p.pular()
        p.atualizar()
        p.desenhar(tela)
        ondas = max(ondas, len(visual.lendaria.ondas))
    return visual.lendaria, ondas


def test_efeitos_lendarios_aparecem(recursos):
    lendaria, ondas = _voar(recursos, efeitos=True)
    assert len(lendaria.faiscas) > 10            # faíscas saindo das costas
    assert len(lendaria.rastro) == lendaria.rastro.maxlen    # rastro dourado
    assert ondas >= 1                            # onda dourada ao bater asas


def test_efeitos_somem_com_os_efeitos_visuais_desligados(recursos):
    lendaria, ondas = _voar(recursos, efeitos=False)
    assert not lendaria.faiscas and not lendaria.rastro and ondas == 0


def test_faiscas_tem_limite(recursos):
    lendaria, _ = _voar(recursos, efeitos=True, quadros=400)
    assert len(lendaria.faiscas) <= 70 + 12      # MAX_FAISCAS + uma explosão


# ---------------------------------------------------------------- ícone
def ler_tamanhos_ico(caminho):
    """Tamanhos gravados num .ico (só biblioteca padrão: o jogo e os testes não precisam do Pillow)."""
    bruto = caminho.read_bytes()
    reservado, tipo, quantidade = struct.unpack_from('<HHH', bruto, 0)
    assert (reservado, tipo) == (0, 1), 'não é um arquivo .ico'
    return [struct.unpack_from('<B', bruto, 6 + 16 * i)[0] or 256 for i in range(quantidade)]


def test_icone_do_executavel_tem_todos_os_tamanhos():
    ico = ICONES / 'flappy_arcade.ico'
    assert ico.exists(), 'rode: python tools/gerar_icone.py'
    assert sorted(ler_tamanhos_ico(ico)) == [16, 24, 32, 48, 64, 128, 256]


def test_icone_da_janela(recursos):
    icone = recursos.icone_janela()
    assert icone.get_size() == (64, 64)
    assert icone is not recursos.passaros['dia'][0]
