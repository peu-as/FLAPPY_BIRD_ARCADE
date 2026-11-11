"""Balão de dica dos modos novos: uma dica por vez, cada uma só na primeira vez.

A sessão pede (`pedir('c3_gelo')`); se a dica ainda não foi vista, entra na
fila. O balão aparece por alguns segundos e some antes se o jogador agir
depois de ter tido tempo de ler. Sem registro (testes, robôs), nada aparece.
"""
import pygame

from ..config.tutorial import DICAS
from ..config.constants import LARGURA
from ..ui.theme import Palette
from ..ui.widgets import painel, quebrar_linhas, texto

DURACAO = 7.0                  # s na tela
LEITURA_MINIMA = 2.5           # s antes de uma ação do jogador poder fechar o balão
ENTRADA = 0.25                 # s de animação
LARGURA_BALAO = 520
TAMANHO_TEXTO = 21


class GuiaDicas:
    def __init__(self, registro=None):
        self.registro = registro
        self.fila = []
        self.atual = None
        self.tempo = 0.0              # há quanto tempo a atual está na tela
        self._imagem = None

    def pedir(self, ident):
        if ident not in DICAS:
            raise KeyError(f'dica desconhecida: {ident}')
        if self.registro is None or self.registro.vista(ident) or ident == self.atual or ident in self.fila:
            return
        self.fila.append(ident)

    def acao(self):
        """O jogador agiu: fecha a dica se ela já teve tempo de ser lida."""
        if self.atual and self.tempo >= LEITURA_MINIMA:
            self.tempo = max(self.tempo, DURACAO - ENTRADA)

    def atualizar(self, dt):
        if self.atual:
            self.tempo += dt
            if self.tempo >= DURACAO:
                self.atual, self._imagem = None, None
        if self.atual is None and self.fila:
            self.atual, self.tempo = self.fila.pop(0), 0.0
            self.registro.marcar(self.atual)
            self._imagem = self._montar(DICAS[self.atual])

    @staticmethod
    def _montar(conteudo):
        linhas = quebrar_linhas(conteudo, TAMANHO_TEXTO, LARGURA_BALAO - 96)
        altura = 24 + 26 * len(linhas)
        balao = pygame.Surface((LARGURA_BALAO, altura + 8), pygame.SRCALPHA)
        painel(balao, pygame.Rect(0, 0, LARGURA_BALAO, altura), Palette.PANEL_LIGHT, sombra=4)
        selo = pygame.Rect(10, 0, 62, 26)
        selo.centery = altura // 2
        painel(balao, selo, Palette.BIRD_ORANGE, raio=10, sombra=0, brilho=False)
        rotulo = texto('DICA', 18, Palette.WHITE, Palette.INK, 2)
        balao.blit(rotulo, rotulo.get_rect(center=selo.center))
        for i, linha in enumerate(linhas):
            balao.blit(texto(linha, TAMANHO_TEXTO, Palette.INK, None), (84, 12 + 26 * i))
        return balao

    def desenhar(self, tela, centro_y):
        if self._imagem is None:
            return
        entra = min(1.0, self.tempo / ENTRADA)
        sai = min(1.0, (DURACAO - self.tempo) / ENTRADA)
        alfa = round(255 * max(0.0, min(entra, sai)))
        img = self._imagem.copy()
        img.set_alpha(alfa)
        deslize = round((1 - entra) * 20)
        tela.blit(img, img.get_rect(center=(LARGURA // 2, centro_y + deslize)))
