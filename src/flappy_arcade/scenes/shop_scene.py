"""Loja: abas SKINS e CENÁRIOS, filtros, vitrine com prévia combinada e grade.

A vitrine mostra a skin voando sobre o cenário: na aba Skins, a skin escolhida
sobre o cenário em uso; na aba Cenários, o cenário escolhido com a skin
equipada. "Ver em" troca a prévia entre Flappy, Galaga e Donkey.

Comprar pede confirmação (segundo clique em até 3 s). Skin comprada já é
equipada; cenário comprado entra na playlist e, no modo fixo, passa a ser o fixo.

Mouse: clique escolhe; roda rola a grade. Teclado: setas escolhem, ENTER
compra/usa, TAB troca de aba, Q/E trocam o filtro, V troca a vista, ESC volta.
"""
import math
import random

import pygame

from ..config.constants import ALTURA, LARGURA
from ..config.scenarios import CENARIOS, MODO_FIXO, NOMES_GRUPO, NOVOS, ORIGINAIS
from ..config.skins import (CATEGORIAS, CORES_RARIDADE, LENDARIA, NOMES_CATEGORIA, NOMES_RARIDADE, POR_CATEGORIA,
                             POR_ID)
from ..core.paths import MUSICA_MENU
from ..core.scene import Scene
from ..gameplay.coins import icone_moeda
from ..systems.scenarios import PLAYLIST_CHEIA, ULTIMO_DA_PLAYLIST
from ..systems.shop import OK
from ..ui.theme import Palette
from ..ui.widgets import Botao, aproximar, desenhar_texto, painel, texto
from .vitrine import (CORES_PERIODO, NOMES_PERIODO, NOMES_VISTA, TAMANHO_PREVIA, VISTAS, FilaMiniaturas,
                      Vitrine, desenhar_cartao_cenario, texto_que_cabe)

SKINS_ABA, CENARIOS_ABA = 'skins', 'cenarios'
FILTROS = {SKINS_ABA: CATEGORIAS, CENARIOS_ABA: (ORIGINAIS, NOVOS)}
ALTURA_TOPO = 78
Y_ABAS, ALTURA_ABA = 86, 40
VITRINE = pygame.Rect(0, Y_ABAS + ALTURA_ABA + 6, LARGURA, 246)
PREVIA = pygame.Rect(18, VITRINE.y + 10, *TAMANHO_PREVIA)
X_INFO = PREVIA.right + 22
Y_FILTROS = VITRINE.bottom + 4
COLUNAS, CARTAO_L, CARTAO_A, ESPACO = 3, 172, 150, 12
X_GRADE = (LARGURA - (COLUNAS * CARTAO_L + (COLUNAS - 1) * ESPACO)) // 2
AREA_GRADE = pygame.Rect(0, Y_FILTROS + 42, LARGURA, ALTURA - Y_FILTROS - 42)
TEMPO_CONFIRMAR = 3.0
TEMPO_AVISO = 2.2


def retangulo_cartao(indice):
    linha, coluna = divmod(indice, COLUNAS)
    return pygame.Rect(X_GRADE + coluna * (CARTAO_L + ESPACO),
                       AREA_GRADE.y + 8 + linha * (CARTAO_A + ESPACO), CARTAO_L, CARTAO_A)


def _itens(aba, filtro):
    if aba == SKINS_ABA:
        return POR_CATEGORIA[filtro]
    return tuple(c for c in CENARIOS if c.grupo == filtro)


