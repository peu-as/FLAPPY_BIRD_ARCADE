"""Peças de tela compartilhadas pela Loja e pelos Equipamentos.

Vitrine: prévia combinada (a skin voando sobre o cenário), vista como no
Flappy, na Galaga ou no Donkey. Cartões de cenário com miniatura.
As miniaturas são montadas aos poucos (FilaMiniaturas) para a tela abrir
sem engasgo: no máximo MINIATURAS_POR_QUADRO por quadro.
"""
import math
from collections import OrderedDict

import pygame

from ..config.constants import ALTURA, LARGURA, Y_CHAO
from ..config.scenarios import NOITE, POR_ID as CENARIOS
from ..gameplay.coins import icone_moeda
from ..gameplay.flappy import Passaro
from ..gameplay.scenery import CenarioNaFase
from ..gameplay.skins import SkinVisual
from ..ui.theme import Palette
from ..ui.widgets import desenhar_texto, painel, texto

VISTAS = ('flappy', 'galaga', 'donkey')
NOMES_VISTA = {'flappy': 'FLAPPY', 'galaga': 'GALAGA', 'donkey': 'DONKEY'}
TAMANHO_PREVIA = (250, 190)
# Recorte da tela inteira (575x860) mostrado em cada vista: onde está o cenário.
CORTES = {'flappy': pygame.Rect(17, 340, 541, 411), 'galaga': pygame.Rect(17, 449, 541, 411),
          'donkey': pygame.Rect(17, 300, 541, 411)}
MINIATURA = (156, 88)
MINIATURAS_POR_QUADRO = 2
CORES_PERIODO = {'dia': (72, 168, 224), 'tarde': (232, 128, 56), 'noite': (52, 52, 120)}
NOMES_PERIODO = {'dia': 'DIA', 'tarde': 'TARDE', 'noite': 'NOITE'}
LIMITE_PREVIAS = 6


def texto_que_cabe(conteudo, tamanho, largura, cor=Palette.WHITE, contorno=Palette.INK, espessura=2):
    """Texto que diminui até caber na largura (nomes longos: 'Boneco de Neve')."""
    while True:
        img = texto(conteudo, tamanho, cor, contorno, espessura)
        if img.get_width() <= largura or tamanho <= 14:
            return img
        tamanho -= 2


class Vitrine:
    def __init__(self, ctx):
        self.ctx = ctx
        self.vista = 'flappy'
        self._fundos = OrderedDict()
        self._visuais = {}
        self.passaro = Passaro(ctx.resources)

    def fundo(self, cenario_id, vista):
        chave = (cenario_id, vista)
        if chave in self._fundos:
            self._fundos.move_to_end(chave)
            return self._fundos[chave]
        tela = self._montar(cenario_id, vista)
        previa = pygame.transform.smoothscale(tela.subsurface(CORTES[vista]), TAMANHO_PREVIA)
        self._fundos[chave] = previa
        while len(self._fundos) > LIMITE_PREVIAS:
            self._fundos.popitem(last=False)
        return previa

    def _montar(self, cenario_id, vista):
        r = self.ctx.resources
        g = r.cenarios
        tela = pygame.Surface((LARGURA, ALTURA))
        if vista == 'galaga':
            tela.blit(g.variante(cenario_id, 'galaga'), (0, 0))
            for i, nome in enumerate(('Red', 'Blue', 'Green', 'Red', 'Blue')):
                inimigo = r.inimigos.get(nome) or next(iter(r.inimigos.values()))
                tela.blit(inimigo, inimigo.get_rect(center=(90 + i * 100, 500)))
        elif vista == 'donkey':
            CenarioNaFase(g, cenario_id).desenhar_donkey(tela, 0)
            tela.blit(r.palmeiras_longe, (0, 0))
            tela.blit(r.palmeiras_perto, (0, 0))
            for x in range(0, LARGURA, r.viga.get_width()):
                tela.blit(r.viga, (x, Y_CHAO))
            tela.blit(r.kong['parado'], r.kong['parado'].get_rect(bottomright=(LARGURA - 30, Y_CHAO)))
            tela.blit(r.barril, r.barril.get_rect(midbottom=(150, Y_CHAO)))
        else:
            tela.blit(g.fundo(cenario_id), (0, 0))
            cano = r.cano_noite if CENARIOS[cenario_id].periodo == NOITE else r.cano_dia
            tela.blit(cano, (430, 600))
            tela.blit(pygame.transform.flip(cano, False, True), (430, 420 - cano.get_height()))
            tela.blit(r.chao, (0, Y_CHAO))
        return tela

    def visual(self, skin_id):
        if skin_id not in self._visuais:
            self._visuais[skin_id] = SkinVisual(skin_id, self.ctx.resources)
        visual = self._visuais[skin_id]
        visual.efeitos = self.ctx.settings.visual_fx_enabled
        return visual

    def atualizar(self):
        p = self.passaro
        p.contador += 1
        if p.contador >= 10:
            p.contador = 0
            p.indice = (p.indice + 1) % 3

    def desenhar(self, surface, rect, cenario_id, skin_id, tempo):
        rect = pygame.Rect(rect)
        painel(surface, rect.inflate(10, 10), Palette.INK, raio=12, sombra=4, brilho=False)
        surface.blit(self.fundo(cenario_id, self.vista), rect)
        efeitos = self.ctx.settings.visual_fx_enabled
        sobe = math.sin(tempo * 3) * 8 if efeitos else 0
        p = self.passaro
        p.skin = self.visual(skin_id)
        largura, altura = p.sprite.get_size()
        centro = (rect.centerx - 30, rect.centery - 10)
        p.x, p.y = centro[0] - largura / 2, centro[1] - altura / 2 + sobe
        p.vy = -math.sin(tempo * 3) * 2.5 if efeitos else 0
        recorte = surface.get_clip()
        surface.set_clip(rect)
        p.desenhar(surface)
        surface.set_clip(recorte)


