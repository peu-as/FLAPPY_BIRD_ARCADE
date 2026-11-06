"""Artes importadas (tools/importar_artes.py): estão todas lá, carregam e cabem no jogo.

As tabelas de nomes são lidas do próprio importador (sem importá-lo, porque ele
precisa de Pillow e numpy, que o jogo não usa).
"""
import ast
import unicodedata
from pathlib import Path

import pygame
import pytest

from flappy_arcade.config.constants import ALTURA, LARGURA, Y_CHAO
from flappy_arcade.gameplay.scenery import montar_retrato

RAIZ = Path(__file__).resolve().parents[1]
SKINS = RAIZ / 'assets' / 'skins'
CENARIOS = RAIZ / 'assets' / 'cenarios'


def _tabelas():
    arvore = ast.parse((RAIZ / 'tools' / 'importar_artes.py').read_text(encoding='utf-8'))
    return {n.targets[0].id: ast.literal_eval(n.value) for n in arvore.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id.startswith('NOMES_')}


def _ident(nome, prefixo=''):
    sem_acento = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode()
    limpo = ''.join(c if c.isalnum() else '_' for c in sem_acento.lower())
    return prefixo + '_'.join(p for p in limpo.split('_') if p)


TABELAS = _tabelas()
IDS_SKINS = [_ident(n) for n in TABELAS['NOMES_SKINS'] if n] + \
            [_ident(n, 'time_') for n in TABELAS['NOMES_TIMES']]
IDS_CENARIOS = [_ident(n) for n in TABELAS['NOMES_CENARIOS']]


def test_quantidades_e_nomes_unicos():
    assert len(IDS_SKINS) == 67 and len(set(IDS_SKINS)) == 67
    assert len(IDS_CENARIOS) == 20 and len(set(IDS_CENARIOS)) == 20
    assert sorted(p.stem for p in SKINS.glob('*.png')) == sorted(IDS_SKINS)
    assert sorted(p.stem for p in CENARIOS.glob('*.png')) == sorted(IDS_CENARIOS)


def test_personagens_de_terceiros_ficam_de_fora():
    excluidos = TABELAS['NOMES_SKINS'][:5]
    assert excluidos == [None] * 5
    for proibido in ('link', 'cavaleiro', 'super_heroi', 'heroi_vermelho', 'padrao', 'batman'):
        assert not (SKINS / f'{proibido}.png').exists()


@pytest.mark.parametrize('ident', IDS_SKINS)
def test_skin_carrega_e_cabe_no_lugar_do_passaro(pygame_pronto, ident):
    img = pygame.image.load(str(SKINS / f'{ident}.png')).convert_alpha()
    assert 50 <= img.get_width() <= 96 and 40 <= img.get_height() <= 110
    assert img.get_width() % 2 == 0 and img.get_height() % 2 == 0     # grade 2x do jogo
    cantos = [img.get_at((x, y)).a for x in (0, img.get_width() - 1) for y in (0, img.get_height() - 1)]
    assert 0 in cantos                                               # fundo transparente
    opacos = pygame.mask.from_surface(img).count() / (img.get_width() * img.get_height())
    assert 0.35 < opacos < 0.9


@pytest.mark.parametrize('ident', IDS_CENARIOS)
def test_cenario_vira_fundo_de_tela(pygame_pronto, ident):
    faixa = pygame.image.load(str(CENARIOS / f'{ident}.png')).convert()
    assert faixa.get_width() == LARGURA and 300 <= faixa.get_height() <= Y_CHAO
    fundo = montar_retrato(faixa)
    assert fundo.get_size() == (LARGURA, ALTURA)
    # a faixa fica apoiada no chão, sem buraco preto no céu
    assert fundo.get_at((LARGURA // 2, Y_CHAO - 1)) == faixa.get_at((LARGURA // 2, faixa.get_height() - 1))
    assert sum(fundo.get_at((LARGURA // 2, 0))[:3]) > 0


def test_artes_pesam_pouco():
    total = sum(p.stat().st_size for p in list(SKINS.glob('*.png')) + list(CENARIOS.glob('*.png')))
    assert total < 4 * 1024 * 1024
    assert not (RAIZ / 'assets' / 'fontes').exists()      # folhas originais ficam em artes/
