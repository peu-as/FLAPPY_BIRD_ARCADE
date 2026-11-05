"""Tela de mapa: 25 casas num caminho, estilo Candy Crush / Super Mario World.

A casa 1 fica embaixo e o caminho sobe em zigue-zague. Casas concluídas
mostram as estrelas; a casa atual tem o pássaro em cima; as casas de chefão
(5, 10, 15, 20, 25) são maiores e coroadas. Navegação: roda do mouse,
arrastar, setas (casa anterior/próxima), ENTER joga, ESC volta.
"""
import math
import random

import pygame

from ..config.constants import ALTURA, LARGURA
from ..config.levels import CAPITULOS, CASAS, INTERVALO_CHEFE, MAPAS, cor_da_casa, etapa_arcade, tem_chefe
from ..core.paths import MUSICA_MENU
from ..core.scene import Scene
from ..gameplay.resources import ajustar_sprite
from ..ui.theme import Palette
from ..ui.widgets import Botao, aproximar, clarear, desenhar_texto, ease_out_back, escurecer, estrela, painel, texto

ESPACO_CASAS = 118
MARGEM_BAIXO, MARGEM_TOPO = 250, 230
ALTURA_MUNDO = MARGEM_BAIXO + (CASAS - 1) * ESPACO_CASAS + MARGEM_TOPO
AMPLITUDE, FREQUENCIA = 158, 0.85
RAIO_CASA, RAIO_CHEFE = 30, 38
ALTURA_TOPO, ALTURA_RODAPE = 78, 44
ARRASTE_MINIMO = 8                    # px: abaixo disso é clique, não arraste


def posicao_casa(casa):
    """Centro da casa no mundo (y cresce para baixo; a casa 1 fica embaixo)."""
    i = casa - 1
    return (LARGURA / 2 + AMPLITUDE * math.sin(i * FREQUENCIA),
            ALTURA_MUNDO - MARGEM_BAIXO - i * ESPACO_CASAS)


