"""Uma casa do mapa: cartão de abertura -> jogo -> resultado com estrelas.

O jogo em si é a sessão da casa (gameplay/level_session.py), com a física
do original; esta cena só cuida da moldura: abertura, gravação do progresso
e os botões do resultado (mapa, de novo, próxima).
"""
import pygame

from ..config.constants import ALTURA, FPS, LARGURA
from ..config.economy import BONUS_POR_ESTRELA_NOVA
from ..config.levels import CAPITULOS, CASAS, MAPAS, NOMES_ESTILOS, cor_da_casa, etapa_arcade
from ..core.scene import Scene
from ..gameplay.coins import icone_moeda
from ..gameplay.level_session import criar_sessao
from ..ui.theme import Palette
from .game_scene import preparar_recompensas
from ..ui.widgets import Botao, GrupoBotoes, desenhar_texto, ease_out_back, estrela, painel, texto

ABERTURA, JOGANDO, RESULTADO = 'ABERTURA', 'JOGANDO', 'RESULTADO'
INTERVALO_ESTRELAS = 0.35          # s entre uma estrela e outra no resultado


def _quebrar(conteudo, tamanho, largura):
    """Quebra um texto em linhas que cabem na largura."""
    linhas, atual = [], ''
    for palavra in conteudo.split():
        teste = f'{atual} {palavra}'.strip()
        if texto(teste, tamanho, contorno=None).get_width() <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    return linhas + [atual] if atual else linhas


