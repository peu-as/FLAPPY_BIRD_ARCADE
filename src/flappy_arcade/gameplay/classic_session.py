"""Sessão do jogo clássico completo (o jogo original).

Reúne estados (MENU, CADASTRO, JOGO, ALERTA, GALAGA, DONKEY, GAMEOVER,
VITORIA), regras do ciclo de níveis, entrada e desenho das telas.

Não conhece a janela nem o loop principal: recebe recursos, áudio e relógio
prontos (injeção de dependência) e desenha numa superfície lógica 575x860.
Quem a conduz é a GameScene.
"""
import math
import random

import pygame

from ..config.constants import (
    ALTURA,
    ESPACO_ENTRE_CANOS,
    ESTADOS_ATIVOS,
    LARGURA,
    MAX_ICONES_VIDA,
    MAX_NOME,
    NIVEL_MAXIMO,
    NOMES_FASES,
    ORDEM_FASES_ESPECIAIS,
    PONTOS_ANTES_PASSAROS,
    PONTOS_ENTRE_ESPECIAIS,
    TEMAS,
    TEMAS_DIA,
    TEMAS_TARDE,
    TEMPO_ALERTA,
    TEMPO_INVULNERAVEL_MS,
    TEMPO_TEMA,
    TOP_RANKING,
    VIDAS_INICIAIS,
    Y_TABELA_RANKING,
)
from ..config.debug import ATALHO_INVALIDA_RANKING, MODO_TESTE, TECLAS_NIVEL
from ..systems import apresentacao
from .difficulty import (
    DificuldadeOriginal,
    desvio_maximo_passagem,
    proximo_multiplo,
    sortear_topo_passagem,
)
from .donkey import FaseDonkey
from .flappy import Chao, Obstaculo, Passaro
from .galaga import FaseGalaga
from ..systems.ranking import (
    adicionar_registro,
    ler_ranking,
    limpar_nome,
    salvar_ranking,
)


