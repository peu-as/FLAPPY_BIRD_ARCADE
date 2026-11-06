"""Modo Livre (treino): o jogo completo, sem vidas e sem fim.

Mesmas regras, física e fases do jogo clássico (herda da ClassicSession),
com estas diferenças:
  * sem cadastro e sem ranking: ESPAÇO no menu já começa a jogar;
  * bater não tira vida: o pássaro volta com a mesma invulnerabilidade
    de 1,2 s do clássico, e a queda é contada;
  * a dificuldade sobe com o TEMPO de jogo (um nível da curva de 25 a cada
    LIVRE_SEGUNDOS_POR_NIVEL segundos, sem contar pausas e alertas) e para no 25;
  * os ciclos (Donkey, Galaga, pássaros) continuam depois do 10, sem tela de vitória;
  * recorde: a maior sequência de pontos sem cair, guardada no save.
"""
from ..config.constants import LARGURA, TEMPO_INVULNERAVEL_MS
from ..config.debug import TECLAS_DESCE_NIVEL, TECLAS_SOBE_NIVEL
from ..config.difficulty_profiles import LIVRE_SEGUNDOS_POR_NIVEL, NIVEIS
from .classic_session import ClassicSession
from .coins import SessaoComMoedas
from .scenery import SessaoComCenarios
from .difficulty_curve import CurvaDificuldade

ESTADOS_QUE_CONTAM_TEMPO = ('JOGO', 'GALAGA', 'DONKEY')
CHAVE_RECORDE = 'free_best_streak'
COR_TITULO = (255, 225, 90)      # mesmo amarelo do HUD clássico
COR_TEXTO = (230, 230, 240)


