"""Prévia de conferência das artes importadas (usada por importar_artes.py --previa).

Skins sobre o céu do jogo, ao lado do pássaro original (referência de
tamanho), e cada cenário montado como fundo de tela com canos, chão e pássaro.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'src'))

import pygame  # noqa: E402

POR_LINHA, CELULA_L, CELULA_A = 12, 126, 104
MINIATURA = (140, 209)


def _imagem(caminho, fator=1):
    img = pygame.image.load(str(caminho)).convert_alpha()
    return pygame.transform.scale(img, (img.get_width() * fator, img.get_height() * fator)) if fator > 1 else img


def gerar_previa(destino, skins, times, cenarios):
    pygame.init()
    pygame.display.set_mode((1, 1))
    from flappy_arcade.gameplay.scenery import montar_retrato
    imgs = RAIZ / 'assets' / 'imgs'
    ceu = _imagem(imgs / 'bg.png', 2)
    chao = _imagem(imgs / 'base.png', 2)
    cano = _imagem(imgs / 'pipe.png', 2)
    original = _imagem(imgs / 'bird2.png', 2)
    fonte = pygame.font.Font(None, 22)
    titulo = pygame.font.Font(None, 34)
    itens = [('Original', original)] + [
        (nome, _imagem(RAIZ / 'assets' / 'skins' / arquivo)) for nome, arquivo, *_ in skins + times]
    linhas_skin = -(-len(itens) // POR_LINHA)
    altura_cenarios = 2 * (MINIATURA[1] + 50)
    tela = pygame.Surface((POR_LINHA * CELULA_L + 20, 60 + linhas_skin * CELULA_A + 70 + altura_cenarios))
    tela.fill((40, 30, 36))
    tela.blit(titulo.render(f'SKINS ({len(itens) - 1})', True, (255, 225, 90)), (12, 14))
    for i, (nome, img) in enumerate(itens):
        x, y = 10 + (i % POR_LINHA) * CELULA_L, 50 + (i // POR_LINHA) * CELULA_A
        tela.blit(ceu, (x, y), (40, 300, CELULA_L - 6, CELULA_A - 6))
        tela.blit(img, img.get_rect(midbottom=(x + CELULA_L // 2 - 3, y + 74)))
        rotulo = fonte.render(nome, True, (255, 255, 255))
        tela.blit(rotulo, rotulo.get_rect(midtop=(x + CELULA_L // 2 - 3, y + 78)))
        if i:
            tela.blit(fonte.render(str(i), True, (30, 60, 70)), (x + 4, y + 3))
    y0 = 60 + linhas_skin * CELULA_A + 20
    tela.blit(titulo.render(f'CENÁRIOS ({len(cenarios)})', True, (255, 225, 90)), (12, y0))
    for i, (nome, arquivo, *_ , periodo, _aviso) in enumerate(cenarios):
        fundo = montar_retrato(_imagem(RAIZ / 'assets' / 'cenarios' / arquivo))
        fundo.blit(cano, (360, 520))
        fundo.blit(pygame.transform.flip(cano, False, True), (360, 290 - cano.get_height()))
        fundo.blit(chao, (0, 760))
        fundo.blit(original, (170, 380))
        x, y = 10 + (i % 10) * (MINIATURA[0] + 12), y0 + 40 + (i // 10) * (MINIATURA[1] + 50)
        tela.blit(pygame.transform.smoothscale(fundo, MINIATURA), (x, y))
        tela.blit(fonte.render(f'C{i + 1} {nome}', True, (255, 255, 255)), (x, y + MINIATURA[1] + 5))
        tela.blit(fonte.render(periodo.split()[2], True, (190, 190, 200)), (x, y + MINIATURA[1] + 22))
    pygame.image.save(tela, str(destino))