# MENU: tela inicial; JOGO: simulação ativa; GAMEOVER: encerramento.
# GALAGA: fase especial em que o jogo vira um "Galaga".
# ALERTA: aviso de 5 s (banner + contagem regressiva) que antecede
# toda fase especial; a cena do Flappy fica congelada e sem dano.
# DONKEY: fase especial temática, com barris, cipós e bananas.
# CADASTRO: tela onde o jogador digita o nome antes de cada partida.
# VITORIA: tela de "Honra Máxima", exibida ao concluir o nível 10.
# A separação por estados evita que a mesma tecla execute ações
# incompatíveis em diferentes momentos.
class ClassicSession:
    """Estados, regras e desenho do jogo clássico completo.

    Dependências injetadas:
      recursos  -- Recursos já carregados (sprites e sons)
      audio     -- AudioManager (respeita as configurações de música e SFX)
      clock     -- relógio com now() em segundos e ticks() em milissegundos
    """
    # Tabelas de dificuldade (o Modo Livre troca pela curva de 25 níveis).
    dificuldade = DificuldadeOriginal()
    # Último nível do ciclo: concluí-lo mostra a tela de Honra Máxima.
    NIVEL_MAXIMO_CICLO = NIVEL_MAXIMO
    # Atalhos na barra do topo. As cenas do jogo trocam por "P ou ESC: Pausa",
    # porque nelas o ESC abre o menu de pausa em vez de sair.
    TEXTO_ATALHOS = 'P: Pausa | ESC: Sair'

    def __init__(self, recursos, audio, clock):
        self.recursos = recursos
        self.audio = audio
        self.clock = clock
        self.tela = pygame.Surface((LARGURA,ALTURA))
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_grande = pygame.font.Font(None, 52)
        # Fontes maiores para o banner do alerta e a contagem regressiva.
        self.fonte_banner = pygame.font.Font(None, 88)
        self.fonte_contagem = pygame.font.Font(None, 200)
        # Fontes da tabela do ranking.
        self.fonte_tabela = pygame.font.Font(None, 22)
        self.fonte_titulo_tabela = pygame.font.Font(None, 28)
        # Em vez de um único recorde, carrega o ranking
        # completo e o nome do último jogador (sugestão no cadastro).
        self.ranking, self.jogador = ler_ranking()
        self.atualizar_recorde()
        self.reiniciar()

    @property
    def som_ativo(self):
        """Indicador do HUD: efeitos sonoros ligados."""
        return self.audio.sfx_enabled

    def tocar(self, nome, volume=0.5):
        self.audio.play_sfx(nome, volume)

    def reiniciar(self):
        """Prepara uma nova partida sem apagar o recorde persistente."""
        self.estado = 'MENU'
        self.passaro = Passaro(self.recursos)
        self.chao = Chao(self.recursos.chao)
        self.obstaculos = []
        self.pontos = 0
        self.vidas = VIDAS_INICIAIS
        self.pausado = False
        self.tempo_ativo = 0.0
        self.tema = 'bg'
        self.especial = False
        self.ultimo_dano = -TEMPO_INVULNERAVEL_MS
        # Cadastro e ranking. O nome do jogador (self.jogador) NÃO é
        # apagado aqui: ele vale também para a próxima partida.
        self.nome_digitado = ''              # texto do campo de cadastro
        self.erro_nome_ate = 0.0             # até quando mostrar o aviso "digite um nome"
        self.posicao_final = None            # posição desta partida no ranking
        self.fim_iniciado = 0.0
        self.ultimo_arcade = 0.0
        self.contador_arcade = 0
        # Ciclos (níveis): cada nível tem duas fases especiais (nos múltiplos
        # de 35 pontos) e, 20 pontos depois delas, a fase dos pássaros (veja
        # definir_nivel). self.especial passa a significar "fase dos pássaros ativa".
        self.nivel = 1
        self.pendentes = []                 # fases especiais que ainda faltam neste ciclo
        self.proximo_especial = PONTOS_ENTRE_ESPECIAIS   # próxima pontuação-gatilho
        self.pontos_para_passaros = None    # pontuação que libera a fase dos pássaros
        self.fim_passaros_em = None         # pontuação em que a fase dos pássaros acaba
        self.definir_nivel(1)
        # Estado do alerta de 5 s que antecede a fase.
        self.variante_alerta = None                    # 'GALAGA' ou 'DONKEY'
        self.alerta_restante = 0.0                     # s que faltam para a fase começar
        self.alerta_decorrido = 0.0                    # s desde o início (anima o banner)
        self.alerta_ultimo_numero = 0                  # último número "bipado" na contagem
        # Controle de cada variante de fase.
        self.galaga = None                     # objeto FaseGalaga (ou None)
        self.donkey = None                     # objeto FaseDonkey (ou None)
        # Banner temporário do modo clássico (subida de nível, fase dos pássaros).
        self.banner = ('', '', (255, 255, 255))
        self.banner_tempo = 0.0
        # Tela de Honra Máxima: partículas dos fogos de artifício.
        self.fogos = []
        self.proximo_fogo = 0.0
        # Partida em que algum atalho de teste foi usado: não entra no ranking.
        self.modo_teste_usado = False
        self.tocar('inicio')

    def iniciar(self):
        self.estado = 'JOGO'
        self.tempo_ativo = 0.0
        self.obstaculos = [self.novo_obstaculo()]      # já com a abertura do nível
        if self.recursos.sons['inicio']:
            self.recursos.sons['inicio'].stop()

    # CADASTRO DO JOGADOR (antes de cada partida)
    def iniciar_cadastro(self):
        """MENU -> CADASTRO: abre o campo de nome, já preenchido com o último
        jogador (basta apertar ENTER para repetir o nome)."""
        self.estado = 'CADASTRO'
        self.nome_digitado = self.jogador
        self.erro_nome_ate = 0.0
        # Repetição de tecla só aqui: segurar BACKSPACE apaga várias letras.
        # Fora do cadastro ela fica desligada (senão repetiria o "bater asas").
        pygame.key.set_repeat(350, 45)

    def sair_cadastro(self):
        pygame.key.set_repeat()          # sem argumentos: desliga a repetição

    def confirmar_cadastro(self):
        """ENTER no cadastro: valida o nome e começa a partida."""
        nome = limpar_nome(self.nome_digitado)
        if not nome:
            self.erro_nome_ate = self.clock.now() + 1.5   # aviso vermelho por 1,5 s
            return
        self.jogador = nome
        self.sair_cadastro()
        salvar_ranking(self.ranking, self.jogador)        # lembra o último jogador
        self.iniciar()

    def tratar_tecla_cadastro(self, evento):
        """Teclado na tela de cadastro.

        Roda ANTES dos atalhos do jogo (S, P, G, K, T...): senão, letras
        comuns do nome (como o "s") ligariam/desligariam o som, pausariam, etc.
        """
        if evento.key == pygame.K_ESCAPE:
            self.sair_cadastro()
            self.estado = 'MENU'
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.confirmar_cadastro()
        elif evento.key == pygame.K_BACKSPACE:
            self.nome_digitado = self.nome_digitado[:-1]
        elif evento.key == pygame.K_DELETE:
            self.nome_digitado = ''
        elif (len(self.nome_digitado) < MAX_NOME and evento.unicode
              and evento.unicode.isprintable()):
            self.nome_digitado += evento.unicode
        return True

    def atualizar_recorde(self):
        """Recorde exibido no menu e no GAME OVER = melhor pontuação do ranking."""
        if self.ranking:
            self.recorde = self.ranking[0]['pontos']
            self.nome_recorde = self.ranking[0]['nome']
        else:
            self.recorde, self.nome_recorde = 0, 'Anônimo'

    def registrar_partida(self, zerou=False):
        """Vincula a pontuação final ao jogador cadastrado e salva o ranking.

        O registro guarda também o nível alcançado e se o
        jogador zerou o jogo (zerou=True na tela de Honra Máxima).
        """
        if self.modo_teste_usado and ATALHO_INVALIDA_RANKING:
            self.posicao_final = None       # partida com atalho de teste não vale recorde
            return
        nome = self.jogador or 'Anônimo'
        self.ranking, self.posicao_final = adicionar_registro(
            self.ranking, nome, self.pontos, self.nivel, zerou)
        self.atualizar_recorde()
        salvar_ranking(self.ranking, self.jogador)

    # DIFICULDADE PROGRESSIVA (modo clássico)
    @property
    def nivel_dificuldade(self):
        """Nível usado nas tabelas de dificuldade. No clássico é o próprio
        nível do ciclo; o Modo Livre o calcula pelo tempo de jogo."""
        return self.nivel

    @property
    def params_nivel(self):
        """Parâmetros do Flappy no nível atual (gravidade, abertura, velocidade...)."""
        return self.dificuldade.flappy(self.nivel_dificuldade)

    def gravidade_atual(self):
        """Gravidade do nível atual."""
        return self.params_nivel['gravidade']

    def novo_passaro_classico(self):
        """Pássaro do modo clássico, já com a gravidade do nível atual."""
        passaro = Passaro(self.recursos)
        passaro.aplicar_dificuldade(self.gravidade_atual())
        return passaro

    def novo_obstaculo(self):
        """Par de canos (ou de pássaros, na fase dos pássaros) nascendo na borda
        direita, com a abertura e a velocidade do nível. Na fase dos
        pássaros dos níveis altos a passagem também sobe e desce."""
        p = self.params_nivel
        oscilacao = p['oscilacao_passaros'] if self.especial else 0.0
        # A altura da passagem nunca fica tão distante da anterior que a
        # subida seja impossível. Se os pássaros oscilam, cada passagem pode estar até
        # 'oscilacao' px fora da base: desconta-se 2x isso do desvio permitido.
        topo = None
        if self.obstaculos:
            sprite = self.passaro.sprite
            desvio = desvio_maximo_passagem(
                p['abertura'], p['velocidade'], self.passaro.gravidade, self.passaro.impulso,
                self.recursos.cano_dia.get_width(), sprite.get_width(), sprite.get_height())
            topo = sortear_topo_passagem(self.obstaculos[-1].topo_base,
                                         max(80, desvio - 2*oscilacao))
        return Obstaculo(LARGURA, self.recursos, self.especial, self.tema,
                         velocidade=p['velocidade'], abertura=p['abertura'],
                         oscilacao=oscilacao, topo=topo)

    # CICLOS (NÍVEIS): especiais por pontuação, fase dos pássaros e vitória
    def ordem_especiais(self, nivel):
        """As duas fases especiais do ciclo, na ordem em que aparecem: os níveis
        ímpares começam pelo Donkey Kong; os pares, pela Galaga."""
        ordem = list(ORDEM_FASES_ESPECIAIS)
        return ordem if nivel % 2 == 1 else ordem[::-1]

    def definir_nivel(self, nivel):
        """Começa o ciclo de um nível: zera o progresso do ciclo e recalcula os
        gatilhos. A pontuação NÃO é alterada. A dificuldade do modo clássico vem
        de self.nivel (veja nivel_dificuldade), então ela muda junto."""
        self.nivel = max(1, min(self.NIVEL_MAXIMO_CICLO, int(nivel)))
        self.especial = False                    # fora da fase dos pássaros
        self.pendentes = self.ordem_especiais(self.nivel)
        self.proximo_especial = proximo_multiplo(self.pontos)
        self.pontos_para_passaros = None
        self.fim_passaros_em = None

    def alvo_gatilho(self):
        """Pontuação do próximo evento do ciclo (usada pela tecla de teste T)."""
        if self.especial:
            return self.fim_passaros_em
        if self.pendentes:
            return self.proximo_especial
        return self.pontos_para_passaros

    def texto_progresso(self):
        """Texto curto do HUD: o que falta para a próxima fase do ciclo."""
        if self.especial:
            return f'FALTAM {max(0, self.fim_passaros_em - self.pontos)}'     # curto: o título já diz "pássaros"
        if self.pendentes:
            return f'PRÓXIMA FASE EM {self.proximo_especial}'
        return f'PÁSSAROS EM {self.pontos_para_passaros}'

    def mostrar_banner(self, titulo, subtitulo='', cor=(255, 120, 60)):
        """Banner pulsante no centro da tela do modo clássico, por 2,5 s."""
        self.banner = (titulo, subtitulo, cor)
        self.banner_tempo = 2.5

    # FASES ESPECIAIS: gatilho -> alerta de 5 s -> fase -> volta
    def verificar_gatilhos(self):
        """Decide, a cada quadro do modo clássico, o próximo passo do ciclo.

        - Durante a FASE DOS PÁSSAROS as fases especiais NÃO são acionadas: só se
          confere se a fase dos pássaros já acabou (pontos >= fim_passaros_em).
          Os múltiplos de 35 que passarem durante ela são ignorados.
        - Com fase especial pendente: o alerta dispara quando a pontuação chega
          ao próximo múltiplo de 35 (o cronograma avança AQUI, no disparo).
        - Concluídas as duas especiais: a fase dos pássaros é liberada 20 pontos
          depois (pontos_para_passaros).
        As teclas de teste não passam por aqui e não alteram o cronograma real.
        """
        if self.estado != 'JOGO':
            return
        if self.especial:
            if self.pontos >= self.fim_passaros_em:
                self.concluir_ciclo()
        elif self.pendentes:
            if self.pontos >= self.proximo_especial:
                self.iniciar_alerta(self.pendentes.pop(0))
        elif self.pontos >= self.pontos_para_passaros:
            self.iniciar_alerta('PASSAROS')

    def iniciar_alerta(self, variante):
        """Entra no estado ALERTA: congela o Flappy e inicia a contagem de 5 s."""
        self.estado = 'ALERTA'
        self.variante_alerta = variante
        self.alerta_restante = TEMPO_ALERTA
        self.alerta_decorrido = 0.0
        self.alerta_ultimo_numero = 0

    def atualizar_alerta(self, dt):
        """Um quadro do alerta. Como usa dt e a pausa interrompe atualizar(),
        o relógio de 5 s também pausa com a tecla P."""
        self.alerta_decorrido += dt
        self.alerta_restante -= dt
        numero = math.ceil(max(0.0, self.alerta_restante))
        if numero > 0 and numero != self.alerta_ultimo_numero:
            self.alerta_ultimo_numero = numero
            self.tocar('ponto', 0.3)         # "bip" a cada segundo (5, 4, 3, 2, 1)
        if self.alerta_restante <= 0:
            self.iniciar_fase_especial(self.variante_alerta)

    def iniciar_fase_especial(self, variante):
        """Troca para o estado da variante e cria a fase.

        O tempo_ativo do Flappy fica congelado: o ciclo de temas só continua
        depois que a fase termina. A dificuldade da fase vem do provedor de
        dificuldade (self.dificuldade), e a fase dos pássaros também passa
        por aqui (variante 'PASSAROS').
        """
        if variante == 'PASSAROS':
            self.iniciar_fase_passaros()
            return
        self.obstaculos = []
        # Zera a trava de dano do Flappy para não ignorar um dano da fase nova.
        self.ultimo_dano = -TEMPO_INVULNERAVEL_MS
        if variante == 'DONKEY':
            self.estado = 'DONKEY'
            n = self.nivel_dificuldade
            self.donkey = FaseDonkey(self.recursos, n - 1, self.dificuldade.donkey(n))
            self.passaro = self.novo_passaro_donkey()
        else:
            self.estado = 'GALAGA'
            n = self.nivel_dificuldade
            self.galaga = FaseGalaga(self.recursos, n - 1, self.dificuldade.galaga(n))

    def iniciar_fase_passaros(self):
        """Começa a fase dos pássaros: o Flappy volta com PÁSSAROS no lugar
        dos canos e os pontos contam normalmente. Ela dura 'pontos_passaros'
        pontos; nos níveis altos os pássaros sobem e descem. Enquanto ela durar,
        as fases especiais não são acionadas."""
        self.especial = True
        faltam = self.params_nivel['pontos_passaros']
        self.fim_passaros_em = self.pontos + faltam
        self.estado = 'JOGO'
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        self.ultimo_dano = self.clock.ticks()
        self.mostrar_banner('FASE DOS PÁSSAROS!', f'passe por {faltam} pássaros: vale pontos',
                            (255, 225, 90))

    def novo_passaro_donkey(self):
        """Pássaro "noturno" no ponto de partida, combinando com a selva escura."""
        passaro = Passaro(self.recursos)
        passaro.familia = 'noite'
        return passaro

    def encerrar_fase_especial(self):
        """Volta ao Flappy Bird, preservando pontos, vidas e tempo.

        Também avança o ciclo: se ainda há fase especial
        pendente, calcula o próximo múltiplo de 35; se as duas já foram feitas,
        a fase dos pássaros fica marcada para 20 pontos depois. Uma fase que
        terminou por tempo esgotado também conta como "passada" (só a vida
        extra se perde).
        """
        if self.estado == 'GALAGA':
            self.galaga = None
        elif self.estado == 'DONKEY':
            self.donkey = None
        self.estado = 'JOGO'
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        # Pequena folga (invulnerabilidade) para o jogador voltar a bater asas.
        self.ultimo_dano = self.clock.ticks()
        if self.pendentes:
            self.proximo_especial = proximo_multiplo(self.pontos)
        else:
            self.pontos_para_passaros = self.pontos + PONTOS_ANTES_PASSAROS

    def concluir_ciclo(self):
        """Fim da fase dos pássaros = fim do ciclo: sobe de nível, ou, se
        era o nível 10, vence o jogo (tela de HONRA MÁXIMA)."""
        self.especial = False
        if self.nivel >= self.NIVEL_MAXIMO_CICLO:
            self.vitoria_final()
            return
        self.definir_nivel(self.nivel + 1)
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        self.ultimo_dano = self.clock.ticks()
        self.mostrar_banner(f'NÍVEL {self.nivel}!', 'mais gravidade, velocidade e canos fechados')

    def ir_para_nivel(self, nivel):
        """ATALHO DE TESTE (teclas 1 a 9 e 0): muda NA HORA para o nível.

        Cancela o alerta ou a fase em andamento, recomeça o ciclo do nível
        (fases pendentes e gatilhos) e aplica ao modo clássico a gravidade, a
        abertura e a velocidade daquele nível. Os pontos não mudam."""
        self.galaga = None
        self.donkey = None
        self.estado = 'JOGO'
        self.definir_nivel(nivel)
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        self.ultimo_dano = self.clock.ticks()
        self.mostrar_banner(f'NÍVEL {self.nivel}!', '(atalho de teste)')

    def pular_para_chefe(self):
        """ATALHO DE TESTE (tecla B): pula a 1ª parte da Galaga ou do Donkey."""
        fase = self.galaga if self.estado == 'GALAGA' else self.donkey
        if fase:
            fase.pular_para_chefe()

    def vitoria_final(self):
        """Nível 10 concluído: grava a pontuação (marcada como "zerou") e
        mostra a tela de HONRA MÁXIMA."""
        self.estado = 'VITORIA'
        self.especial = False
        self.fim_iniciado = self.clock.now()
        self.fogos, self.proximo_fogo = [], 0.0
        self.registrar_partida(zerou=True)
        self.tocar('inicio')

    def atualizar_vitoria(self, dt):
        """Fogos de artifício da tela de vitória: explosões de partículas coloridas
        que sobem, se abrem e caem com a gravidade."""
        self.proximo_fogo -= dt
        if self.proximo_fogo <= 0:
            self.proximo_fogo = random.uniform(0.25, 0.6)
            cx, cy = random.randint(60, LARGURA-60), random.randint(80, 330)
            cor = random.choice([(255, 215, 0), (255, 90, 90), (90, 220, 255),
                                 (130, 255, 140), (255, 140, 255)])
            for _ in range(26):
                ang = random.uniform(0, 2*math.pi)
                vel = random.uniform(60, 230)
                self.fogos.append([cx, cy, vel*math.cos(ang), vel*math.sin(ang),
                                   random.uniform(0.8, 1.6), cor])
        for p in self.fogos:                     # x, y, vx, vy, vida, cor
            p[0] += p[2]*dt
            p[1] += p[3]*dt
            p[3] += 220*dt                       # gravidade
            p[4] -= dt
        self.fogos = [p for p in self.fogos if p[4] > 0]

    def finalizar(self):
        """Muda para GAMEOVER e grava a pontuação no ranking do jogador.

        O nome vem do cadastro (feito antes da partida) e TODA partida com
        pontos entra no ranking.
        """
        self.estado = 'GAMEOVER'
        self.fim_iniciado = self.clock.now()
        self.contador_arcade = 0
        self.ultimo_arcade = 0.0
        self.registrar_partida()
        self.tocar('fim')

    def perder_vida(self, agora_ms):
        if agora_ms-self.ultimo_dano < TEMPO_INVULNERAVEL_MS:
            return
        self.ultimo_dano = agora_ms
        self.vidas -= 1
        self.tocar('colisao')
        self.tocar('morte')
        if self.vidas <= 0:
            self.finalizar()
        else:
            self.reposicionar_apos_dano()

    def reposicionar_apos_dano(self):
        """Depois de um dano (sem fim de jogo), recoloca o jogador em jogo."""
        if self.estado == 'GALAGA':
            # Na Galaga, a nave volta ao centro; a formação continua.
            self.galaga.reposicionar_jogador()
        elif self.estado == 'DONKEY':
            # Na fase Donkey, o pássaro recomeça e a pista é limpa;
            # o cronômetro da fase continua de onde estava.
            self.passaro = self.novo_passaro_donkey()
            self.donkey.reposicionar()
        else:
            # Reinicia o pássaro e obstáculos, preservando pontos/tempo.
            # Já com a gravidade e a abertura do nível.
            self.passaro = self.novo_passaro_classico()
            self.obstaculos = [self.novo_obstaculo()]

    def tema_por_tempo(self):
        """Escolhe cenário e fase pelo tempo ativo, sem contar pausas."""
        # O tempo só escolhe o CENÁRIO (um tema novo a cada
        # TEMPO_TEMA s). Quem decide a fase dos pássaros é o ciclo por pontos.
        indice = int(self.tempo_ativo // TEMPO_TEMA)
        self.tema = TEMAS[indice % len(TEMAS)]
        self.passaro.familia = ('dia' if self.tema in TEMAS_DIA else
                                'tarde' if self.tema in TEMAS_TARDE else 'noite')

    def aplicar_efeitos_fase(self, fase, estado_fase, agora_ms):
        """Aplica na sessão o que a fase produziu neste
        quadro (comum à Galaga e ao Donkey Kong).

        As fases especiais NÃO somam pontos ao placar: são bônus. O que elas
        entregam é:
          - sons: efeitos a tocar;
          - vidas_ganhas: vidas extras (só quando a fase foi CONCLUÍDA);
          - dano: o jogador foi atingido (perde uma vida);
          - terminou: hora de voltar ao Flappy.
        """
        for nome in fase.sons:
            self.tocar(nome)
        fase.sons.clear()
        if fase.vidas_ganhas:
            self.vidas += fase.vidas_ganhas
            fase.vidas_ganhas = 0
        if fase.dano:
            fase.dano = False
            self.perder_vida(agora_ms)
            if self.estado != estado_fase:   # acabaram as vidas: GAMEOVER
                return
        if fase.terminou:
            self.encerrar_fase_especial()

    def atualizar_galaga(self, dt, agora_ms):
        """Um quadro da fase Galaga: lê teclas, atualiza e aplica efeitos."""
        g = self.galaga
        # get_pressed() informa as teclas que estão seguradas AGORA,
        # ideal para movimento contínuo (os eventos KEYDOWN disparam uma vez).
        teclas = pygame.key.get_pressed()
        esquerda = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        direita = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]
        g.atualizar(dt, esquerda, direita, teclas[pygame.K_SPACE])
        self.aplicar_efeitos_fase(g, 'GALAGA', agora_ms)

    def atualizar_donkey(self, dt, agora_ms):
        """Um quadro da fase Donkey Kong: física do pássaro + fase."""
        d = self.donkey
        if not d.resultado:
            # Depois da vitória o pássaro fica parado até a fase acabar,
            # para não morrer por acidente durante a mensagem final.
            self.passaro.atualizar()
        d.atualizar(dt, self.passaro)
        self.aplicar_efeitos_fase(d, 'DONKEY', agora_ms)

    def atualizar(self, dt, agora_ms):
        """Avança a simulação, cria obstáculos e detecta colisões.

        dt é o intervalo em segundos; agora_ms é o relógio em milissegundos.
        """
        # A pausa vale para todos os estados ativos (JOGO, ALERTA,
        # GALAGA e DONKEY); cada fase especial tem seu próprio método.
        if self.pausado:
            return
        if self.estado == 'ALERTA':
            self.atualizar_alerta(dt)
            return
        if self.estado == 'GALAGA':
            self.atualizar_galaga(dt, agora_ms)
            return
        if self.estado == 'DONKEY':
            self.atualizar_donkey(dt, agora_ms)
            return
        if self.estado == 'VITORIA':          # fogos de artifício da tela final
            self.atualizar_vitoria(dt)
            return
        if self.estado != 'JOGO':
            return
        self.tempo_ativo += dt
        self.tema_por_tempo()
        # A cada quadro o pássaro recebe a gravidade (e o impulso)
        # do NÍVEL atual, o chão e os canos andam na velocidade do nível e os canos
        # novos já nascem com a abertura do nível (veja parametros_nivel).
        params = self.params_nivel
        self.passaro.aplicar_dificuldade(params['gravidade'])
        self.passaro.atualizar()
        self.chao.atualizar(params['velocidade'])
        if not self.obstaculos or self.obstaculos[-1].x < LARGURA-ESPACO_ENTRE_CANOS:
            self.obstaculos.append(self.novo_obstaculo())
        for obstaculo in self.obstaculos:
            obstaculo.atualizar()
            if obstaculo.colide(self.passaro):
                self.perder_vida(agora_ms)
                break
            if not obstaculo.passou and obstaculo.x+obstaculo.largura < self.passaro.x:
                obstaculo.passou = True
                self.pontos += 1
                self.tocar('ponto')
        self.obstaculos = [o for o in self.obstaculos if o.x+o.largura >= 0]
        if self.estado == 'JOGO' and (self.passaro.y < 30 or
                                     self.passaro.retangulo().bottom >= self.chao.y):
            self.perder_vida(agora_ms)
        # O banner some depois de 2,5 s; em seguida o ciclo decide
        # se chegou a hora de uma fase especial, da fase dos pássaros ou do próximo nível.
        self.banner_tempo = max(0.0, self.banner_tempo - dt)
        self.verificar_gatilhos()

    def texto(self, mensagem, x, y, cor=(255,255,255), grande=False, centro=False):
        """Renderiza texto; centro=True centraliza horizontalmente em x."""
        fonte = self.fonte_grande if grande else self.fonte
        img = fonte.render(str(mensagem),True,cor)
        self.tela.blit(img, (x-img.get_width()//2 if centro else x,y))

    def texto_destaque(self, mensagem, x, y, cor, fonte, escala=1.0, fundo=False):
        """Texto com sombra, centralizado em (x, y) (y = CENTRO do texto,
        diferente de texto(), em que y é o topo). escala != 1 faz o efeito
        "pulsar" do banner, usando rotozoom (rotação 0°, só ampliação)."""
        img = fonte.render(str(mensagem), True, cor)
        sombra = fonte.render(str(mensagem), True, (0, 0, 0))
        if escala != 1.0:
            img = pygame.transform.rotozoom(img, 0, escala)
            sombra = pygame.transform.rotozoom(sombra, 0, escala)
        ret = img.get_rect(center=(x, y))
        if fundo:   # tarja escura translúcida: melhora a leitura sobre cenários "poluídos"
            tarja = pygame.Surface((ret.width + 24, ret.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(tarja, (0, 0, 0, 160), tarja.get_rect(), border_radius=8)
            self.tela.blit(tarja, tarja.get_rect(center=ret.center))
        self.tela.blit(sombra, ret.move(4, 4))
        self.tela.blit(img, ret)

    def desenhar_listras(self, y, altura, deslocamento):
        """Faixa de listras amarelas e pretas (sinalização de perigo).
        'deslocamento' faz as listras correrem para o lado."""
        pygame.draw.rect(self.tela, (20, 20, 20), (0, y, LARGURA, altura))
        passo = 44
        inicio = -passo + int(deslocamento) % passo
        for x in range(inicio, LARGURA + passo, passo):
            pygame.draw.polygon(self.tela, (255, 205, 30),
                                [(x, y), (x + 22, y), (x + 22 - altura, y + altura),
                                 (x - altura, y + altura)])

    def desenhar_alerta(self):
        """Camada do estado ALERTA, desenhada sobre a cena congelada:
        escurecimento, faixa de perigo, banner "FASE ESPECIAL!" que pisca e
        pulsa, nome da fase, dica e contagem regressiva de 5 s."""
        t = self.alerta_decorrido
        nome, dica, cor_nome = NOMES_FASES[self.variante_alerta]
        # 1) Escurece a cena para destacar o aviso.
        camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        camada.fill((0, 0, 0, 150))
        self.tela.blit(camada, (0, 0))
        # 2) Faixa central vermelha translúcida, com listras de perigo.
        faixa = pygame.Surface((LARGURA, 150), pygame.SRCALPHA)
        faixa.fill((150, 0, 0, 205))
        self.tela.blit(faixa, (0, 175))
        self.desenhar_listras(165, 14, t*60)
        self.desenhar_listras(325, 14, -t*60)
        # 3) Título: alterna amarelo/vermelho 4x por segundo e pulsa em 10 rad/s.
        cor = (255, 230, 60) if int(t*4) % 2 == 0 else (255, 255, 255)
        self.texto_destaque('NOVA FASE!' if self.variante_alerta == 'PASSAROS' else 'FASE ESPECIAL!', LARGURA//2, 230, cor,
                            self.fonte_banner, 1 + 0.06*math.sin(t*10))
        self.texto_destaque(nome, LARGURA//2, 290, cor_nome, self.fonte_grande)
        self.texto_destaque(dica, LARGURA//2, 372, (255, 255, 255), self.fonte)
        # 4) Contagem regressiva: o número "bate" no início de cada segundo.
        restante = max(0.0, self.alerta_restante)
        numero = max(1, math.ceil(restante))
        fracao = restante - math.floor(restante)          # 1 -> 0 dentro de cada segundo
        self.texto_destaque('A FASE COMEÇA EM', LARGURA//2, 440, (255, 255, 255), self.fonte)
        self.texto_destaque(numero, LARGURA//2, 545, (255, 225, 90),
                            self.fonte_contagem, 1 + 0.35*fracao**3)
        # 5) Barra de progresso dos 5 s.
        barra = pygame.Rect(0, 0, 360, 18)
        barra.center = (LARGURA//2, 680)
        pygame.draw.rect(self.tela, (50, 50, 50), barra, border_radius=9)
        cheio = barra.copy()
        cheio.width = int(barra.width*restante/TEMPO_ALERTA)
        if cheio.width > 0:
            pygame.draw.rect(self.tela, (255, 205, 30), cheio, border_radius=9)
        pygame.draw.rect(self.tela, (255, 255, 255), barra, 2, border_radius=9)

    # Renderiza a pontuação com imagens PNG em vez de caracteres de uma fonte.
    # O argumento centralizar controla se x representa o centro ou a borda esquerda.
    def numero(self, valor, x, y, fator=1.0, centralizar=False):
        """Desenha pontuação com sprites PNG; fator=0.5 reduz à metade."""
        """Desenha os algarismos; x indica o centro quando centralizar=True."""
        # Primeiro preparamos todos os dígitos, inclusive a escala desejada.
        # Isso permite conhecer a largura total antes de desenhar qualquer sprite.
        sprites = []
        for digito in str(max(0, valor)):
            sprite = self.recursos.numeros[digito]
            if fator != 1:
                sprite = pygame.transform.smoothscale(
                    sprite, (max(1, int(sprite.get_width() * fator)),
                             max(1, int(sprite.get_height() * fator))))
            sprites.append(sprite)

        # A largura depende da quantidade e do tamanho dos algarismos.
        largura_total = sum(sprite.get_width() for sprite in sprites)
        if centralizar:
            # A posição inicial fica metade da largura à esquerda do centro.
            # O resultado permanece centralizado para 1, 2 ou mais dígitos.
            x -= largura_total // 2
        for sprite in sprites:
            self.tela.blit(sprite, (x, y))
            x += sprite.get_width()

    def medalha(self):
        """Retorna a maior medalha atingida ou None se não houver.

        Ajuste os limiares abaixo para testar a dificuldade da premiação.
        A ordem importa: primeiro ouro, depois prata e bronze.
        """
        if self.pontos >= 150: return 'ouro'
        if self.pontos >= 100: return 'prata'
        if self.pontos >= 50: return 'bronze'
        return None

    def desenhar_placar(self, com_medalha=True, com_nivel=False):
        """Placar do Flappy (pontos, vidas e medalha), reaproveitado
        pelos estados JOGO, ALERTA, GALAGA e DONKEY.

        As vidas podem passar de 6 (fase especial
        concluída = +1 vida): até MAX_ICONES_VIDA aparecem como ícones; acima
        disso, um ícone com o contador "xN".
        com_nivel=True mostra o nível de dificuldade do modo clássico.
        """
        self.numero(self.pontos,20,45)
        vida_sprite = self.recursos.passaros[self.passaro.familia][0]
        mini = pygame.transform.scale(vida_sprite,(26,20))
        if self.vidas <= MAX_ICONES_VIDA:
            for i in range(self.vidas):
                self.tela.blit(mini,(LARGURA-35-i*30,50))
        else:
            self.tela.blit(mini,(LARGURA-35,50))
            contador = self.fonte.render(f'x{self.vidas}',True,(255,255,255))
            self.tela.blit(contador,(LARGURA-35-6-contador.get_width(),49))
        if com_nivel:
            # Nível do ciclo (1 a 10) e o que falta para a próxima fase.
            rotulo = self.fonte.render(f'NÍVEL {self.nivel}/{NIVEL_MAXIMO}',
                                       True,(255,225,90))
            self.tela.blit(rotulo,(LARGURA-12-rotulo.get_width(),78))
            progresso = self.fonte_tabela.render(self.texto_progresso(),True,(230,230,240))
            self.tela.blit(progresso,(LARGURA-12-progresso.get_width(),100))
        if com_medalha:
            medalha = self.medalha()
            if medalha:
                self.tela.blit(self.recursos.medalhas[medalha],(15,120))

    def desenhar_mensagem_fase(self, mensagem):
        """Mensagem grande no meio da tela durante uma fase especial.
        Um '\n' separa linhas: a 1ª é dourada e as demais (ex.: "+1 VIDA") verdes."""
        for i, linha in enumerate(mensagem.split('\n')):
            cor = (255,225,90) if i == 0 else (130,255,140)
            self.texto_destaque(linha, LARGURA//2, 400 + 58*i, cor, self.fonte_grande)

    def desenhar_vitoria(self):
        """Tela de HONRA MÁXIMA: fundo escuro com raios dourados
        girando, troféu desenhado com formas, fogos de artifício, a mensagem de
        parabéns e a tabela do ranking (a linha do jogador fica destacada)."""
        t = self.clock.now() - self.fim_iniciado
        self.tela.fill((20, 12, 44))
        cx, cy = LARGURA//2, 205
        for k in range(18):                        # raios giratórios (um "sol" atrás do troféu)
            ang = t*0.4 + k*(2*math.pi/18)
            ponta1 = (cx + 760*math.cos(ang), cy + 760*math.sin(ang))
            ponta2 = (cx + 760*math.cos(ang + 0.10), cy + 760*math.sin(ang + 0.10))
            pygame.draw.polygon(self.tela, (66, 44, 14), [(cx, cy), ponta1, ponta2])
        pygame.draw.circle(self.tela, (110, 76, 18), (cx, cy), 150)
        pygame.draw.circle(self.tela, (190, 140, 36), (cx, cy), 112)
        # Troféu dourado: alças, taça, haste e base.
        ouro, ouro_esc = (255, 208, 48), (168, 118, 18)
        for lado in (-1, 1):
            pygame.draw.ellipse(self.tela, ouro_esc, (cx + lado*74 - 24, cy - 66, 48, 56), 8)
        taca = [(cx-62, cy-72), (cx+62, cy-72), (cx+46, cy-6), (cx+18, cy+24), (cx-18, cy+24), (cx-46, cy-6)]
        pygame.draw.polygon(self.tela, ouro, taca)
        pygame.draw.polygon(self.tela, ouro_esc, taca, 4)
        pygame.draw.rect(self.tela, ouro, (cx-10, cy+24, 20, 34))
        pygame.draw.rect(self.tela, ouro_esc, (cx-46, cy+58, 92, 16), border_radius=4)
        pygame.draw.rect(self.tela, ouro, (cx-60, cy+74, 120, 14), border_radius=4)
        estrela = []                               # estrela de 5 pontas no centro da taça
        for i in range(10):
            raio = 24 if i % 2 == 0 else 10
            a = -math.pi/2 + i*math.pi/5
            estrela.append((cx + raio*math.cos(a), cy - 34 + raio*math.sin(a)))
        pygame.draw.polygon(self.tela, (255, 250, 220), estrela)
        for x, y, vx, vy, vida, cor in self.fogos:   # fogos de artifício
            pygame.draw.circle(self.tela, cor, (int(x), int(y)), max(1, int(3*min(1.0, vida))))
        pulso = 1.0 + 0.05*math.sin(t*5)
        self.texto_destaque('HONRA MÁXIMA!', LARGURA//2, 345, (255, 215, 0), self.fonte_banner, pulso)
        self.texto_destaque('VOCÊ ZEROU O JOGO!', LARGURA//2, 405, (255, 255, 255), self.fonte_grande)
        self.texto_destaque(f'Parabéns, {self.jogador or "jogador"}!', LARGURA//2, 455,
                            (130, 255, 140), self.fonte_grande)
        self.texto(f'{self.pontos} pontos  -  {NIVEL_MAXIMO} níveis concluídos',
                   LARGURA//2, 495, (255, 225, 90), centro=True)
        if self.modo_teste_usado:
            self.texto('Modo teste: partida fora do ranking', LARGURA//2, 522,
                       (255, 140, 140), centro=True)
        self.desenhar_ranking()

    def desenhar_cadastro(self):
        """Tela de identificação, mostrada antes de cada partida."""
        self.chao.desenhar(self.tela)
        cartao = pygame.Surface((LARGURA-60,360),pygame.SRCALPHA)
        pygame.draw.rect(cartao,(10,14,30,220),cartao.get_rect(),border_radius=18)
        pygame.draw.rect(cartao,(255,205,30,255),cartao.get_rect(),3,border_radius=18)
        self.tela.blit(cartao,(30,230))
        self.texto_destaque('QUEM VAI JOGAR?',LARGURA//2,285,(255,225,90),self.fonte_grande)
        self.texto('Digite seu nome para entrar no ranking:',LARGURA//2,335,
                   (255,255,255),centro=True)
        campo = pygame.Rect(0,0,LARGURA-120,66)
        campo.center = (LARGURA//2,415)
        pygame.draw.rect(self.tela,(245,245,245),campo,border_radius=10)
        pygame.draw.rect(self.tela,(255,205,30),campo,3,border_radius=10)
        cursor = '_' if int(self.clock.now()*2) % 2 == 0 else ' '
        texto = self.nome_digitado + cursor
        img = self.fonte_grande.render(texto,True,(30,30,40))
        if img.get_width() > campo.width-28:    # nome muito largo (ex.: WWWW...): fonte menor
            img = self.fonte.render(texto,True,(30,30,40))
        self.tela.blit(img,img.get_rect(midleft=(campo.x+14,campo.centery)))
        if self.clock.now() < self.erro_nome_ate:
            self.texto('Digite pelo menos um caractere!',LARGURA//2,470,
                       (255,90,90),centro=True)
        else:
            self.texto(f'Até {MAX_NOME} caracteres. Fica salvo no ranking.',
                       LARGURA//2,470,(200,200,200),centro=True)
        self.texto('ENTER: começar    DEL: limpar    ESC: voltar',LARGURA//2,520,
                   (255,225,90),centro=True)

    def desenhar_ranking(self):
        """Tabela Top 10 (posição, jogador e pontos).

        A linha da partida que acabou de terminar fica destacada. Posições
        ainda vazias aparecem com "---". Para mover a tabela, mude
        Y_TABELA_RANKING.
        """
        x0, y0 = 20, Y_TABELA_RANKING
        largura, altura = LARGURA-40, ALTURA-Y_TABELA_RANKING-12
        cartao = pygame.Surface((largura,altura),pygame.SRCALPHA)
        pygame.draw.rect(cartao,(10,14,30,225),cartao.get_rect(),border_radius=14)
        pygame.draw.rect(cartao,(255,205,30,255),cartao.get_rect(),2,border_radius=14)
        self.tela.blit(cartao,(x0,y0))
        titulo = self.fonte_titulo_tabela.render('TOP 10 - MELHORES RECORDES',True,(255,215,0))
        self.tela.blit(titulo,titulo.get_rect(midtop=(LARGURA//2,y0+8)))
        # Colunas: posição e nome alinhados à esquerda; pontos, à direita.
        colunas = (x0+22, x0+75, x0+largura-130, x0+largura-24)   # coluna do nível
        direita = (False, False, True, True)
        cinza = (150,155,170)
        y = y0 + 38
        for texto, x, alinha_direita in zip(('#','JOGADOR','NÍVEL','PONTOS'), colunas, direita):
            img = self.fonte_tabela.render(texto,True,cinza)
            self.tela.blit(img,(x-img.get_width() if alinha_direita else x,y))
        pygame.draw.line(self.tela,cinza,(x0+14,y+19),(x0+largura-14,y+19),1)
        y += 24
        podio = {1:(255,215,0), 2:(210,214,224), 3:(214,140,70)}
        for i in range(TOP_RANKING):
            posicao = i + 1
            linha_y = y + i*20
            registro = self.ranking[i] if i < len(self.ranking) else None
            if registro:
                cor = podio.get(posicao,(255,255,255))
                # Nível alcançado ("ZEROU" para quem concluiu o nível 10).
                nivel = ('ZEROU' if registro.get('zerou')
                         else (str(registro['nivel']) if registro.get('nivel') else '-'))
                campos = (str(posicao), registro['nome'], nivel, str(registro['pontos']))
                if posicao == self.posicao_final:       # destaca a partida atual
                    faixa = pygame.Surface((largura-16,20),pygame.SRCALPHA)
                    faixa.fill((255,225,90,80))
                    self.tela.blit(faixa,(x0+8,linha_y-2))
                    cor = (255,245,160)
            else:
                cor, campos = (95,100,115), (str(posicao),'---','','-')
            for texto, x, alinha_direita in zip(campos, colunas, direita):
                img = self.fonte_tabela.render(texto,True,cor)
                self.tela.blit(img,(x-img.get_width() if alinha_direita else x,linha_y))
        rodape = self.fonte_tabela.render('ESPACO ou clique para reiniciar',True,(220,220,220))
        self.tela.blit(rodape,rodape.get_rect(midbottom=(LARGURA//2,y0+altura-8)))

    def rotulo_tema(self):
        return 'Tema: '+self.tema

    def desenhar_fundo(self):
        """Fundo do quadro (as sessões com cenários comprados trocam só isto)."""
        fundo = self.recursos.fundos[self.tema if self.estado!='MENU' else 'bg']
        self.tela.blit(pygame.transform.scale(fundo,(LARGURA,ALTURA)),(0,0))

    def desenhar(self):
        """Desenha o estado atual e apresenta o quadro na janela."""
        # Todas as posições abaixo usam a superfície lógica de 575 x 860.
        # Só ao final redimensionamos a imagem para a janela do usuário.
        self.desenhar_fundo()
        if self.estado == 'MENU':
            self.chao.desenhar(self.tela)
            logo = self.recursos.logo
            self.tela.blit(logo,logo.get_rect(center=(LARGURA//2,300)))
            oscilacao = int(12*math.sin(self.clock.now()*3))
            sprite = self.recursos.passaros['dia'][1]
            self.tela.blit(sprite,sprite.get_rect(center=(LARGURA//2,408+oscilacao)))
            self.texto(f'RECORDE: {self.recorde} - {self.nome_recorde}',
                       LARGURA//2,170,centro=True)
            self.texto('ESPACO ou clique para iniciar',LARGURA//2,650,centro=True)
        elif self.estado == 'JOGO':
            for obstaculo in self.obstaculos:
                obstaculo.desenhar(self.tela)
            self.chao.desenhar(self.tela)
            self.passaro.desenhar(self.tela)
            self.desenhar_placar(com_nivel=True)   # mostra nível e progresso do ciclo
            if self.especial:
                # Fase dos pássaros (do ciclo): vale pontos normalmente, diferente
                # das fases especiais-bônus (Galaga e Donkey Kong).
                self.texto('FASE DOS PÁSSAROS!',LARGURA//2,95,(255,220,90),centro=True)
            if self.banner_tempo > 0:
                # Banner de 2,5 s (subida de nível / início da fase dos pássaros), pulsando.
                titulo, subtitulo, cor = self.banner
                pulso = 1.0 + 0.06*math.sin(self.banner_tempo*12)
                fonte = self.fonte_banner if len(titulo) <= 11 else self.fonte_grande
                self.texto_destaque(titulo,LARGURA//2,165,cor,fonte,pulso)
                if subtitulo:
                    self.texto_destaque(subtitulo,LARGURA//2,215,(255,255,255),self.fonte)
        elif self.estado == 'ALERTA':
            # A cena do Flappy fica congelada (mesmo desenho do JOGO,
            # sem o texto da fase por tempo) e o aviso é desenhado por cima.
            for obstaculo in self.obstaculos:
                obstaculo.desenhar(self.tela)
            self.chao.desenhar(self.tela)
            self.passaro.desenhar(self.tela)
            self.desenhar_placar(com_nivel=True)
            self.desenhar_alerta()
        elif self.estado == 'DONKEY':
            # A própria FaseDonkey desenha cenário, Kong, obstáculos,
            # barris, bananas, chão e pássaro. Aqui entram placar e textos.
            d = self.donkey
            d.desenhar(self.tela, self.passaro)
            self.desenhar_placar(com_medalha=False)
            if d.mensagem:
                self.desenhar_mensagem_fase(d.mensagem)
            # O texto de status e a dica vêm da própria fase (mudam no chefão).
            self.texto_destaque(d.texto_status, LARGURA//2, ALTURA-30, (255,255,255),
                                self.fonte, fundo=True)
            if d.dica:
                self.texto_destaque(d.dica, LARGURA//2, ALTURA-68, (220,220,220),
                                    self.fonte, fundo=True)
        elif self.estado == 'GALAGA':
            # A própria FaseGalaga desenha o cenário espacial (fundo,
            # inimigos, tiros, nave). Aqui entram o placar e os textos.
            g = self.galaga
            g.desenhar(self.tela)
            # A medalha fica de fora para não cobrir a primeira coluna.
            self.desenhar_placar(com_medalha=False)
            if g.mensagem:
                self.desenhar_mensagem_fase(g.mensagem)
            # O texto de status e a dica vêm da própria fase (mudam no chefão).
            self.texto(g.texto_status,LARGURA//2,ALTURA-35,centro=True)
            if g.dica:
                self.texto(g.dica,LARGURA//2,ALTURA-65,(200,200,200),centro=True)
        elif self.estado == 'VITORIA':
            # Tela de Honra Máxima (nível 10 concluído).
            self.desenhar_vitoria()
        elif self.estado == 'CADASTRO':
            # Tela para digitar o nome do jogador.
            self.desenhar_cadastro()
        else:  # GAMEOVER
            # Nesta tela, os elementos são posicionados em camadas:
            # chão, identificação do recordista, logotipo, moldura e placar.
            self.chao.desenhar(self.tela)
            # Cabeçalho: jogador cadastrado, pontuação e a
            # posição desta partida no ranking (o registro foi gravado em finalizar()).
            if self.posicao_final == 1:
                titulo_recorde = f'NOVO RECORDE, {self.jogador}!'
            else:
                titulo_recorde = f'JOGADOR: {self.jogador or "Anônimo"}'
            if self.posicao_final:
                detalhe_recorde = f'{self.pontos} pontos - {self.posicao_final}º lugar no ranking'
            elif self.modo_teste_usado:
                detalhe_recorde = f'{self.pontos} pontos - modo teste (fora do ranking)'
            else:
                detalhe_recorde = f'{self.pontos} pontos - não entrou no ranking'
            # O parâmetro centro=True alinha o texto no eixo médio da tela.
            # Coordenadas verticais escolhidas para ficar acima de GAME OVER.
            self.texto(titulo_recorde, LARGURA // 2, 105,
                       (255, 215, 0), centro=True)
            self.texto(detalhe_recorde, LARGURA // 2, 135,
                       (255, 255, 255), centro=True)
            # Pisca a cada 0,5 s durante os primeiros 10 s.
            decorrido = self.clock.now()-self.fim_iniciado
            if decorrido >= 10 or int(decorrido*2)%2 == 0:
                img = self.recursos.gameover
                self.tela.blit(img,img.get_rect(center=(LARGURA//2,245)))
            # A moldura deve ser desenhada antes dos títulos e dos números,
            # caso contrário cobriria o conteúdo do placar.
            moldura = self.recursos.moldura
            self.tela.blit(moldura,moldura.get_rect(center=(LARGURA//2,450)))
            # Posicionamento do placar conforme as coordenadas escolhidas.
            # Os textos usam x=270 como ponto inicial (não centralizado).
            # Os algarismos começam em x=380 e usam metade do tamanho original.
            # PONTOS: texto (270, 375); valor (380, 410).
            # RECORDE: texto (270, 460); valor (380, 490).
            self.texto('PONTOS', 270, 375)
            self.numero(self.pontos, 380, 410, 0.5)
            self.texto('RECORDE', 270, 460)
            # Durante a digitação, a tela já mostra a pontuação candidata
            # ao novo recorde; a gravação efetiva ocorre apenas com Enter.
            self.numero(max(self.recorde, self.pontos), 380, 490, 0.5)
            # A medalha é posicionada dentro da moldura do GAME OVER.
            # Valores aprovados para esta tela: x=106, y=420.
            medalha = self.medalha()
            if medalha:
                self.tela.blit(self.recursos.medalhas[medalha], (106, 420))
            # O nome é informado no CADASTRO; aqui aparece a tabela com os
            # 10 melhores recordes (e o aviso de reiniciar).
            self.desenhar_ranking()
        # A camada de pausa vale para todos os estados ativos
        # (JOGO, ALERTA, GALAGA e DONKEY).
        if self.pausado and self.estado in ESTADOS_ATIVOS:
            camada = pygame.Surface((LARGURA,ALTURA),pygame.SRCALPHA)
            camada.fill((0,0,0,155))
            self.tela.blit(camada,(0,0))
            # No ALERTA o banner ocupa o meio da tela; o aviso desce para não sobrepor.
            y_pausa = 740 if self.estado == 'ALERTA' else 360
            self.texto('PAUSADO',LARGURA//2,y_pausa,grande=True,centro=True)
            self.texto('Pressione P para continuar',LARGURA//2,y_pausa+60,centro=True)
        # A barra superior pertence a todos os estados do jogo; por isso,
        # está fora do if/elif/else de MENU, JOGO, GALAGA e GAMEOVER.
        pygame.draw.rect(self.tela,(45,50,60),(0,0,LARGURA,30))
        self.texto('S: Som '+('ON' if self.som_ativo else 'OFF'),8,5)
        if self.estado == 'CADASTRO':
            dica = 'ENTER: OK | ESC: Voltar'     # alinhada à direita (é mais larga que a padrão)
            self.texto(dica,LARGURA-8-self.fonte.size(dica)[0],5)
        else:
            self.texto(self.TEXTO_ATALHOS,LARGURA-220,5)
        # Rótulo da barra: agora também informa a fase Galaga.
        if self.estado == 'GALAGA':
            rotulo = 'FASE GALAGA'
        elif self.estado == 'DONKEY':
            rotulo = 'FASE DONKEY'          # curto para não invadir o texto de pausa
        elif self.estado == 'ALERTA':
            rotulo = 'PREPARE-SE!'          #
        elif self.estado == 'VITORIA':
            rotulo = 'HONRA MÁXIMA'         #
        elif self.estado == 'CADASTRO':
            rotulo = 'CADASTRO'             #
        elif self.especial:
            rotulo = 'FASE PÁSSAROS'        # veja o texto "FASE DOS PÁSSAROS!"
        else:
            rotulo = self.rotulo_tema()
        self.texto(rotulo,165,5,(255,225,90))
        if self.modo_teste_usado:
            self.texto('[TESTE]',LARGURA//2,34,(255,110,110),centro=True)   # partida de teste

    def tratar_evento(self, evento):
        """Processa teclado e mouse.

        As posições do mouse já chegam em coordenadas lógicas (575x860): a
        conversão da janela real é feita pela App. Retorna False para sair.
        """
        # Na Galaga, o mouse também move a nave (posição horizontal).
        if (evento.type == pygame.MOUSEMOTION and self.estado == 'GALAGA'
                and self.galaga):
            self.galaga.alvo_x = evento.pos[0]
        if evento.type == pygame.KEYDOWN:
            # A digitação do nome vem ANTES de qualquer atalho
            # (S, P, G, K, T...), senão as letras do nome acionariam comandos.
            if self.estado == 'CADASTRO':
                return self.tratar_tecla_cadastro(evento)
            if evento.key == pygame.K_ESCAPE:
                return False
            if evento.key == pygame.K_s:
                self.audio.toggle_mute()
            # A pausa vale em todos os estados ativos (inclui ALERTA e DONKEY).
            if evento.key == pygame.K_p and self.estado in ESTADOS_ATIVOS:
                self.pausado = not self.pausado
            # Atalhos de teste/cheat (só com MODO_TESTE = True). Este
            # trecho só é alcançado FORA do cadastro: lá, tratar_tecla_cadastro()
            # consome a tecla antes, por isso dá para digitar números no nome sem
            # mudar a dificuldade. Os atalhos de fase passam pelo ALERTA de 5 s, como
            # no jogo real, e NÃO alteram o cronograma de pontuação.
            # (no Modo Apresentação, systems/apresentacao.py, também valem)
            if (MODO_TESTE or apresentacao.ligado()) and self.estado in ESTADOS_ATIVOS and not self.pausado:
                self.tratar_atalho_teste(evento.key)
            # X lança o Banana-rang. Esta linha só é alcançada FORA do cadastro (o
            # return lá em cima trata a digitação do nome), então digitar "x" no nome é seguro.
            if (evento.key == pygame.K_x and self.estado == 'DONKEY' and self.donkey
                    and not self.pausado):
                self.donkey.lancar_bumerangue(self.passaro)
            # O espaço é tratado uma única vez (em dobro, bateria asas duas
            # vezes e pularia o menu no GAME OVER).
            if evento.key == pygame.K_SPACE:
                self.acao_principal()
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (1,3):
            # Clique na barra superior não é comando de pulo.
            y_logico = evento.pos[1]
            if y_logico > 30 and self.estado != 'CADASTRO':
                self.acao_principal()
        return True

    def tratar_atalho_teste(self, tecla):
        """Atalhos de teste (só com MODO_TESTE = True, fora do cadastro):
          1..9 e 0 -> pula para o nível 1..9 e 10     G / K / F -> alerta + Galaga / Donkey / pássaros
          T -> pontuação 1 ponto antes do próximo gatilho     V -> tela de HONRA MÁXIMA
          B -> (Galaga/Donkey) vai direto ao chefão    C -> (Galaga/Donkey) solta uma cápsula de bônus
        Qualquer atalho marca a partida como TESTE: ela não entra no ranking (a marca é
        posta ANTES da ação, porque a tecla V já registra a partida)."""
        if (tecla in TECLAS_NIVEL
                or (self.estado == 'JOGO' and tecla in (pygame.K_g, pygame.K_k, pygame.K_f,
                                                        pygame.K_t, pygame.K_v))
                or (self.estado in ('GALAGA', 'DONKEY') and tecla in (pygame.K_b, pygame.K_c))):
            self.modo_teste_usado = True
        if tecla in TECLAS_NIVEL:                    # 1 a 9 e 0 (= nível 10)
            self.ir_para_nivel(TECLAS_NIVEL[tecla])
        elif self.estado == 'JOGO':
            if tecla == pygame.K_g:
                self.iniciar_alerta('GALAGA')        # G: alerta + fase Galaga
            elif tecla == pygame.K_k:
                self.iniciar_alerta('DONKEY')        # K: alerta + fase Donkey Kong
            elif tecla == pygame.K_f:
                self.iniciar_alerta('PASSAROS')      # F: alerta + fase dos pássaros
            elif tecla == pygame.K_t:
                # T: deixa a pontuação 1 ponto abaixo do próximo gatilho; o
                # próximo ponto dispara o evento de verdade.
                self.pontos = max(self.pontos, self.alvo_gatilho() - 1)
            elif tecla == pygame.K_v:
                self.vitoria_final()                 # V: tela de HONRA MÁXIMA
        elif tecla == pygame.K_b and self.estado in ('GALAGA', 'DONKEY'):
            self.pular_para_chefe()                  # B: pula direto para o chefão
        elif tecla == pygame.K_c and self.estado in ('GALAGA', 'DONKEY'):
            fase = self.galaga if self.estado == 'GALAGA' else self.donkey
            if fase:
                fase.soltar_capsula_teste()          # C: solta uma cápsula de bônus

    def acao_principal(self):
        """Interpreta espaço/clique de acordo com o estado do jogo."""
        # Do menu vai para o CADASTRO; a partida só
        # começa depois que o jogador confirma o nome (ENTER).
        if self.estado == 'MENU': self.iniciar_cadastro()
        elif self.estado == 'JOGO' and not self.pausado:
            self.passaro.pular()
            self.tocar('pulo')
        # Na Galaga, o mesmo comando vira "atirar".
        elif self.estado == 'GALAGA' and not self.pausado:
            self.galaga.atirar()
        # Na fase Donkey, volta a ser "bater asas" (física do Flappy).
        # No ALERTA nenhum comando de jogo age: a cena está congelada.
        elif self.estado == 'DONKEY' and not self.pausado and not self.donkey.resultado:
            self.passaro.pular()
            self.tocar('pulo')
        # Ignora espaço/clique no primeiro segundo do GAME OVER: quem
        # morre apertando sem parar não "pula" a tabela do ranking sem ver.
        # A tela de HONRA MÁXIMA também reinicia (esperando 2,5 s, para a
        # comemoração e o ranking aparecerem).
        elif (self.estado in ('GAMEOVER', 'VITORIA')
              and self.clock.now() - self.fim_iniciado > (2.5 if self.estado == 'VITORIA' else 1.0)):
            self.reiniciar()

    def pos_atualizar(self):
        """Repete o jingle de arcade no GAME OVER (até 3 vezes, a cada 2 s).

        Chamado pela GameScene logo após atualizar(), na mesma ordem do loop
        original.
        """
        if self.estado == 'GAMEOVER' and self.contador_arcade < 3:
            agora = self.clock.now()
            if agora-self.fim_iniciado >= 3.5 and (self.ultimo_arcade == 0 or
                                                     agora-self.ultimo_arcade >= 2):
                self.tocar('arcade')
                self.ultimo_arcade = agora
                self.contador_arcade += 1