def _catmull_rom(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


class MapScene(Scene):
    fps = 60

    def __init__(self, ctx, mapa):
        super().__init__(ctx)
        self.mapa = mapa
        self.info = MAPAS[mapa]
        self.tempo = 0.0
        self.hover = {c: 0.0 for c in range(1, CASAS + 1)}
        self.pop = {}                     # casa -> tempo desde que foi liberada (animação)
        self.casa_mouse = None
        self.arraste = None               # (y_inicial_mouse, rolagem_inicial, arrastou?)
        self.casa_atual = ctx.progress.casa_atual(mapa)
        self.selecionada = self.casa_atual
        self.rolagem = self.rolagem_alvo = self._rolagem_para(self.selecionada)
        self.estrelas_fundo = [(random.uniform(0, LARGURA), random.uniform(0, ALTURA),
                                random.uniform(0.15, 0.6), random.choice((1, 2))) for _ in range(110)]
        self.voltar = Botao((14, 16, 56, 46), '<', self._sair, 'secundario', tamanho_texto=40)
        self.camada = pygame.Surface((LARGURA, ALTURA))      # para misturar cenários
        r = ctx.resources
        self.icones_estilo = {
            'flappy': ajustar_sprite(r.passaros['dia'][1], 24),
            'passaros': ajustar_sprite(r.especiais['Red'], 24),
            'donkey': ajustar_sprite(r.kong['parado'], 24),
            'galaga': ajustar_sprite(next(iter(r.inimigos.values())), 24),
        }
        self._montar_caminho()

    # ------------------------------------------------------------ estado
    def on_enter(self):
        self.ctx.audio.play_music(MUSICA_MENU, volume=0.5)
        nova = self.ctx.progress.casa_atual(self.mapa)
        if nova != self.casa_atual:            # voltou de uma vitória que liberou casa
            self.pop[nova] = 0.0
            self.casa_atual = self.selecionada = nova
            self.rolagem_alvo = self._rolagem_para(nova)
        self._montar_caminho()

    def _rolagem_para(self, casa):
        _, y = posicao_casa(casa)
        return self._limitar(y - ALTURA * 0.55)

    def _limitar(self, rolagem):
        return max(0.0, min(ALTURA_MUNDO - ALTURA, rolagem))

    def _montar_caminho(self):
        """Pré-desenha a trilha inteira (só muda quando o progresso muda)."""
        sup = pygame.Surface((LARGURA, ALTURA_MUNDO), pygame.SRCALPHA)
        pontos = [posicao_casa(c) for c in range(1, CASAS + 1)]
        estendidos = [pontos[0]] + pontos + [pontos[-1]]
        progresso = self.ctx.progress
        for i in range(CASAS - 1):
            feito = progresso.concluida(self.mapa, i + 1)
            cor = clarear(cor_da_casa(self.mapa, i + 1), 0.55) if feito else Palette.PANEL_LIGHT
            amostras = [_catmull_rom(*estendidos[i:i + 4], t / 24) for t in range(25)]
            for x, y in amostras:
                pygame.draw.circle(sup, Palette.INK, (round(x), round(y)), 15)
            for x, y in amostras:
                pygame.draw.circle(sup, cor, (round(x), round(y)), 11)
            for x, y in amostras[3:-3:4]:
                pygame.draw.circle(sup, escurecer(cor, 0.25), (round(x), round(y)), 3)
        if self.mapa == 'arcade':
            self._desenhar_placas(sup)
        self.caminho = sup

    def _desenhar_placas(self, sup):
        """Placa de cada capítulo da jornada, ao lado da primeira casa dele."""
        for numero, capitulo in enumerate(CAPITULOS, start=1):
            casa = (numero - 1) * INTERVALO_CHEFE + 1
            x, y = posicao_casa(casa)
            rotulo = texto(f'CAPÍTULO {numero}', 18, Palette.INK, None)
            nome = texto(capitulo.titulo, 26, Palette.WHITE, Palette.INK, 2)
            placa = pygame.Rect(0, 0, max(rotulo.get_width(), nome.get_width()) + 28, 62)
            placa.center = (x - 170 if x > LARGURA / 2 else x + 170, y + 18)
            placa.clamp_ip(pygame.Rect(8, 0, LARGURA - 16, ALTURA_MUNDO))
            pygame.draw.rect(sup, Palette.INK, (placa.centerx - 4, placa.bottom, 8, 26))   # poste
            painel(sup, placa, capitulo.cor, sombra=4)
            sup.blit(rotulo, rotulo.get_rect(center=(placa.centerx, placa.y + 17)))
            sup.blit(nome, nome.get_rect(center=(placa.centerx, placa.y + 41)))

    def _sair(self):
        self.manager.pop()

    def _jogar(self, casa):
        from .level_scene import LevelScene          # evita import circular
        if self.ctx.progress.liberada(self.mapa, casa):
            self.ctx.audio.play_sfx('ponto', 0.35)
            self.selecionada = casa
            self.manager.push(LevelScene(self.ctx, self.mapa, casa))
        else:
            self.ctx.audio.play_sfx('colisao', 0.25)

    def casa_em(self, pos_tela):
        x, y = pos_tela[0], pos_tela[1] + self.rolagem
        for casa in range(1, CASAS + 1):
            cx, cy = posicao_casa(casa)
            raio = RAIO_CHEFE if tem_chefe(casa) else RAIO_CASA
            if (x - cx) ** 2 + (y - cy) ** 2 <= (raio + 6) ** 2:
                return casa
        return None

    # ------------------------------------------------------------ entrada
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._sair()
            elif event.key in (pygame.K_UP, pygame.K_RIGHT):
                self._selecionar(self.selecionada + 1)
            elif event.key in (pygame.K_DOWN, pygame.K_LEFT):
                self._selecionar(self.selecionada - 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._jogar(self.selecionada)
            elif event.key == pygame.K_PAGEUP:
                self.rolagem_alvo = self._limitar(self.rolagem_alvo - ALTURA * 0.7)
            elif event.key == pygame.K_PAGEDOWN:
                self.rolagem_alvo = self._limitar(self.rolagem_alvo + ALTURA * 0.7)
            return
        if event.type == pygame.MOUSEWHEEL:
            self.rolagem_alvo = self._limitar(self.rolagem_alvo - event.y * 90)
            return
        if event.type == pygame.MOUSEMOTION:
            self.voltar.foco = self.voltar.contem(event.pos)
            if self.arraste:
                y0, r0, arrastou = self.arraste
                distancia = event.pos[1] - y0
                if arrastou or abs(distancia) > ARRASTE_MINIMO:
                    self.arraste = (y0, r0, True)
                    self.rolagem = self.rolagem_alvo = self._limitar(r0 - distancia)
            self.casa_mouse = self.casa_em(event.pos) if event.pos[1] > ALTURA_TOPO else None
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.voltar.contem(event.pos):
                self.voltar.apertado = True
            else:
                self.arraste = (event.pos[1], self.rolagem, False)
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.voltar.apertado:
                self.voltar.apertado = False
                if self.voltar.contem(event.pos):
                    self.voltar.ativar()
                return
            arrastou = self.arraste and self.arraste[2]
            self.arraste = None
            if not arrastou and event.pos[1] > ALTURA_TOPO:
                casa = self.casa_em(event.pos)
                if casa:
                    self._jogar(casa)

    def _selecionar(self, casa):
        if 1 <= casa <= CASAS and self.ctx.progress.liberada(self.mapa, casa):
            self.selecionada = casa
            self.rolagem_alvo = self._rolagem_para(casa)

    # ------------------------------------------------------------ quadro
    def update(self, dt):
        self.tempo += dt
        self.rolagem = aproximar(self.rolagem, self.rolagem_alvo, dt, 260)
        self.voltar.atualizar(dt)
        for casa in self.hover:
            alvo = 1.0 if casa in (self.casa_mouse, self.selecionada) and self.ctx.progress.liberada(self.mapa, casa) else 0.0
            self.hover[casa] = aproximar(self.hover[casa], alvo, dt)
        for casa in list(self.pop):
            self.pop[casa] += dt
            if self.pop[casa] > 1.2:
                del self.pop[casa]

    def draw(self, surface):
        efeitos = self.ctx.settings.visual_fx_enabled
        self._desenhar_fundo(surface, efeitos)
        surface.blit(self.caminho, (0, -round(self.rolagem)))
        topo, base = self.rolagem - 60, self.rolagem + ALTURA + 60
        for casa in range(1, CASAS + 1):
            if topo <= posicao_casa(casa)[1] <= base:
                self._desenhar_casa(surface, casa, efeitos)
        self._desenhar_barra_topo(surface)
        self._desenhar_rodape(surface)

    def _desenhar_fundo(self, surface, efeitos):
        if self.mapa != 'arcade':
            self._pintar(surface, {'flappy': 'dia', 'donkey': 'selva', 'galaga': 'espaco'}[self.mapa], efeitos)
            return
        # Jornada: o cenário acompanha o capítulo no meio da tela, com uma
        # transição suave perto da divisa entre dois capítulos.
        y_meio = self.rolagem + ALTURA / 2
        indice = (ALTURA_MUNDO - MARGEM_BAIXO - y_meio) / ESPACO_CASAS        # casa - 1, contínuo
        posicao = max(0.0, min(len(CAPITULOS) - 1.0, (indice + 0.5) / INTERVALO_CHEFE - 0.5))
        atual = int(posicao)
        mistura = max(0.0, min(1.0, (posicao - atual - 0.6) / 0.4))
        self._pintar(surface, CAPITULOS[atual].fundo, efeitos)
        if mistura > 0 and atual + 1 < len(CAPITULOS):
            self._pintar(self.camada, CAPITULOS[atual + 1].fundo, efeitos)
            self.camada.set_alpha(round(255 * mistura))
            surface.blit(self.camada, (0, 0))

    def _pintar(self, surface, cenario, efeitos):
        r = self.ctx.resources
        if cenario in ('dia', 'tarde', 'noite'):
            surface.blit(r.fundos[{'dia': 'bg', 'tarde': 'bg1', 'noite': 'night'}[cenario]], (0, 0))
        elif cenario == 'selva':
            surface.blit(r.fundo_selva, (0, 0))
            # palmeiras em tela cheia: deslizam de leve com a rolagem (paralaxe)
            sobra = ALTURA_MUNDO - ALTURA
            for camada, deslize in ((r.palmeiras_longe, 30), (r.palmeiras_perto, 70)):
                surface.blit(camada, (0, deslize * (self.rolagem / sobra - 1)))
        else:
            surface.fill((10, 10, 34))
            for x, y, fator, tamanho in self.estrelas_fundo:
                brilho = 160 + int(95 * math.sin(self.tempo * 2 + x)) if efeitos else 200
                yy = (y - self.rolagem * fator) % ALTURA
                pygame.draw.rect(surface, (brilho, brilho, min(255, brilho + 30)), (x, yy, tamanho, tamanho))

    def _desenhar_casa(self, surface, casa, efeitos):
        progresso = self.ctx.progress
        cx, cy = posicao_casa(casa)
        cy -= self.rolagem
        chefe = tem_chefe(casa)
        liberada = progresso.liberada(self.mapa, casa)
        feitas = progresso.estrelas(self.mapa, casa)
        cor_casa = cor_da_casa(self.mapa, casa)
        atual = casa == self.casa_atual and liberada and not feitas
        raio = (RAIO_CHEFE if chefe else RAIO_CASA) * (1 + 0.12 * self.hover[casa])
        if casa in self.pop:
            raio *= 0.6 + 0.4 * ease_out_back(self.pop[casa] / 0.6)
        if atual and efeitos:
            pulso = (math.sin(self.tempo * 4) + 1) / 2
            pygame.draw.circle(surface, clarear(Palette.BIRD_YELLOW, 0.4), (cx, cy), raio + 8 + 5 * pulso, 4)
        if not liberada:
            cor = Palette.LOCKED
        elif atual:
            cor = Palette.BIRD_YELLOW
        elif feitas:
            cor = cor_casa
        else:
            cor = Palette.PANEL_LIGHT
        pygame.draw.circle(surface, Palette.INK, (cx, cy + 5), raio + 3)               # sombra
        pygame.draw.circle(surface, Palette.DANGER if chefe and liberada else Palette.INK, (cx, cy), raio + 3)
        pygame.draw.circle(surface, cor, (cx, cy), raio - (3 if chefe else 0))
        pygame.draw.circle(surface, clarear(cor, 0.4), (cx - raio * 0.3, cy - raio * 0.35), raio * 0.28)
        if casa == self.selecionada and liberada:
            pygame.draw.circle(surface, Palette.WHITE, (cx, cy), raio + 6, 3)
        if liberada:
            desenhar_texto(surface, str(casa), 40 if chefe else 34, (cx, cy + 1), Palette.WHITE, espessura=2)
        else:
            self._desenhar_cadeado(surface, cx, cy)
        if chefe:
            self._desenhar_coroa(surface, cx, cy - raio - 10, liberada)
        if self.mapa == 'arcade':
            self._desenhar_selo_estilo(surface, cx + raio * 0.8, cy - raio * 0.62, casa)   # canto de cima: longe das estrelas
        if feitas:
            for i in range(3):
                estrela(surface, (cx + (i - 1) * 21, cy + raio + 13 - (5 if i == 1 else 0)), 11, i < feitas)
        if atual:
            quadro = self.ctx.resources.passaros['dia'][int(self.tempo * 9) % 3]
            sobe = math.sin(self.tempo * 3) * 6 if efeitos else 0
            surface.blit(quadro, quadro.get_rect(center=(cx, cy - raio - (66 if chefe else 30) + sobe)))  # acima da coroa

    def _desenhar_selo_estilo(self, surface, x, y, casa):
        """Selo com o ícone do estilo da casa (aparece até nas bloqueadas)."""
        pygame.draw.circle(surface, Palette.INK, (x, y), 17)
        pygame.draw.circle(surface, Palette.PANEL_LIGHT, (x, y), 14)
        icone = self.icones_estilo[etapa_arcade(casa).estilo]
        surface.blit(icone, icone.get_rect(center=(x, y)))

    def _desenhar_cadeado(self, surface, cx, cy):
        corpo = pygame.Rect(0, 0, 22, 17)
        corpo.center = (cx, cy + 5)
        pygame.draw.arc(surface, Palette.INK, (cx - 8, cy - 11, 16, 18), 0, math.pi, 4)
        pygame.draw.rect(surface, Palette.PANEL, corpo, border_radius=3)
        pygame.draw.rect(surface, Palette.INK, corpo, 2, border_radius=3)

    def _desenhar_coroa(self, surface, cx, base, liberada):
        cor = Palette.COIN if liberada else Palette.LOCKED
        pontos = [(cx - 16, base), (cx - 16, base - 14), (cx - 8, base - 6), (cx, base - 18),
                  (cx + 8, base - 6), (cx + 16, base - 14), (cx + 16, base)]
        pygame.draw.polygon(surface, cor, pontos)
        pygame.draw.polygon(surface, Palette.INK, pontos, 3)

    def _desenhar_barra_topo(self, surface):
        barra = pygame.Rect(-6, -10, LARGURA + 12, ALTURA_TOPO + 10)
        painel(surface, barra, Palette.PANEL, sombra=4)
        self.voltar.desenhar(surface)
        desenhar_texto(surface, self.info.titulo, 30, (LARGURA // 2 + 8, 30), self.info.cor, espessura=2)
        desenhar_texto(surface, f'CASA {self.selecionada} DE {CASAS}', 20, (LARGURA // 2 + 8, 56),
                       Palette.INK, contorno=None)
        total = f'{self.ctx.progress.total(self.mapa)}/{self.ctx.progress.maximo()}'
        rotulo = texto(total, 28, Palette.WHITE, Palette.INK, 2)
        rect = rotulo.get_rect(midright=(LARGURA - 14, 39))
        surface.blit(rotulo, rect)
        estrela(surface, (rect.x - 18, 38), 14, True)

    def _desenhar_rodape(self, surface):
        faixa = pygame.Surface((LARGURA, ALTURA_RODAPE), pygame.SRCALPHA)
        faixa.fill((*Palette.INK, 170))
        surface.blit(faixa, (0, ALTURA - ALTURA_RODAPE))
        dica = texto('RODA ou SETAS navegam   ENTER joga   ESC volta', 21, Palette.PANEL_LIGHT, None)
        surface.blit(dica, dica.get_rect(center=(LARGURA // 2, ALTURA - ALTURA_RODAPE // 2)))
