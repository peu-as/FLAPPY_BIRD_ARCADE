"""Equipamentos: como os cenários comprados aparecem nas fases.

FIXO: um cenário a partida inteira (clique no cartão para escolher).
ALEATÓRIO: a playlist (até 15) é sorteada a cada 20 s; clique liga e desliga.
Tudo fica salvo no save. A vitrine mostra o cenário em foco com a skin equipada.

Teclado: setas escolhem, ENTER usa/marca, F fixo, A aleatório, V troca a
vista, ESC volta.
"""
import pygame

from ..config.constants import ALTURA, LARGURA
from ..config.scenarios import CENARIOS, MAX_PLAYLIST, MODO_ALEATORIO, MODO_FIXO, POR_ID as POR_ID_CENARIO
from ..config.skins import POR_ID as POR_ID_SKIN
from ..core.paths import MUSICA_MENU
from ..core.scene import Scene
from ..systems.scenarios import PLAYLIST_CHEIA, ULTIMO_DA_PLAYLIST
from ..ui.theme import Palette
from ..ui.widgets import Botao, aproximar, desenhar_texto, painel, texto
from .vitrine import (NOMES_VISTA, TAMANHO_PREVIA, VISTAS, FilaMiniaturas, Vitrine, desenhar_cartao_cenario,
                      texto_que_cabe)

ALTURA_TOPO = 78
PAINEL = pygame.Rect(0, ALTURA_TOPO + 6, LARGURA, 300)
PREVIA = pygame.Rect(18, PAINEL.y + 14, *TAMANHO_PREVIA)
X_INFO = PREVIA.right + 22
LARGURA_INFO = LARGURA - X_INFO - 16
COLUNAS, CARTAO_L, CARTAO_A, ESPACO = 3, 172, 150, 12
X_GRADE = (LARGURA - (COLUNAS * CARTAO_L + (COLUNAS - 1) * ESPACO)) // 2
AREA_GRADE = pygame.Rect(0, PAINEL.bottom + 8, LARGURA, ALTURA - PAINEL.bottom - 8)
TEMPO_AVISO = 2.2


def retangulo_cartao(indice):
    linha, coluna = divmod(indice, COLUNAS)
    return pygame.Rect(X_GRADE + coluna * (CARTAO_L + ESPACO),
                       AREA_GRADE.y + 10 + linha * (CARTAO_A + ESPACO), CARTAO_L, CARTAO_A)