class ShopScene(Scene):
    fps = 60

    def __init__(self, ctx, aba=SKINS_ABA):
        super().__init__(ctx)
        self.loja = ctx.shop
        self.cenarios = ctx.scenarios
        self.tempo = 0.0
        self.vitrine = Vitrine(ctx)
        self.miniaturas = FilaMiniaturas(ctx.resources.cenarios)
        self.miniaturas_skin = {}
        equipada = POR_ID[self.loja.equipada]
        self.filtro = {SKINS_ABA: equipada.categoria, CENARIOS_ABA: ORIGINAIS}
        self.aba = SKINS_ABA
        self.indice = 0
        self.rolagem = self.rolagem_alvo = 0.0
        self.confirmando = None          # (aba, id, segundos restantes)
        self.aviso = ('', 0.0)
        self.confetes = []
        self.aleatorio = random.Random(7)
        self.hover = {}
        self.mouse_em = None
        self.voltar = Botao((14, 16, 56, 46), '<', self._sair, 'secundario', tamanho_texto=40)
        largura_aba = (LARGURA - 40) // 2
        self.abas = {
            SKINS_ABA: Botao((14, Y_ABAS, largura_aba, ALTURA_ABA), 'SKINS',
                             lambda: self.trocar_aba(SKINS_ABA), tamanho_texto=28),
            CENARIOS_ABA: Botao((26 + largura_aba, Y_ABAS, largura_aba, ALTURA_ABA), 'CENÁRIOS',
                                lambda: self.trocar_aba(CENARIOS_ABA), tamanho_texto=28),
        }
        self.botoes_vista = [Botao((PREVIA.x + i * 85, PREVIA.bottom + 8, 80, 30), NOMES_VISTA[v],
                                   lambda v=v: self.ver_em(v), tamanho_texto=18) for i, v in enumerate(VISTAS)]
        self.acao = Botao((X_INFO, VITRINE.y + 150, LARGURA - X_INFO - 16, 50), '', self._agir, tamanho_texto=26)
        self.equipamentos = Botao((X_INFO, VITRINE.y + 206, LARGURA - X_INFO - 16, 34), 'EQUIPAMENTOS',
                                  self._abrir_equipamentos, 'secundario', tamanho_texto=20)
        self.botoes_filtro = []
        if aba == CENARIOS_ABA:
            self.trocar_aba(CENARIOS_ABA)
        else:
            self._montar_filtros()
            self.indice = self.itens.index(equipada)
            self._garantir_visivel()

    def on_enter(self):
        self.ctx.audio.play_music(MUSICA_MENU, volume=0.5)

    # ------------------------------------------------------------ estado
    @property
    def itens(self):
        return _itens(self.aba, self.filtro[self.aba])

    @property
    def item(self):
        return self.itens[self.indice]

    @property
    def skin(self):
        """Skin mostrada na vitrine (a escolhida, ou a equipada na aba Cenários)."""
        return self.item if self.aba == SKINS_ABA else POR_ID[self.loja.equipada]

    @property
    def cenario_previa(self):
        if self.aba == CENARIOS_ABA:
            return self.item.id
        return self.cenarios.fixo if self.cenarios.modo == MODO_FIXO else self.cenarios.playlist[0]

    def possui(self, item):
        return (self.loja if self.aba == SKINS_ABA else self.cenarios).possui(item.id)

    def _montar_filtros(self):
        filtros = FILTROS[self.aba]
        largura = (LARGURA - 28 - 8 * (len(filtros) - 1)) // len(filtros)
        self.botoes_filtro = []
        for i, f in enumerate(filtros):
            nome = NOMES_CATEGORIA[f] if self.aba == SKINS_ABA else NOMES_GRUPO[f]
            quantidade = len(_itens(self.aba, f))
            self.botoes_filtro.append(Botao((14 + i * (largura + 8), Y_FILTROS, largura, 34),
                                            f'{nome} ({quantidade})', lambda f=f: self.trocar_filtro(f),
                                            tamanho_texto=20))
        self._estilos()

    def _estilos(self):
        for aba, botao in self.abas.items():
            botao.estilo = 'destaque' if aba == self.aba else 'secundario'
        for f, botao in zip(FILTROS[self.aba], self.botoes_filtro):
            botao.estilo = 'primario' if f == self.filtro[self.aba] else 'secundario'
        for v, botao in zip(VISTAS, self.botoes_vista):
            botao.estilo = 'primario' if v == self.vitrine.vista else 'secundario'

    def trocar_aba(self, aba):
        if aba == self.aba and self.botoes_filtro:
            return
        self.aba = aba
        self.confirmando = None
        self._montar_filtros()
        self.indice = 0
        if aba == CENARIOS_ABA:                       # começa no cenário em uso
            atual = self.cenario_em_uso()
            for f in FILTROS[aba]:
                ids = [c.id for c in _itens(aba, f)]
                if atual in ids:
                    self.filtro[aba] = f
                    self._estilos()
                    self.indice = ids.index(atual)
        self.rolagem = self.rolagem_alvo = 0.0
        self._garantir_visivel()

    def cenario_em_uso(self):
        return self.cenarios.fixo if self.cenarios.modo == MODO_FIXO else self.cenarios.playlist[0]

    def trocar_filtro(self, filtro):
        if filtro == self.filtro[self.aba]:
            return
        self.filtro[self.aba] = filtro
        self.indice = 0
        self.confirmando = None
        self.rolagem = self.rolagem_alvo = 0.0
        self._estilos()

    def passar_filtro(self, passo):
        filtros = FILTROS[self.aba]
        self.trocar_filtro(filtros[(filtros.index(self.filtro[self.aba]) + passo) % len(filtros)])

    def ver_em(self, vista):
        self.vitrine.vista = vista
        self._estilos()

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
        if 0 <= indice < len(self.itens) and indice != self.indice:
            self.indice = indice
            self.confirmando = None
            self._garantir_visivel()

    def _sair(self):
        self.manager.pop()

    def _abrir_equipamentos(self):
        from .equipment_scene import EquipmentScene
        self.ctx.audio.play_sfx('ponto', 0.35)
        self.manager.push(EquipmentScene(self.ctx))

    def _avisar(self, mensagem):
        self.aviso = (mensagem, TEMPO_AVISO)

    # ------------------------------------------------------------ ações
    def _agir(self):
        item, audio = self.item, self.ctx.audio
        if self.possui(item):
            self._usar(item)
            return
        if not self.ctx.wallet.pode_pagar(item.preco):
            audio.play_sfx('colisao', 0.25)
            return
        if not self.confirmando or self.confirmando[:2] != (self.aba, item.id):
            self.confirmando = (self.aba, item.id, TEMPO_CONFIRMAR)
            audio.play_sfx('pulo', 0.4)
            return
        if self.aba == SKINS_ABA:
            comprou = self.loja.comprar(item.id) == OK
            if comprou:
                self.loja.equipar(item.id)
        else:
            comprou = self.cenarios.comprar(item.id) == OK
            if comprou and self.cenarios.modo == MODO_FIXO:
                self.cenarios.usar_fixo(item.id)
        if comprou:
            self.confirmando = None
            audio.play_sfx('ponto', 0.6)
            self._comemorar()

    def _usar(self, item):
        audio = self.ctx.audio
        if self.aba == SKINS_ABA:
            if self.loja.equipada != item.id:
                self.loja.equipar(item.id)
                audio.play_sfx('ponto', 0.4)
            return
        if self.cenarios.modo == MODO_FIXO:
            if self.cenarios.fixo != item.id:
                self.cenarios.usar_fixo(item.id)
                audio.play_sfx('ponto', 0.4)
            return
        resultado = self.cenarios.alternar_na_playlist(item.id)
        if resultado == PLAYLIST_CHEIA:
            self._avisar('A playlist já tem 15 cenários')
            audio.play_sfx('colisao', 0.25)
        elif resultado == ULTIMO_DA_PLAYLIST:
            self._avisar('A playlist precisa de pelo menos 1')
            audio.play_sfx('colisao', 0.25)
        else:
            audio.play_sfx('ponto', 0.4)

    def _comemorar(self):
        if not self.ctx.settings.visual_fx_enabled:
            return
        destaque = CORES_RARIDADE[self.item.raridade] if self.aba == SKINS_ABA else CORES_PERIODO[self.item.periodo]
        cores = (Palette.COIN, Palette.LOGO_GREEN, Palette.WHITE, destaque)
        centro = PREVIA.center
        for _ in range(40):
            ang = self.aleatorio.uniform(0, 2 * math.pi)
            vel = self.aleatorio.uniform(120, 320)
            self.confetes.append([*centro, vel * math.cos(ang), vel * math.sin(ang) - 120, 0.0,
                                  self.aleatorio.choice(cores)])

    def _texto_acao(self):
        """(rótulo, estilo, habilitado) do botão da vitrine."""
        item = self.item
        if self.possui(item):
            if self.aba == SKINS_ABA:
                return ('EQUIPADA', 'secundario', False) if self.loja.equipada == item.id else ('EQUIPAR', 'primario', True)
            if self.cenarios.modo == MODO_FIXO:
                return ('EM USO', 'secundario', False) if self.cenarios.fixo == item.id else ('USAR', 'primario', True)
            if self.cenarios.na_playlist(item.id):
                return 'TIRAR DA PLAYLIST', 'secundario', True
            return 'PÔR NA PLAYLIST', 'primario', True
        faltam = item.preco - self.ctx.wallet.saldo
        if faltam > 0:
            return f'FALTAM {faltam}', 'primario', False
        if self.confirmando and self.confirmando[:2] == (self.aba, item.id):
            return 'CONFIRMAR?', 'perigo', True
        return f'COMPRAR {item.preco}', 'destaque', True

    # ------------------------------------------------------------ entrada
    def _botoes(self):
        botoes = [self.voltar, *self.abas.values(), *self.botoes_filtro, *self.botoes_vista, self.acao]
        if self.aba == CENARIOS_ABA:
            botoes.append(self.equipamentos)
        return botoes

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            tecla = event.key
            if tecla == pygame.K_ESCAPE:
                self._sair()
            elif tecla == pygame.K_TAB:
                self.trocar_aba(CENARIOS_ABA if self.aba == SKINS_ABA else SKINS_ABA)
            elif tecla in (pygame.K_q, pygame.K_PAGEUP):
                self.passar_filtro(-1)
            elif tecla in (pygame.K_e, pygame.K_PAGEDOWN):
                self.passar_filtro(1)
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
                if self.acao.habilitado:
                    self._agir()
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
                self._selecionar(indice)

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
        if self.confirmando:
            aba, ident, restante = self.confirmando
            self.confirmando = (aba, ident, restante - dt) if restante > dt else None
        mensagem, restante = self.aviso
        self.aviso = (mensagem, max(0.0, restante - dt))
        rotulo, estilo, habilitado = self._texto_acao()
        self.acao.rotulo, self.acao.estilo, self.acao.habilitado = rotulo, estilo, habilitado
        for botao in self._botoes():
            botao.atualizar(dt)
        for i in range(len(self.itens)):
            chave = (self.aba, i)
            alvo = 1.0 if i in (self.indice, self.mouse_em) else 0.0
            self.hover[chave] = aproximar(self.hover.get(chave, 0.0), alvo, dt)
        self.vitrine.atualizar()
        self.miniaturas.atualizar()
        vivos = []
        for c in self.confetes:
            c[0] += c[2] * dt
            c[1] += c[3] * dt
            c[3] += 520 * dt
            c[4] += dt
            if c[4] < 1.4:
                vivos.append(c)
        self.confetes = vivos

    def draw(self, surface):
        surface.blit(self.ctx.resources.fundos['bg'], (0, -60))
        self._desenhar_grade(surface)
        self._desenhar_vitrine(surface)
        for botao in self.botoes_filtro:
            botao.desenhar(surface)
        self._desenhar_topo(surface)

    def _desenhar_topo(self, surface):
        painel(surface, pygame.Rect(-6, -10, LARGURA + 12, ALTURA_TOPO + 10), Palette.PANEL, sombra=4)
        self.voltar.desenhar(surface)
        desenhar_texto(surface, 'LOJA', 40, (LARGURA // 2, 38), Palette.BIRD_YELLOW, espessura=3)
        saldo = texto(str(self.ctx.wallet.saldo), 30, Palette.WHITE, Palette.INK, 2)
        rect = saldo.get_rect(midright=(LARGURA - 16, 39))
        surface.blit(saldo, rect)
        icone = icone_moeda(14)
        surface.blit(icone, icone.get_rect(midright=(rect.x - 6, 39)))

    def _desenhar_vitrine(self, surface):
        fundo = pygame.Surface((LARGURA, VITRINE.bottom - Y_ABAS + 6), pygame.SRCALPHA)
        fundo.fill((*Palette.SKY, 235))
        surface.blit(fundo, (0, Y_ABAS - 6))
        for botao in self.abas.values():
            botao.desenhar(surface)
        self.vitrine.desenhar(surface, PREVIA, self.cenario_previa, self.skin.id, self.tempo)
        for botao in self.botoes_vista:
            botao.desenhar(surface)
        for x, y, _, _, _, cor in self.confetes:
            pygame.draw.rect(surface, cor, (x, y, 7, 7))
        item = self.item
        largura = LARGURA - X_INFO - 16
        nome = texto_que_cabe(item.nome.upper(), 32, largura)
        surface.blit(nome, (X_INFO, VITRINE.y + 12))
        if self.aba == SKINS_ABA:
            selo_texto, cor = NOMES_RARIDADE[item.raridade], CORES_RARIDADE[item.raridade]
        else:
            selo_texto, cor = NOMES_PERIODO[item.periodo], CORES_PERIODO[item.periodo]
        selo = texto(selo_texto, 20, Palette.WHITE, None)
        caixa = pygame.Rect(X_INFO, VITRINE.y + 54, selo.get_width() + 24, 28)
        painel(surface, caixa, cor, raio=14, sombra=3, brilho=False)
        surface.blit(selo, selo.get_rect(center=caixa.center))
        if self.possui(item):
            estado = 'NA SUA COLEÇÃO'
            if self.aba == CENARIOS_ABA and self.cenarios.modo != MODO_FIXO:
                estado = f'PLAYLIST {len(self.cenarios.playlist)}/15'
            desenhar_texto(surface, estado, 22, topo_esquerdo=(X_INFO, VITRINE.y + 100), cor=Palette.WHITE)
        else:
            icone = icone_moeda(14)
            surface.blit(icone, (X_INFO, VITRINE.y + 98))
            desenhar_texto(surface, str(item.preco), 34, topo_esquerdo=(X_INFO + 34, VITRINE.y + 94),
                           cor=Palette.COIN)
        self.acao.desenhar(surface)
        if self.aba == CENARIOS_ABA:
            self.equipamentos.desenhar(surface)
        mensagem, restante = self.aviso
        if restante > 0:
            img = texto(mensagem, 22, Palette.WHITE, Palette.INK, 2)
            caixa = img.get_rect(center=(LARGURA // 2, VITRINE.bottom - 14)).inflate(24, 12)
            painel(surface, caixa, Palette.DANGER, raio=12, sombra=3, brilho=False)
            surface.blit(img, img.get_rect(center=caixa.center))

    def _desenhar_grade(self, surface):
        fundo = pygame.Surface((LARGURA, ALTURA - Y_FILTROS + 6), pygame.SRCALPHA)
        fundo.fill((*Palette.INK, 150))
        surface.blit(fundo, (0, Y_FILTROS - 6))
        surface.set_clip(AREA_GRADE)
        for i, item in enumerate(self.itens):
            rect = retangulo_cartao(i).move(0, -round(self.rolagem))
            if rect.bottom < AREA_GRADE.top or rect.top > AREA_GRADE.bottom:
                continue
            escala = 1 + 0.05 * self.hover.get((self.aba, i), 0.0)
            rect = rect.inflate(rect.w * (escala - 1), rect.h * (escala - 1))
            if self.aba == SKINS_ABA:
                self._desenhar_cartao_skin(surface, item, rect)
            else:
                self._desenhar_cartao_cenario(surface, item, rect)
            if i == self.indice:
                pygame.draw.rect(surface, Palette.WHITE, rect.inflate(8, 8), 3, border_radius=12)
        surface.set_clip(None)

    def _miniatura_skin(self, skin_id):
        if skin_id not in self.miniaturas_skin:
            self.miniaturas_skin[skin_id] = self.vitrine.visual(skin_id).sprite_para(0)
        return self.miniaturas_skin[skin_id]

    def _desenhar_cartao_skin(self, surface, skin, rect):
        cor = CORES_RARIDADE[skin.raridade]
        possui = self.loja.possui(skin.id)
        painel(surface, rect, Palette.PANEL_LIGHT if possui else Palette.PANEL, sombra=4)
        if skin.raridade == LENDARIA:
            self._moldura_lendaria(surface, rect)
        faixa = pygame.Rect(rect.x + 3, rect.y + 3, rect.w - 6, 24)
        pygame.draw.rect(surface, cor, faixa, border_top_left_radius=8, border_top_right_radius=8)
        rotulo = texto(NOMES_RARIDADE[skin.raridade], 18, Palette.WHITE, None)
        surface.blit(rotulo, rotulo.get_rect(center=faixa.center))
        mini = self._miniatura_skin(skin.id)
        surface.blit(mini, mini.get_rect(center=(rect.centerx, rect.y + 64)))
        nome = texto_que_cabe(skin.nome, 22, rect.w - 12, Palette.INK, None)
        surface.blit(nome, nome.get_rect(center=(rect.centerx, rect.y + 106)))
        if self.loja.equipada == skin.id:
            desenhar_texto(surface, 'EQUIPADA', 22, (rect.centerx, rect.bottom - 20), Palette.LOGO_GREEN)
        elif possui:
            desenhar_texto(surface, 'COMPRADA', 22, (rect.centerx, rect.bottom - 20), Palette.WHITE)
        else:
            preco = texto(str(skin.preco), 24, Palette.COIN, Palette.INK, 2)
            icone = icone_moeda(10)
            x = rect.centerx - (icone.get_width() + 4 + preco.get_width()) // 2
            surface.blit(icone, icone.get_rect(midleft=(x, rect.bottom - 20)))
            surface.blit(preco, preco.get_rect(midleft=(x + icone.get_width() + 4, rect.bottom - 20)))

    def _moldura_lendaria(self, surface, rect):
        """Moldura dourada que pulsa (fixa com os efeitos visuais desligados)."""
        fase = (math.sin(self.tempo * 4) + 1) / 2 if self.ctx.settings.visual_fx_enabled else 1.0
        cor = tuple(round(a + (b - a) * fase) for a, b in zip(CORES_RARIDADE[LENDARIA], (255, 236, 140)))
        pygame.draw.rect(surface, cor, rect.inflate(4, 4), 3, border_radius=12)

    def _desenhar_cartao_cenario(self, surface, cenario, rect):
        possui = self.cenarios.possui(cenario.id)
        aleatorio = self.cenarios.modo != MODO_FIXO
        if not possui:
            rodape, cor = cenario.preco, Palette.COIN
        elif not aleatorio and self.cenarios.fixo == cenario.id:
            rodape, cor = 'EM USO', Palette.LOGO_GREEN
        elif aleatorio and self.cenarios.na_playlist(cenario.id):
            rodape, cor = 'NA PLAYLIST', Palette.LOGO_GREEN
        else:
            rodape, cor = 'COMPRADO', Palette.WHITE
        desenhar_cartao_cenario(surface, rect, cenario, self.miniaturas.pegar(cenario.id), rodape, cor,
                                ativo=possui)