class LevelScene(Scene):
    fps = FPS        # a física é por quadro, calibrada a 30 FPS

    def __init__(self, ctx, mapa, casa):
        super().__init__(ctx)
        self.mapa, self.casa = mapa, casa
        self.info = MAPAS[mapa]
        self.cor = cor_da_casa(mapa, casa)
        self.session = criar_sessao(mapa, casa, ctx.resources, ctx.audio, ctx.clock)
        preparar_recompensas(self.session, ctx)
        self.depositadas = 0          # moedas (com bônus) já levadas à carteira
        self.bonus = 0
        # O banner de início da sessão (ex.: "FASE DOS PÁSSAROS!") espera o jogo
        # começar, em vez de ficar congelado atrás do cartão de abertura.
        self.banner_guardado, self.session.banner_tempo = self.session.banner_tempo, 0.0
        self.fase = ABERTURA
        self.tempo_fase = 0.0
        self.melhor_antes = ctx.progress.estrelas(mapa, casa)
        self.melhorou, self.liberou = False, None
        self.estrelas_tocadas = 0
        self.grupo = None
        self.escurecer = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self.escurecer.fill(Palette.DIM)

    # ------------------------------------------------------------ transições
    def _comecar(self):
        self.fase, self.tempo_fase = JOGANDO, 0.0
        self.session.banner_tempo = self.banner_guardado

    def _terminar(self):
        s = self.session
        if s.resultado == 'VITORIA':
            self.melhorou, self.liberou = self.ctx.progress.registrar(self.mapa, self.casa, s.estrelas)
            self.bonus = BONUS_POR_ESTRELA_NOVA * max(0, s.estrelas - self.melhor_antes)
        self._depositar()
        self.fase, self.tempo_fase = RESULTADO, 0.0
        botoes = self._botoes_resultado()
        self.grupo = GrupoBotoes(botoes, colunas=3)
        self.grupo.focar(botoes[-1])           # ENTER = botão principal (o último)

    def _botoes_resultado(self):
        venceu = self.session.resultado == 'VITORIA'
        tem_proxima = venceu and self.casa < CASAS
        largura, y = 150, ALTURA // 2 + 166
        botoes = [
            Botao((0, 0, largura, 58), 'MAPA', self._mapa, 'secundario', tamanho_texto=30),
            Botao((0, 0, largura, 58), 'DE NOVO', self._de_novo,
                  'secundario' if tem_proxima else 'primario', tamanho_texto=30),
        ]
        if tem_proxima:
            botoes.append(Botao((0, 0, largura, 58), 'PRÓXIMA', self._proxima, 'primario', tamanho_texto=30))
        total = len(botoes) * largura + (len(botoes) - 1) * 14
        for i, b in enumerate(botoes):
            b.rect.topleft = (LARGURA // 2 - total // 2 + i * (largura + 14), y)
        return botoes

    def _depositar(self):
        """Leva à carteira só o que ainda não foi depositado (pode rodar várias vezes)."""
        novas = self.session.moedas_coletadas + self.bonus - self.depositadas
        self.depositadas += novas
        self.ctx.wallet.depositar(novas)

    def on_exit(self):
        self._depositar()           # saiu no meio: guarda o que já coletou

    def _mapa(self):
        self.manager.pop()

    def _de_novo(self):
        self.manager.replace(LevelScene(self.ctx, self.mapa, self.casa))

    def _proxima(self):
        self.manager.replace(LevelScene(self.ctx, self.mapa, self.casa + 1))

    # ------------------------------------------------------------ entrada
    def handle_event(self, event):
        tecla = event.key if event.type == pygame.KEYDOWN else None
        if self.fase == ABERTURA:
            if tecla == pygame.K_ESCAPE:
                self._mapa()
            elif tecla in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER) or (
                    event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self._comecar()
        elif self.fase == JOGANDO:
            if not self.session.tratar_evento(event):      # ESC
                self._mapa()
        else:
            if tecla == pygame.K_ESCAPE:
                self._mapa()
            elif tecla == pygame.K_r:
                self._de_novo()
            else:
                self.grupo.tratar_evento(event)

    # ------------------------------------------------------------ quadro
    def update(self, dt):
        self.tempo_fase += dt
        if self.fase == JOGANDO:
            self.session.atualizar(dt, self.ctx.clock.ticks())
            if self.session.resultado:
                self._terminar()
        elif self.fase == RESULTADO:
            self.grupo.atualizar(dt)
            devidas = min(self.session.estrelas, int(self.tempo_fase / INTERVALO_ESTRELAS))
            while self.estrelas_tocadas < devidas:
                self.estrelas_tocadas += 1
                self.ctx.audio.play_sfx('ponto', 0.4)

    def draw(self, surface):
        self.session.desenhar()
        surface.blit(self.session.tela, (0, 0))
        if self.fase == ABERTURA:
            surface.blit(self.escurecer, (0, 0))
            self._desenhar_abertura(surface)
        elif self.fase == RESULTADO:
            surface.blit(self.escurecer, (0, 0))
            self._desenhar_resultado(surface)

    def _cabecalho(self, surface, cartao):
        faixa = pygame.Rect(cartao.x, cartao.y, cartao.w, 64)
        painel(surface, faixa, self.cor, sombra=0)
        desenhar_texto(surface, f'CASA {self.casa}', 46, (cartao.centerx, faixa.centery + 1), espessura=3)
        if self.session.chefe:
            selo = pygame.Rect(0, 0, 112, 34)
            selo.midright = (cartao.right + 10, cartao.y - 4)
            painel(surface, selo, Palette.DANGER, sombra=3)
            desenhar_texto(surface, 'CHEFÃO!', 24, selo.center, espessura=2)

    def subtitulo(self):
        """Linha abaixo de "CASA N": o mapa, ou o capítulo e o estilo na jornada."""
        if self.mapa != 'arcade':
            return self.info.titulo
        etapa = etapa_arcade(self.casa)
        capitulo = CAPITULOS[etapa.capitulo - 1].titulo
        return f'CAPÍTULO {etapa.capitulo}: {capitulo}  -  {NOMES_ESTILOS[etapa.estilo].upper()}'

    def _desenhar_abertura(self, surface):
        cartao = pygame.Rect(0, 0, 470, 330)
        cartao.center = (LARGURA // 2, ALTURA // 2 - 20)
        painel(surface, cartao, Palette.PANEL)
        self._cabecalho(surface, cartao)
        desenhar_texto(surface, self.subtitulo(), 24, (cartao.centerx, cartao.y + 86), Palette.INK, contorno=None)
        y = cartao.y + 124
        for linha in _quebrar(self.session.objetivo, 32, cartao.w - 50):
            desenhar_texto(surface, linha, 32, (cartao.centerx, y), Palette.WHITE, espessura=2)
            y += 34
        desenhar_texto(surface, 'MELHOR RESULTADO', 20, (cartao.centerx, cartao.y + 212), Palette.INK, contorno=None)
        for i in range(3):
            estrela(surface, (cartao.centerx + (i - 1) * 46, cartao.y + 248), 19, i < self.melhor_antes)
        piscar = int(self.tempo_fase * 2) % 2 == 0 or not self.ctx.settings.visual_fx_enabled
        if piscar:
            desenhar_texto(surface, 'ESPAÇO ou clique para começar', 26, (cartao.centerx, cartao.bottom + 40),
                           Palette.WHITE, espessura=2)
        desenhar_texto(surface, 'ESC volta ao mapa', 20, (cartao.centerx, cartao.bottom + 72),
                       Palette.PANEL_LIGHT, contorno=Palette.INK, espessura=1)

    def _desenhar_resultado(self, surface):
        venceu = self.session.resultado == 'VITORIA'
        cartao = pygame.Rect(0, 0, 490, 320)
        cartao.center = (LARGURA // 2, ALTURA // 2 - 22)
        painel(surface, cartao, Palette.PANEL)
        self._cabecalho(surface, cartao)
        titulo, cor = ('VITÓRIA!', Palette.LOGO_GREEN) if venceu else ('NÃO FOI DESSA VEZ', Palette.DANGER)
        desenhar_texto(surface, titulo, 48 if venceu else 40, (cartao.centerx, cartao.y + 104), cor, espessura=3)
        efeitos = self.ctx.settings.visual_fx_enabled
        for i in range(3):
            cheia = i < self.session.estrelas
            inicio = (i + 1) * INTERVALO_ESTRELAS
            escala = ease_out_back((self.tempo_fase - inicio) / 0.35) if (cheia and efeitos) else 1.0
            raio = 30 if i == 1 else 25
            centro = (cartao.centerx + (i - 1) * 74, cartao.y + 172 - (10 if i == 1 else 0))
            estrela(surface, centro, raio, False)
            if cheia and (self.tempo_fase >= inicio or not efeitos):
                estrela(surface, centro, max(1, raio * escala), True)
        if venceu:
            nota = ('NOVO RECORDE NESTA CASA!' if self.melhorou and self.melhor_antes
                    else f'CASA {self.liberou} LIBERADA!' if self.liberou else
                    'MAPA COMPLETO!' if self.casa == CASAS else 'CASA CONCLUÍDA')
        else:
            nota = 'Tente de novo: R ou o botão abaixo'
        self._desenhar_moedas(surface, cartao.centerx, cartao.y + 226)
        desenhar_texto(surface, nota, 24, (cartao.centerx, cartao.bottom - 30), Palette.INK, contorno=None)
        self.grupo.desenhar(surface)

    def _desenhar_moedas(self, surface, cx, y):
        """Linha "+N  (bônus +B)" com o ícone de moeda."""
        partes = [texto(f'+{self.session.moedas_coletadas}', 30, Palette.COIN, Palette.INK, 2)]
        if self.bonus:
            partes.append(texto(f'  bônus +{self.bonus}', 24, Palette.WHITE, Palette.INK, 2))
        icone = icone_moeda(12)
        largura = icone.get_width() + 6 + sum(p.get_width() for p in partes)
        x = cx - largura // 2
        surface.blit(icone, icone.get_rect(midleft=(x, y)))
        x += icone.get_width() + 6
        for parte in partes:
            surface.blit(parte, parte.get_rect(midleft=(x, y)))
            x += parte.get_width()
