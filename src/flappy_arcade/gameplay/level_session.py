"""Casas dos mapas: desafios fechados com 3 vidas e de 1 a 3 estrelas.

Cada tipo de casa herda da ClassicSession, então a física, os obstáculos e
as fases são exatamente os do jogo original. Muda só a moldura do desafio:
  * a dificuldade é o nível N da curva de 25 (N = número da casa);
  * começa direto no desafio (sem menu, cadastro ou ranking);
  * termina com self.resultado = 'VITORIA' ou 'DERROTA', e a sessão congela
    nesse quadro: quem mostra o resultado é a LevelScene.
"""
from ..config.constants import LARGURA
from ..config.levels import (
    CASAS,
    VIDAS_POR_CASA,
    estrelas_por_danos,
    meta_flappy,
    tem_chefe,
)
from .classic_session import ClassicSession
from .difficulty_curve import CurvaDificuldade

CURVA = CurvaDificuldade()
COR_TITULO = (255, 225, 90)
COR_TEXTO = (230, 230, 240)


class DificuldadeDaCasa:
    """A curva de 25 níveis, ligando ou não o chefão das fases especiais."""

    def __init__(self, chefe):
        self.chefe = chefe

    def flappy(self, nivel):
        return CURVA.flappy(nivel)

    def galaga(self, nivel):
        return {**CURVA.galaga(nivel), 'chefe': self.chefe}

    def donkey(self, nivel):
        return {**CURVA.donkey(nivel), 'chefe': self.chefe}


class LevelSession(ClassicSession):
    """Base das casas. As subclasses dizem como o desafio começa e termina."""

    def __init__(self, recursos, audio, clock, casa):
        self.casa = max(1, min(CASAS, casa))
        self.chefe = tem_chefe(self.casa)
        self.dificuldade = DificuldadeDaCasa(self.chefe)
        super().__init__(recursos, audio, clock)

    @property
    def nivel_dificuldade(self):
        return self.casa

    def reiniciar(self):
        super().reiniciar()
        self.vidas = VIDAS_POR_CASA
        self.danos = 0
        self.resultado = None            # None, 'VITORIA' ou 'DERROTA'
        self.iniciar()                   # sai do menu e para a música de abertura
        self.comecar()

    def comecar(self):
        raise NotImplementedError

    @property
    def objetivo(self):
        raise NotImplementedError

    @property
    def estrelas(self):
        return estrelas_por_danos(self.danos) if self.resultado == 'VITORIA' else 0

    # ---- o que muda em relação ao clássico ----
    def atualizar_recorde(self):
        self.recorde, self.nome_recorde = 0, ''

    def registrar_partida(self, zerou=False):
        """Mapas não usam o ranking."""

    def atualizar(self, dt, agora_ms):
        if not self.resultado:
            super().atualizar(dt, agora_ms)

    def perder_vida(self, agora_ms):
        vidas_antes = self.vidas
        super().perder_vida(agora_ms)
        if self.vidas < vidas_antes:
            self.danos += 1

    def finalizar(self):
        """Acabaram as vidas."""
        self.encerrar_casa('DERROTA')

    def aplicar_efeitos_fase(self, fase, estado_fase, agora_ms):
        fase.vidas_ganhas = 0            # nos mapas, vencer dá estrelas, não vidas
        super().aplicar_efeitos_fase(fase, estado_fase, agora_ms)

    def encerrar_casa(self, resultado):
        if self.resultado:
            return
        self.resultado = resultado
        self.pausado = False
        self.tocar('ponto' if resultado == 'VITORIA' else 'morte')

    # ---- HUD: pontos, vidas e a casa ----
    def desenhar_placar(self, com_medalha=True, com_nivel=False):
        super().desenhar_placar(com_medalha=False, com_nivel=False)
        rotulo = self.fonte.render(f'CASA {self.casa}/{CASAS}', True, COR_TITULO)
        self.tela.blit(rotulo, (LARGURA - 12 - rotulo.get_width(), 78))
        progresso = self.texto_progresso()
        if progresso:
            imagem = self.fonte_tabela.render(progresso, True, COR_TEXTO)
            self.tela.blit(imagem, (LARGURA - 12 - imagem.get_width(), 100))

    def texto_progresso(self):
        return ''


class FlappyLevelSession(LevelSession):
    """Passar por N canos; nas casas de chefão, pela fase dos pássaros."""

    def comecar(self):
        if self.chefe:
            self.iniciar_fase_passaros()
            self.meta = self.fim_passaros_em
        else:
            self.meta = meta_flappy(self.casa)
            self.passaro = self.novo_passaro_classico()   # já com a gravidade da casa

    @property
    def objetivo(self):
        meta = self.meta - self.pontos
        return f'Passe por {meta} pássaros' if self.chefe else f'Passe por {meta} canos'

    def verificar_gatilhos(self):
        if self.estado == 'JOGO' and self.pontos >= self.meta:
            self.encerrar_casa('VITORIA')

    def texto_progresso(self):
        return f'FALTAM {max(0, self.meta - self.pontos)}'


class _FaseEspecialSession(LevelSession):
    VARIANTE = None

    def comecar(self):
        self.iniciar_fase_especial(self.VARIANTE)

    def encerrar_fase_especial(self):
        """A fase acabou: vitória só se o objetivo foi cumprido (tempo esgotado perde)."""
        fase = self.galaga or self.donkey
        self.encerrar_casa('VITORIA' if fase.resultado == 'VITORIA' else 'DERROTA')

    def verificar_gatilhos(self):
        """Sem ciclo de fases: a casa é só esta fase."""


class GalagaLevelSession(_FaseEspecialSession):
    VARIANTE = 'GALAGA'

    @property
    def objetivo(self):
        return ('Derrube a formação e vença o Boss Galaga' if self.chefe
                else 'Derrube toda a formação antes do tempo acabar')


class DonkeyLevelSession(_FaseEspecialSession):
    VARIANTE = 'DONKEY'

    @property
    def objetivo(self):
        return ('Atravesse a selva e derrote o Kong Furioso' if self.chefe
                else 'Atravesse a selva desviando dos barris')


SESSOES_POR_MAPA = {
    'flappy': FlappyLevelSession,
    'galaga': GalagaLevelSession,
    'donkey': DonkeyLevelSession,
}
