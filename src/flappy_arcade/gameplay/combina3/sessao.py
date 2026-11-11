"""Sessão do Combina 3: uma casa do mapa, da primeira troca ao resultado.

Cumpre o mesmo contrato das outras sessões de casa (veja scenes/level_scene.py).

Uma jogada anda em etapas, para a tela animar cada uma:
    PRONTO -> TROCA (as duas peças trocam de lugar) -> ESTOURO (o que combinou some)
           -> QUEDA (as peças caem e entram novas) -> ESTOURO de novo se houver cascata
           -> ... -> PRONTO (ou EMBARALHA se não sobrou jogada possível)

Controles
  Mouse: clique numa peça e depois na vizinha, ou arraste a peça na direção da troca.
  Teclado: setas movem o cursor; ESPAÇO segura a peça; com a peça segura, a seta troca.
"""
import pygame

from ...config import combina3 as cfg
from ...config.constants import ALTURA, LARGURA
from ...ui.theme import Palette
from ...ui.widgets import desenhar_texto, painel, texto
from ..coins import icone_moeda
from .tabuleiro import Tabuleiro
from .visual import AREA, VisualCombina3, casa_em

PRONTO, TROCA, ESTOURO, QUEDA, EMBARALHA = 'PRONTO', 'TROCA', 'ESTOURO', 'QUEDA', 'EMBARALHA'
DT = 1 / 30
TEMPO_TROCA, TEMPO_ESTOURO, TEMPO_MINIMO_QUEDA, TEMPO_EMBARALHA = 0.18, 0.22, 0.12, 0.7
SEGUNDOS_PARA_DICA = 5.0
ARRASTE_MINIMO = 24
SETAS = {pygame.K_LEFT: (0, -1), pygame.K_RIGHT: (0, 1), pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0)}


