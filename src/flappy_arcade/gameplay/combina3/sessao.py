"""Sessão do Combina 3: uma casa do mapa, da primeira troca ao resultado.

Cumpre o mesmo contrato das outras sessões de casa (veja scenes/level_scene.py).
As regras da casa (objetivos, chefão, ataques) ficam em partida.py; aqui
ficam a entrada, as animações e o HUD.

Uma jogada anda em etapas, para a tela animar cada uma:
    PRONTO -> TROCA (as duas peças trocam de lugar) -> ESTOURO (o que combinou some)
           -> QUEDA (as peças caem e entram novas) -> ESTOURO de novo se houver cascata
           -> ... -> ATAQUE (casas de chefão, a cada N jogadas) -> PRONTO
           (ou EMBARALHA se não sobrou jogada possível)

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
from .partida import Partida
from .visual import AREA, VisualCombina3, casa_em

PRONTO, TROCA, ESTOURO, QUEDA, EMBARALHA, ATAQUE = 'PRONTO', 'TROCA', 'ESTOURO', 'QUEDA', 'EMBARALHA', 'ATAQUE'
DT = 1 / 30
TEMPO_TROCA, TEMPO_ESTOURO, TEMPO_MINIMO_QUEDA, TEMPO_EMBARALHA = 0.18, 0.22, 0.12, 0.7
TEMPO_ATAQUE = 0.75
SEGUNDOS_PARA_DICA = 5.0
ARRASTE_MINIMO = 24
SETAS = {pygame.K_LEFT: (0, -1), pygame.K_RIGHT: (0, 1), pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0)}
HUD = pygame.Rect(14, 12, 350, 150)
POS_CHEFE = (HUD.x + 64, HUD.y + 92)          # de onde saem os ataques


def _milhar(n):
    return f'{n:,}'.replace(',', '.')


class Combina3Session:
    estado = 'JOGO'                # para a pausa: a partida está em andamento
    pausado = False
    TEXTO_ATALHOS = 'P ou ESC: Pausa'

    def __init__(self, recursos, audio, clock, casa, semente=None):
        self.recursos, self.audio, self.clock = recursos, audio, clock
        self.casa = casa
        self.definicao = cfg.casa_combina3(casa)
        self.partida = Partida(self.definicao, semente=semente)
        self.tab = self.partida.tab
        self.visual = VisualCombina3(recursos)
        self.visual.sincronizar(self.tab)
        self.tela = pygame.Surface((LARGURA, ALTURA))
        self.etapa = PRONTO
        self.tempo_etapa = 0.0
        self.tempo = 0.0
        self.ocioso = 0.0
        self.onda = None
        self.ataque = None
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
    def jogadas(self):
        return self.partida.jogadas

    @property
    def usadas(self):
        return self.partida.usadas

    @property
    def objetivo(self):
        return cfg.descrever(self.definicao)

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
        self.partida.usar_jogada()
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
        dano = self.partida.aplicar(onda)
        if dano:
            self.visual.dano_no_chefe(POS_CHEFE, dano)
        self.visual.sincronizar(self.tab)
        self.audio.play_sfx('ponto', min(0.7, 0.3 + 0.1 * onda.multiplicador))
        self._mudar(ESTOURO)

    def _fim_da_jogada(self):
        self.onda = None
        if self.partida.cumprida():
            sobrando = self.jogadas
            self.moedas_coletadas += cfg.MOEDAS_POR_VITORIA + sobrando // cfg.JOGADAS_POR_MOEDA
            self.estrelas = cfg.estrelas_combina3(self.definicao.jogadas, self.usadas)
            self.resultado = 'VITORIA'
            return
        if self.jogadas <= 0:
            self.resultado = 'DERROTA'
            self.audio.play_sfx('morte', 0.5)
            return
        self.ataque = self.partida.planejar_ataque()
        if self.ataque:
            self.visual.ataque(POS_CHEFE, self.ataque)
            quem = self.definicao.chefao
            frase = {'rei_inseto': 'O REI-INSETO PRENDEU PEÇAS!', 'kong': 'O KONG JOGOU BARRIS!',
                     'dupla': 'OS CHEFÕES ATACARAM!'}[quem.nome]
            self.aviso = (frase if not self.ataque.bravo else frase.replace('!', ' (BRAVO)!'), 1.8)
            self.audio.play_sfx('colisao', 0.5)
            self._mudar(ATAQUE)
        else:
            self._seguir()

    def _seguir(self):
        """Fim de tudo: pronto para a próxima jogada (ou embaralha se não houver nenhuma)."""
        if self.tab.dica() is None:
            self.tab.embaralhar()
            self.visual.sincronizar(self.tab)
            self.aviso = ('SEM JOGADAS: EMBARALHANDO!', 1.6)
            self._mudar(EMBARALHA)
        else:
            self._mudar(PRONTO)

    def _ataque_chegou(self):
        removidas = self.partida.aplicar_ataque(self.ataque)
        self.ataque = None
        self.visual.ao_ataque(removidas)
        self.visual.sincronizar(self.tab)
        if self.partida.embaralhou:                # o ataque tirou a última jogada: embaralhou
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
        elif self.etapa == ATAQUE and self.tempo_etapa >= TEMPO_ATAQUE:
            self._ataque_chegou()
        elif self.etapa == EMBARALHA and self.tempo_etapa >= TEMPO_EMBARALHA and self.visual.parado():
            self._mudar(PRONTO)

    # ------------------------------------------------------------ desenho
    def desenhar(self):
        tela = self.tela
        self.visual.desenhar(tela, self.tab, self.tempo, self.selecao, self.cursor, self.dica,
                             self.partida.casulos, self.partida.barris)
        self._hud(tela)
        self.visual.desenhar_ataques(tela)

    def _hud(self, tela):
        painel(tela, HUD, Palette.PANEL, sombra=4)
        if self.definicao.chefao:
            self._hud_chefe(tela)
        elif [o[0] for o in self.definicao.objetivos] == [cfg.PONTOS]:
            self._hud_pontos(tela)
        else:
            self._hud_objetivos(tela)
        lado = pygame.Rect(376, 12, LARGURA - 390, 150)
        painel(tela, lado, Palette.PANEL_LIGHT if self.jogadas > 5 else Palette.BIRD_ORANGE, sombra=4)
        desenhar_texto(tela, 'JOGADAS', 20, (lado.centerx, lado.y + 22), Palette.INK, contorno=None)
        desenhar_texto(tela, str(self.jogadas), 76, (lado.centerx, lado.y + 86), Palette.WHITE, espessura=4)
        tela.blit(texto(self.TEXTO_ATALHOS, 20, Palette.WHITE), (14, ALTURA - 30))
        mensagem, restante = self.aviso
        dica = mensagem if restante > 0 else 'Troque duas peças vizinhas para juntar 3 iguais'
        img = texto(dica, 22, Palette.BIRD_YELLOW if restante > 0 else Palette.WHITE)
        tela.blit(img, img.get_rect(center=(LARGURA // 2, AREA.bottom + 34)))

    def _moedas(self, tela, y):
        icone = icone_moeda(10)
        tela.blit(icone, icone.get_rect(midright=(HUD.right - 62, y + 12)))
        desenhar_texto(tela, f'+{self.moedas_coletadas}', 22, topo_esquerdo=(HUD.right - 56, y), cor=Palette.COIN)

    @staticmethod
    def _barra(tela, rect, fracao, cor):
        pygame.draw.rect(tela, Palette.INK, rect.inflate(6, 6), border_radius=10)
        pygame.draw.rect(tela, (90, 70, 80), rect, border_radius=8)
        cheia = rect.copy()
        cheia.w = round(rect.w * max(0.0, min(1.0, fracao)))
        if cheia.w > 4:
            pygame.draw.rect(tela, cor, cheia, border_radius=8)

    def _hud_pontos(self, tela):
        meta = self.definicao.objetivos[0][1]
        desenhar_texto(tela, 'PONTOS', 20, topo_esquerdo=(HUD.x + 16, HUD.y + 10), cor=Palette.INK, contorno=None)
        desenhar_texto(tela, _milhar(self.tab.pontos), 44, topo_esquerdo=(HUD.x + 16, HUD.y + 30),
                       cor=Palette.WHITE, espessura=3)
        barra = pygame.Rect(HUD.x + 16, HUD.y + 84, HUD.w - 32, 20)
        self._barra(tela, barra, self.tab.pontos / meta, Palette.LOGO_GREEN)
        tela.blit(texto(f'META {_milhar(meta)}', 20, Palette.INK, None), (barra.x, barra.bottom + 8))
        self._moedas(tela, barra.bottom + 6)

    def _hud_objetivos(self, tela):
        desenhar_texto(tela, 'OBJETIVO', 20, topo_esquerdo=(HUD.x + 16, HUD.y + 10), cor=Palette.INK, contorno=None)
        progresso = self.partida.progresso()
        n = len(progresso)
        largura = (HUD.w - 32 - 10 * (n - 1)) // n
        for i, (objetivo, feito, alvo) in enumerate(progresso):
            chip = pygame.Rect(HUD.x + 16 + i * (largura + 10), HUD.y + 34, largura, 78)
            pronto = feito >= alvo
            pygame.draw.rect(tela, (70, 150, 80) if pronto else Palette.PANEL_LIGHT, chip, border_radius=10)
            pygame.draw.rect(tela, Palette.INK, chip, 3, border_radius=10)
            icone = self.visual.icone_objetivo(objetivo)
            tela.blit(icone, icone.get_rect(center=(chip.centerx, chip.y + 26)))
            if pronto:
                self.visual.visto(tela, (chip.right - 16, chip.y + 14))
            rotulo = 'FEITO!' if pronto else f'{feito}/{alvo}'
            desenhar_texto(tela, rotulo, 22 if len(rotulo) <= 7 else 18, (chip.centerx, chip.y + 60),
                           Palette.WHITE, espessura=2)
        desenhar_texto(tela, f'PONTOS {_milhar(self.tab.pontos)}', 20, topo_esquerdo=(HUD.x + 16, HUD.y + 120),
                       cor=Palette.INK, contorno=None)
        self._moedas(tela, HUD.y + 118)

    def _hud_chefe(self, tela):
        chefao, p = self.definicao.chefao, self.partida
        titulo = chefao.titulo + ('  BRAVO!' if p.bravo else '')
        desenhar_texto(tela, titulo, 20, topo_esquerdo=(HUD.x + 16, HUD.y + 10),
                       cor=Palette.DANGER if p.bravo else Palette.INK, contorno=None)
        self.visual.desenhar_chefe(tela, chefao.nome, POS_CHEFE, p.bravo, self.tempo)
        barra = pygame.Rect(HUD.x + 128, HUD.y + 50, HUD.w - 146, 24)
        self._barra(tela, barra, p.vida / chefao.vida, Palette.DANGER)
        desenhar_texto(tela, f'VIDA {p.vida}', 20, topo_esquerdo=(barra.x, barra.bottom + 8), cor=Palette.INK,
                       contorno=None)
        falta = p.jogadas_para_ataque()
        aviso = 'ATACA NA PRÓXIMA!' if falta == 1 else f'ATACA EM {falta} JOGADAS'
        desenhar_texto(tela, aviso, 18, topo_esquerdo=(barra.x, barra.bottom + 34),
                       cor=Palette.DANGER if falta == 1 else Palette.INK, contorno=None)
        self._moedas(tela, HUD.y + 10)