class FreeSession(SessaoComCenarios, SessaoComMoedas, ClassicSession):
    dificuldade = CurvaDificuldade()
    NIVEL_MAXIMO_CICLO = float('inf')    # ciclos sem fim

    def __init__(self, recursos, audio, clock, save):
        self.save = save
        self.recordes = save.section('records')
        self.recorde_pendente = False    # recorde novo ainda não gravado em disco
        super().__init__(recursos, audio, clock)

    # ------------------------------------------------------------ estado
    def reiniciar(self):
        super().reiniciar()
        self.nivel_livre = 1             # nível da curva de 25 (pelo tempo)
        self.tempo_livre = 0.0           # s de jogo efetivo
        self.quedas = 0
        self.sequencia = 0               # pontos desde a última queda
        self.pontos_vistos = 0

    @property
    def nivel_dificuldade(self):
        return self.nivel_livre

    @property
    def melhor_sequencia(self):
        return self.recordes[CHAVE_RECORDE]

    def atualizar_recorde(self):
        """Texto de recorde da tela inicial (o clássico mostra o ranking)."""
        self.recorde = self.melhor_sequencia
        self.nome_recorde = 'maior sequência sem cair'

    # ------------------------------------------------------------ regras
    def acao_principal(self):
        if self.estado == 'MENU':
            self.iniciar()               # sem cadastro: o Modo Livre não usa ranking
        else:
            super().acao_principal()

    def perder_vida(self, agora_ms):
        """Batida sem fim de jogo: conta a queda e recoloca o jogador."""
        if agora_ms - self.ultimo_dano < TEMPO_INVULNERAVEL_MS:
            return
        self.ultimo_dano = agora_ms
        self.quedas += 1
        self.sequencia = 0
        self.gravar_recorde()
        self.tocar('colisao')
        self.reposicionar_apos_dano()

    def concluir_ciclo(self):
        """Fim da fase dos pássaros: começa outro ciclo (nunca a tela de vitória)."""
        self.especial = False
        self.definir_nivel(self.nivel + 1)
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        self.ultimo_dano = self.clock.ticks()
        self.mostrar_banner(f'CICLO {self.nivel}!', 'as fases especiais voltam')

    def ir_para_nivel(self, nivel):
        """Atalho de teste: leva também a dificuldade para esse nível."""
        self.nivel_livre = max(1, min(NIVEIS, nivel))
        self.tempo_livre = (self.nivel_livre - 1) * LIVRE_SEGUNDOS_POR_NIVEL
        super().ir_para_nivel(nivel)

    def tratar_atalho_teste(self, tecla):
        """Atalhos do clássico + (+ / -): dificuldade um nível acima / abaixo."""
        if tecla in TECLAS_SOBE_NIVEL:
            self.mudar_dificuldade_teste(self.nivel_livre + 1)
        elif tecla in TECLAS_DESCE_NIVEL:
            self.mudar_dificuldade_teste(self.nivel_livre - 1)
        else:
            super().tratar_atalho_teste(tecla)

    def mudar_dificuldade_teste(self, nivel):
        """Muda só a dificuldade (o ciclo de fases continua onde está).

        Vale na hora para o Flappy; Galaga e Donkey usam o nível novo na
        próxima vez que começarem.
        """
        self.modo_teste_usado = True
        self.nivel_livre = max(1, min(NIVEIS, nivel))
        self.tempo_livre = (self.nivel_livre - 1) * LIVRE_SEGUNDOS_POR_NIVEL
        if self.estado == 'JOGO':
            self.passaro.aplicar_dificuldade(self.params_nivel['gravidade'])
            self.mostrar_banner(f'NÍVEL {self.nivel_livre}!', '(atalho de teste)', COR_TITULO)

    def atualizar(self, dt, agora_ms):
        super().atualizar(dt, agora_ms)
        self.contar_pontos()
        if self.estado in ESTADOS_QUE_CONTAM_TEMPO and not self.pausado:
            self.tempo_livre += dt
            alvo = min(NIVEIS, 1 + int(self.tempo_livre // LIVRE_SEGUNDOS_POR_NIVEL))
            if alvo > self.nivel_livre:
                self.subir_dificuldade(alvo)

    def contar_pontos(self):
        ganho = self.pontos - self.pontos_vistos
        self.pontos_vistos = self.pontos
        if ganho > 0:
            self.sequencia += ganho
            if self.sequencia > self.melhor_sequencia:
                self.recordes[CHAVE_RECORDE] = self.sequencia
                self.recorde_pendente = True
                self.atualizar_recorde()

    def subir_dificuldade(self, nivel):
        """Novos canos já nascem com o nível novo; o pássaro ajusta a gravidade."""
        self.nivel_livre = nivel
        if self.estado == 'JOGO':
            self.passaro.aplicar_dificuldade(self.params_nivel['gravidade'])
            self.mostrar_banner(f'NÍVEL {nivel}!', 'a dificuldade aumentou', COR_TITULO)

    def gravar_recorde(self):
        if self.recorde_pendente:
            self.recorde_pendente = False
            self.save.save()

    def encerrar(self):
        """Chamado ao sair do modo: grava um recorde ainda pendente."""
        self.gravar_recorde()

    # ------------------------------------------------------------ HUD
    def desenhar_placar(self, com_medalha=True, com_nivel=False):
        """Pontos à esquerda (o saldo de moedas fica logo abaixo); à direita,
        o painel do Modo Livre (sem vidas e sem medalha)."""
        self.numero(self.pontos, 20, 45)
        # Linhas curtas, alinhadas à direita: não alcançam o centro da tela, onde
        # ficam avisos como "FASE DOS PÁSSAROS!" (teste de sobreposição por pixels).
        linhas = [
            ('MODO LIVRE', self.fonte, COR_TITULO),
            (f'NÍVEL {self.nivel_livre}/{NIVEIS}', self.fonte, COR_TEXTO),
            (f'QUEDAS {self.quedas}', self.fonte_tabela, COR_TEXTO),
            (f'SEQUÊNCIA {self.sequencia}', self.fonte_tabela, COR_TEXTO),
            (f'MELHOR {self.melhor_sequencia}', self.fonte_tabela, COR_TITULO),
        ]
        if com_nivel:
            linhas.append((self.texto_progresso(), self.fonte_tabela, COR_TEXTO))
        y = 46
        for texto, fonte, cor in linhas:
            imagem = fonte.render(texto, True, cor)
            self.tela.blit(imagem, (LARGURA - 12 - imagem.get_width(), y))
            y += imagem.get_height() + 3