class Combina3Session:
    estado = 'JOGO'                # para a pausa: a partida está em andamento
    pausado = False
    TEXTO_ATALHOS = 'P ou ESC: Pausa'

    def __init__(self, recursos, audio, clock, casa, semente=None):
        self.recursos, self.audio, self.clock = recursos, audio, clock
        self.casa = casa
        self.definicao = cfg.casa_combina3(casa)
        self.tab = Tabuleiro(cfg.LINHAS, cfg.COLUNAS, semente=semente)
        self.visual = VisualCombina3(recursos)
        self.visual.sincronizar(self.tab)
        self.tela = pygame.Surface((LARGURA, ALTURA))
        self.jogadas = self.definicao.jogadas
        self.usadas = 0
        self.etapa = PRONTO
        self.tempo_etapa = 0.0
        self.tempo = 0.0
        self.ocioso = 0.0
        self.onda = None
        self.selecao = None
        self.cursor = None                     # só aparece quando o teclado é usado
        self.arrasto = None                    # (casa, posição do clique)
        self.dica = None
        self.aviso = ('', 0.0)
        self.moedas_coletadas = 0
        self.resultado = None
        self.estrelas = 0
        self.banner_tempo = 0.0
        self.skin = None
        self.efeitos_bonus = True

    # ------------------------------------------------------------ contrato da casa
    @property
    def chefe(self):
        return self.definicao.chefe

    @property
    def pontos(self):
        return self.tab.pontos

    @property
    def objetivo(self):
        tres, _ = cfg.jogadas_para_estrelas(self.definicao.jogadas)
        meta = f'{self.definicao.meta:,}'.replace(',', '.')
        return f'Faça {meta} pontos em {self.definicao.jogadas} jogadas. 3 estrelas: sobrando {tres}.'

    def preparar_recompensas(self, skin=None, saldo=0, efeitos=True, moedas=True):
        self.skin = skin
        self.visual.efeitos = efeitos

    def preparar_cenarios(self, diretor, efeitos=True):
        self.visual.preparar_fundo(diretor.gerenciador.fundo(diretor.atual))

    # ------------------------------------------------------------ jogada
    def tentar(self, a, b):
        """Tenta trocar as peças das casas a e b. True se a troca combinou."""
        if self.etapa != PRONTO or self.resultado or self.jogadas <= 0:
            return False
        pa, pb = self.tab.peca(a), self.tab.peca(b)
        if pa is None or pb is None or not self.tab.adjacentes(a, b):
            return False
        self.selecao = self.dica = None
        self.ocioso = 0.0
        onda = self.tab.trocar(a, b)
        if onda is None:
            self.visual.tremer(pa, pb, a, b)
            self.audio.play_sfx('colisao', 0.2)
            return False
        self.onda = onda
        self.jogadas -= 1
        self.usadas += 1
        self.visual.sincronizar(self.tab)
        self._mudar(TROCA)
        self.audio.play_sfx('pulo', 0.35)
        return True

    def acao_principal(self):
        """Faz a jogada da dica (usado pela verificação automática e pelos testes)."""
        jogada = self.tab.dica() if self.etapa == PRONTO else None
        return bool(jogada) and self.tentar(*jogada)

    def _mudar(self, etapa):
        self.etapa, self.tempo_etapa = etapa, 0.0

    def _estourar(self):
        onda = self.onda
        self.visual.ao_aplicar(onda)
        for casa in onda.criadas:
            self.moedas_coletadas += cfg.MOEDAS_POR_ESPECIAL
            self.visual.moedas(casa, cfg.MOEDAS_POR_ESPECIAL)
        self.tab.aplicar(onda)
        self.visual.sincronizar(self.tab)
        self.audio.play_sfx('ponto', min(0.7, 0.3 + 0.1 * onda.multiplicador))
        self._mudar(ESTOURO)

    def _fim_da_jogada(self):
        self.onda = None
        if self.tab.pontos >= self.definicao.meta:
            sobrando = self.jogadas
            self.moedas_coletadas += cfg.MOEDAS_POR_VITORIA + sobrando // cfg.JOGADAS_POR_MOEDA
            self.estrelas = cfg.estrelas_combina3(self.definicao.jogadas, self.usadas)
            self.resultado = 'VITORIA'
        elif self.jogadas <= 0:
            self.resultado = 'DERROTA'
            self.audio.play_sfx('morte', 0.5)
        elif self.tab.dica() is None:
            self.tab.embaralhar()
            self.visual.sincronizar(self.tab)
            self.aviso = ('SEM JOGADAS: EMBARALHANDO!', 1.6)
            self._mudar(EMBARALHA)
        else:
            self._mudar(PRONTO)

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if self.resultado:
            return True
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            casa = casa_em(evento.pos)
            self.cursor = None
            if casa is None or self.tab.peca(casa) is None:
                self.selecao = None
            elif self.selecao is not None and self.tab.adjacentes(self.selecao, casa):
                self.tentar(self.selecao, casa)
            else:
                self.selecao, self.arrasto = casa, (casa, evento.pos)
        elif evento.type == pygame.MOUSEMOTION and self.arrasto:
            casa, origem = self.arrasto
            dx, dy = evento.pos[0] - origem[0], evento.pos[1] - origem[1]
            if max(abs(dx), abs(dy)) >= ARRASTE_MINIMO:
                passo = (0, 1 if dx > 0 else -1) if abs(dx) > abs(dy) else (1 if dy > 0 else -1, 0)
                self.arrasto = None
                self.tentar(casa, (casa[0] + passo[0], casa[1] + passo[1]))
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self.arrasto = None
        elif evento.type == pygame.KEYDOWN:
            self._tecla(evento.key)
        return True

    def _tecla(self, tecla):
        if tecla in SETAS:
            dl, dc = SETAS[tecla]
            if self.selecao is not None:
                destino = (self.selecao[0] + dl, self.selecao[1] + dc)
                origem, self.cursor = self.selecao, destino if self.tab.dentro(*destino) else self.selecao
                self.tentar(origem, destino)
                self.selecao = None
            else:
                l, c = self.cursor or (cfg.LINHAS // 2, cfg.COLUNAS // 2)
                self.cursor = (max(0, min(cfg.LINHAS - 1, l + dl)), max(0, min(cfg.COLUNAS - 1, c + dc)))
        elif tecla in (pygame.K_SPACE, pygame.K_RETURN):
            if self.selecao is not None:
                self.selecao = None
            elif self.cursor is not None and self.tab.peca(self.cursor) is not None:
                self.selecao = self.cursor

    # ------------------------------------------------------------ quadro
    def atualizar(self, dt=DT, agora_ms=0):
        if self.resultado:
            return
        self.tempo += DT
        self.tempo_etapa += DT
        mensagem, restante = self.aviso
        self.aviso = (mensagem, max(0.0, restante - DT))
        self.visual.atualizar(DT)
        if self.etapa == PRONTO:
            self.ocioso += DT
            if self.ocioso >= SEGUNDOS_PARA_DICA and self.dica is None:
                self.dica = self.tab.dica()
        elif self.etapa == TROCA and self.tempo_etapa >= TEMPO_TROCA:
            self._estourar()
        elif self.etapa == ESTOURO and self.tempo_etapa >= TEMPO_ESTOURO:
            self.visual.sincronizar(self.tab, self.tab.cair())
            self._mudar(QUEDA)
        elif self.etapa == QUEDA and self.tempo_etapa >= TEMPO_MINIMO_QUEDA and self.visual.parado():
            self.onda = self.tab.proxima_onda()
            if self.onda:
                self._estourar()
            else:
                self._fim_da_jogada()
        elif self.etapa == EMBARALHA and self.tempo_etapa >= TEMPO_EMBARALHA and self.visual.parado():
            self._mudar(PRONTO)

    # ------------------------------------------------------------ desenho
    def desenhar(self):
        tela = self.tela
        self.visual.desenhar(tela, self.tab, self.tempo, self.selecao, self.cursor, self.dica)
        self._hud(tela)

    def _hud(self, tela):
        meta = self.definicao.meta
        caixa = pygame.Rect(14, 12, 350, 150)
        painel(tela, caixa, Palette.PANEL, sombra=4)
        desenhar_texto(tela, 'PONTOS', 20, topo_esquerdo=(caixa.x + 16, caixa.y + 10), cor=Palette.INK, contorno=None)
        desenhar_texto(tela, f'{self.tab.pontos:,}'.replace(',', '.'), 44, topo_esquerdo=(caixa.x + 16, caixa.y + 30),
                       cor=Palette.WHITE, espessura=3)
        barra = pygame.Rect(caixa.x + 16, caixa.y + 84, caixa.w - 32, 20)
        pygame.draw.rect(tela, Palette.INK, barra.inflate(6, 6), border_radius=10)
        pygame.draw.rect(tela, (90, 70, 80), barra, border_radius=8)
        cheia = barra.copy()
        cheia.w = round(barra.w * min(1.0, self.tab.pontos / meta))
        if cheia.w > 4:
            pygame.draw.rect(tela, Palette.LOGO_GREEN, cheia, border_radius=8)
        rotulo = texto(f'META {meta:,}'.replace(',', '.'), 20, Palette.INK, None)
        tela.blit(rotulo, (barra.x, barra.bottom + 8))
        icone = icone_moeda(10)
        tela.blit(icone, icone.get_rect(midright=(caixa.right - 62, barra.bottom + 18)))
        desenhar_texto(tela, f'+{self.moedas_coletadas}', 22, topo_esquerdo=(caixa.right - 56, barra.bottom + 6),
                       cor=Palette.COIN)
        lado = pygame.Rect(376, 12, LARGURA - 390, 150)
        painel(tela, lado, Palette.PANEL_LIGHT if self.jogadas > 5 else Palette.BIRD_ORANGE, sombra=4)
        desenhar_texto(tela, 'JOGADAS', 20, (lado.centerx, lado.y + 22), Palette.INK, contorno=None)
        desenhar_texto(tela, str(self.jogadas), 76, (lado.centerx, lado.y + 86), Palette.WHITE, espessura=4)
        tela.blit(texto(self.TEXTO_ATALHOS, 20, Palette.WHITE), (14, ALTURA - 30))
        mensagem, restante = self.aviso
        dica = mensagem if restante > 0 else 'Troque duas peças vizinhas para juntar 3 iguais'
        img = texto(dica, 22, Palette.BIRD_YELLOW if restante > 0 else Palette.WHITE)
        tela.blit(img, img.get_rect(center=(LARGURA // 2, AREA.bottom + 34)))