class EquipmentScene(Scene):
    fps = 60

    def __init__(self, ctx):
        super().__init__(ctx)
        self.cenarios = ctx.scenarios
        self.tempo = 0.0
        self.vitrine = Vitrine(ctx)
        self.miniaturas = FilaMiniaturas(ctx.resources.cenarios)
        self.rolagem = self.rolagem_alvo = 0.0
        self.aviso = ('', 0.0)
        self.hover = {}
        self.mouse_em = None
        self.voltar = Botao((14, 16, 56, 46), '<', self._sair, 'secundario', tamanho_texto=40)
        self.modos = {
            MODO_FIXO: Botao((X_INFO, PAINEL.y + 44, LARGURA_INFO, 44), 'FIXO',
                             lambda: self.definir_modo(MODO_FIXO), tamanho_texto=26),
            MODO_ALEATORIO: Botao((X_INFO, PAINEL.y + 96, LARGURA_INFO, 44), 'ALEATÓRIO',
                                  lambda: self.definir_modo(MODO_ALEATORIO), tamanho_texto=26),
        }
        self.botoes_vista = [Botao((PREVIA.x + i * 85, PREVIA.bottom + 8, 80, 30), NOMES_VISTA[v],
                                   lambda v=v: self.ver_em(v), tamanho_texto=18) for i, v in enumerate(VISTAS)]
        self.trocar_skin = Botao((X_INFO, PAINEL.y + 222, LARGURA_INFO, 30), 'TROCAR SKIN',
                                 lambda: self._abrir_loja('skins'), 'secundario', tamanho_texto=18)
        self.loja = Botao((X_INFO, PAINEL.y + 258, LARGURA_INFO, 30), 'LOJA DE CENÁRIOS',
                          lambda: self._abrir_loja('cenarios'), 'destaque', tamanho_texto=18)
        self._recarregar()

    # ------------------------------------------------------------ estado
    def _recarregar(self):
        comprados = set(self.cenarios.comprados)
        self.itens = [c for c in CENARIOS if c.id in comprados]
        foco = self.cenarios.fixo if self.cenarios.modo == MODO_FIXO else self.cenarios.playlist[0]
        self.indice = next((i for i, c in enumerate(self.itens) if c.id == foco), 0)
        self._estilos()
        self._garantir_visivel()

    def on_enter(self):
        self.ctx.audio.play_music(MUSICA_MENU, volume=0.5)
        self._recarregar()                 # pode ter comprado algo na loja

    @property
    def item(self):
        return self.itens[self.indice]

    def _estilos(self):
        for modo, botao in self.modos.items():
            botao.estilo = 'destaque' if modo == self.cenarios.modo else 'secundario'
        for v, botao in zip(VISTAS, self.botoes_vista):
            botao.estilo = 'primario' if v == self.vitrine.vista else 'secundario'

    def definir_modo(self, modo):
        if self.cenarios.modo != modo:
            self.cenarios.definir_modo(modo)
            self.ctx.audio.play_sfx('ponto', 0.4)
        self._estilos()

    def ver_em(self, vista):
        self.vitrine.vista = vista
        self._estilos()

    def escolher(self, indice=None):
        """Clique/ENTER no cartão: no fixo, passa a ser o fixo; no aleatório, liga/desliga."""
        if indice is not None:
            self._selecionar(indice)
        cenario = self.item
        audio = self.ctx.audio
        if self.cenarios.modo == MODO_FIXO:
            self.cenarios.usar_fixo(cenario.id)
            audio.play_sfx('ponto', 0.4)
            return
        resultado = self.cenarios.alternar_na_playlist(cenario.id)
        if resultado == PLAYLIST_CHEIA:
            self.aviso = (f'A playlist já tem {MAX_PLAYLIST} cenários', TEMPO_AVISO)
            audio.play_sfx('colisao', 0.25)
        elif resultado == ULTIMO_DA_PLAYLIST:
            self.aviso = ('A playlist precisa de pelo menos 1', TEMPO_AVISO)
            audio.play_sfx('colisao', 0.25)
        else:
            audio.play_sfx('ponto', 0.4)

    def _abrir_loja(self, aba):
        from .shop_scene import ShopScene
        self.ctx.audio.play_sfx('ponto', 0.35)
        self.manager.push(ShopScene(self.ctx, aba=aba))

    def _sair(self):
        self.manager.pop()

    def _rolagem_maxima(self):
        ultimo = retangulo_cartao(len(self.itens) - 1)
        return max(0, ultimo.bottom + 16 - AREA_GRADE.bottom)

    def _garantir_visivel(self):
        rect = retangulo_cartao(self.indice).move(0, -self.rolagem_alvo)
        if rect.top < AREA_GRADE.top + 6:
            self.rolagem_alvo -= AREA_GRADE.top + 6 - rect.top
        elif rect.bottom > AREA_GRADE.bottom - 6:
            self.rolagem_alvo += rect.bottom - (AREA_GRADE.bottom - 6)
        self.rolagem_alvo = max(0, min(self._rolagem_maxima(), self.rolagem_alvo))

    def _selecionar(self, indice):
        if 0 <= indice < len(self.itens):
            self.indice = indice
            self._garantir_visivel()

    # ------------------------------------------------------------ entrada
    def _botoes(self):
        return [self.voltar, *self.modos.values(), *self.botoes_vista, self.trocar_skin, self.loja]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            tecla = event.key
            if tecla == pygame.K_ESCAPE:
                self._sair()
            elif tecla == pygame.K_f:
                self.definir_modo(MODO_FIXO)
            elif tecla == pygame.K_a:
                self.definir_modo(MODO_ALEATORIO)
            elif tecla == pygame.K_v:
                self.ver_em(VISTAS[(VISTAS.index(self.vitrine.vista) + 1) % len(VISTAS)])
            elif tecla == pygame.K_LEFT:
                self._selecionar(self.indice - 1)
            elif tecla == pygame.K_RIGHT:
                self._selecionar(self.indice + 1)
            elif tecla == pygame.K_UP:
                self._selecionar(self.indice - COLUNAS)
            elif tecla == pygame.K_DOWN:
                self._selecionar(min(len(self.itens) - 1, self.indice + COLUNAS))
            elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.escolher()
            return
        if event.type == pygame.MOUSEWHEEL:
            self.rolagem_alvo = max(0, min(self._rolagem_maxima(), self.rolagem_alvo - event.y * 80))
            return
        if event.type == pygame.MOUSEMOTION:
            for botao in self._botoes():
                botao.foco = botao.contem(event.pos)
            self.mouse_em = self._cartao_em(event.pos)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for botao in self._botoes():
                if botao.contem(event.pos) and botao.habilitado:
                    botao.apertado = True
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for botao in self._botoes():
                if botao.apertado:
                    botao.apertado = False
                    if botao.contem(event.pos):
                        botao.ativar()
                        return
            indice = self._cartao_em(event.pos)
            if indice is not None:
                self.escolher(indice)

    def _cartao_em(self, pos):
        if not AREA_GRADE.collidepoint(pos):
            return None
        for i in range(len(self.itens)):
            if retangulo_cartao(i).move(0, -self.rolagem).collidepoint(pos):
                return i
        return None

    # ------------------------------------------------------------ quadro
    def update(self, dt):
        self.tempo += dt
        self.rolagem = aproximar(self.rolagem, self.rolagem_alvo, dt, 220)
        mensagem, restante = self.aviso
        self.aviso = (mensagem, max(0.0, restante - dt))
        self._estilos()
        for botao in self._botoes():
            botao.atualizar(dt)
        for i in range(len(self.itens)):
            alvo = 1.0 if i in (self.indice, self.mouse_em) else 0.0
            self.hover[i] = aproximar(self.hover.get(i, 0.0), alvo, dt)
        self.vitrine.atualizar()
        self.miniaturas.atualizar()

    def draw(self, surface):
        surface.blit(self.ctx.resources.fundos['bg'], (0, -60))
        self._desenhar_grade(surface)
        self._desenhar_painel(surface)
        painel(surface, pygame.Rect(-6, -10, LARGURA + 12, ALTURA_TOPO + 10), Palette.PANEL, sombra=4)
        self.voltar.desenhar(surface)
        desenhar_texto(surface, 'EQUIPAMENTOS', 38, (LARGURA // 2 + 20, 38), Palette.BIRD_YELLOW, espessura=3)

    def _desenhar_painel(self, surface):
        fundo = pygame.Surface(PAINEL.size, pygame.SRCALPHA)
        fundo.fill((*Palette.SKY, 235))
        surface.blit(fundo, PAINEL)
        skin = self.ctx.shop.equipada
        self.vitrine.desenhar(surface, PREVIA, self.item.id, skin, self.tempo)
        for botao in self.botoes_vista:
            botao.desenhar(surface)
        desenhar_texto(surface, 'CENÁRIOS NAS FASES', 20, topo_esquerdo=(X_INFO, PAINEL.y + 14), cor=Palette.WHITE)
        for botao in self.modos.values():
            botao.desenhar(surface)
        if self.cenarios.modo == MODO_FIXO:
            linha1 = texto_que_cabe(POR_ID_CENARIO[self.cenarios.fixo].nome, 22, LARGURA_INFO)
            linha2 = 'a partida inteira'
        else:
            linha1 = texto(f'PLAYLIST {len(self.cenarios.playlist)}/{MAX_PLAYLIST}', 22, Palette.WHITE)
            linha2 = 'troca a cada 20 s'
        surface.blit(linha1, (X_INFO, PAINEL.y + 150))
        desenhar_texto(surface, linha2, 18, topo_esquerdo=(X_INFO, PAINEL.y + 176), cor=Palette.WHITE, espessura=1)
        nome_skin = texto_que_cabe(f'SKIN: {POR_ID_SKIN[skin].nome}', 18, LARGURA_INFO)
        surface.blit(nome_skin, (X_INFO, PAINEL.y + 200))
        self.trocar_skin.desenhar(surface)
        self.loja.desenhar(surface)
        mensagem, restante = self.aviso
        if restante > 0:
            img = texto(mensagem, 22, Palette.WHITE, Palette.INK, 2)
            caixa = img.get_rect(center=(LARGURA // 2, PAINEL.bottom - 4)).inflate(24, 12)
            painel(surface, caixa, Palette.DANGER, raio=12, sombra=3, brilho=False)
            surface.blit(img, img.get_rect(center=caixa.center))

    def _desenhar_grade(self, surface):
        fundo = pygame.Surface(AREA_GRADE.size, pygame.SRCALPHA)
        fundo.fill((*Palette.INK, 150))
        surface.blit(fundo, AREA_GRADE)
        surface.set_clip(AREA_GRADE)
        aleatorio = self.cenarios.modo == MODO_ALEATORIO
        for i, cenario in enumerate(self.itens):
            rect = retangulo_cartao(i).move(0, -round(self.rolagem))
            if rect.bottom < AREA_GRADE.top or rect.top > AREA_GRADE.bottom:
                continue
            escala = 1 + 0.05 * self.hover.get(i, 0.0)
            rect = rect.inflate(rect.w * (escala - 1), rect.h * (escala - 1))
            if aleatorio:
                marcado = self.cenarios.na_playlist(cenario.id)
                rodape, cor = ('NA PLAYLIST', Palette.LOGO_GREEN) if marcado else ('FORA', Palette.WHITE)
            else:
                marcado = None
                em_uso = self.cenarios.fixo == cenario.id
                rodape, cor = ('EM USO', Palette.LOGO_GREEN) if em_uso else ('USAR', Palette.WHITE)
            desenhar_cartao_cenario(surface, rect, cenario, self.miniaturas.pegar(cenario.id), rodape, cor,
                                    marcado=marcado, ativo=True if marcado is None else marcado)
            if i == self.indice:
                pygame.draw.rect(surface, Palette.WHITE, rect.inflate(8, 8), 3, border_radius=12)
        surface.set_clip(None)
        if len(self.itens) <= 3:
            dica = texto('Compre mais cenários na LOJA para montar a playlist', 20, Palette.WHITE, Palette.INK, 2)
            surface.blit(dica, dica.get_rect(center=(LARGURA // 2, retangulo_cartao(3).centery)))