class FilaMiniaturas:
    """Miniaturas pedidas pelos cartões: devolve as prontas e monta as outras aos poucos."""

    def __init__(self, gerenciador):
        self.gerenciador = gerenciador
        self.pedidas = []

    def pegar(self, cenario_id):
        if self.gerenciador.tem_miniatura(cenario_id, MINIATURA):
            return self.gerenciador.miniatura(cenario_id, MINIATURA)
        if cenario_id not in self.pedidas:
            self.pedidas.append(cenario_id)
        return None

    def atualizar(self):
        for cenario_id in self.pedidas[:MINIATURAS_POR_QUADRO]:
            self.gerenciador.miniatura(cenario_id, MINIATURA)
        del self.pedidas[:MINIATURAS_POR_QUADRO]


def desenhar_cartao_cenario(surface, rect, cenario, miniatura, rodape, cor_rodape=Palette.WHITE,
                            marcado=None, ativo=True):
    """Cartão: miniatura com o período, nome e uma linha de estado (preço ou EM USO...).
    marcado: None (sem caixinha), True ou False (caixinha da playlist)."""
    painel(surface, rect, Palette.PANEL_LIGHT if ativo else Palette.PANEL, sombra=4)
    caixa = pygame.Rect(rect.x + 8, rect.y + 8, *MINIATURA)
    if miniatura is not None:
        surface.blit(miniatura, caixa)
    else:
        pygame.draw.rect(surface, Palette.SKY_DEEP, caixa)
    pygame.draw.rect(surface, Palette.INK, caixa, 2)
    periodo = texto(NOMES_PERIODO[cenario.periodo], 16, Palette.WHITE, None)
    selo = pygame.Rect(caixa.x + 4, caixa.y + 4, periodo.get_width() + 12, 20)
    pygame.draw.rect(surface, CORES_PERIODO[cenario.periodo], selo, border_radius=10)
    surface.blit(periodo, periodo.get_rect(center=selo.center))
    nome = texto_que_cabe(cenario.nome, 22, rect.w - 12, Palette.INK, None)
    surface.blit(nome, nome.get_rect(center=(rect.centerx, caixa.bottom + 16)))
    if marcado is not None:
        quadrado = pygame.Rect(caixa.right - 30, caixa.y + 4, 26, 26)
        pygame.draw.rect(surface, Palette.WHITE, quadrado, border_radius=6)
        pygame.draw.rect(surface, Palette.INK, quadrado, 3, border_radius=6)
        if marcado:
            pygame.draw.lines(surface, Palette.SUCCESS, False,
                              [(quadrado.x + 5, quadrado.centery), (quadrado.x + 11, quadrado.bottom - 6),
                               (quadrado.right - 5, quadrado.y + 6)], 4)
    y = rect.bottom - 20
    if isinstance(rodape, int):                     # preço
        preco = texto(str(rodape), 24, Palette.COIN, Palette.INK, 2)
        icone = icone_moeda(10)
        x = rect.centerx - (icone.get_width() + 4 + preco.get_width()) // 2
        surface.blit(icone, icone.get_rect(midleft=(x, y)))
        surface.blit(preco, preco.get_rect(midleft=(x + icone.get_width() + 4, y)))
    elif rodape:
        desenhar_texto(surface, rodape, 22, (rect.centerx, y), cor_rodape)
