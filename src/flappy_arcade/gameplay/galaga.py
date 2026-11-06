"""Fase especial Galaga: nave, formação de inimigos, mergulhos e o Boss Galaga."""
import math
import random

import pygame

from ..config.constants import (
    ALTURA,
    BOMBA_DANO_CHEFE,
    BOMBA_INVULNERAVEL,
    BONUS_ABATES_POR_CAPSULA,
    BONUS_MAX_TIROS,
    BONUS_SUPERAQUECIMENTO,
    COLUNAS_GALAGA,
    DESLOC_GEMEO,
    ESPACO_COL,
    ESPACO_LIN,
    INTERVALO_TIRO,
    LARGURA,
    MAX_TIROS_JOGADOR,
    PASSAROS_ESPECIAIS,
    TEMPO_CHEFE_GALAGA,
    TEMPO_INVULNERAVEL_MS,
    TIPOS_BONUS,
    TURBO_CADENCIA,
    TURBO_VEL_NAVE,
    VELOCIDADE_NAVE,
    VELOCIDADE_TIRO,
    VIDAS_POR_FASE_ESPECIAL,
    Y_FORMACAO,
    Y_NAVE,
)
from .difficulty import parametros_galaga
from .effects import Explosao
from .geometry import bezier
from .hud import desenhar_hud_bonus, texto_vidas_extras
from .powerups import CapsulaBonus, EfeitosAtivos


# A fase Galaga é um "mini-jogo" dentro do jogo. A classe FaseGalaga
# cuida de tudo que é interno a ela (nave, inimigos, tiros, colisões).
# A ClassicSession só decide QUANDO ela começa/termina e como o resultado
# (pontos, vidas, sons) afeta a partida principal.

class Tiro:
    """Projétil do jogador (sobe) ou de um inimigo (desce)."""
    def __init__(self, x, y, vx, vy, do_jogador):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy          # velocidades em px/s
        self.do_jogador = do_jogador
        self.largura, self.altura = (6, 18) if do_jogador else (10, 10)

    def atualizar(self, dt):
        # Movimento uniforme: posição += velocidade × tempo.
        self.x += self.vx*dt
        self.y += self.vy*dt

    def retangulo(self):
        return pygame.Rect(int(self.x - self.largura/2),
                           int(self.y - self.altura/2),
                           self.largura, self.altura)

    def fora_da_tela(self):
        return (self.y < 30 or self.y > ALTURA
                or self.x < -20 or self.x > LARGURA+20)

    def desenhar(self, tela):
        if self.do_jogador:
            pygame.draw.rect(tela, (255, 240, 120), self.retangulo(),
                             border_radius=3)
        else:
            pygame.draw.circle(tela, (255, 90, 60),
                               self.retangulo().center, 5)

class Inimigo:
    """Pássaro especial com um pequeno "ciclo de vida" (máquina de estados):

    ESPERA    -> aguarda o atraso para entrar na tela
    ENTRADA   -> voa em curva até a sua posição (slot) na formação
    FORMACAO  -> fica no slot, balançando junto com a formação
    MERGULHO  -> ataca em curva na direção do jogador
    RETORNO   -> reaparece no topo e desce até o slot
    """
    def __init__(self, sprite, col, linha, atraso, vida):
        self.sprite = sprite
        self.col, self.linha = col, linha
        self.vida = vida            # linha 0 ("chefes") resiste a 2 tiros
        self.estado = 'ESPERA'
        self.atraso = atraso
        self.t, self.duracao = 0.0, 1.5   # progresso da curva (t de 0 a 1)
        self.x, self.y = -100.0, -100.0
        self.p0 = self.p1 = self.p2 = (0.0, 0.0)  # pontos da curva
        self.piscar = 0.0           # tempo restante do "pisca" após levar tiro
        self.persegue = 0.0         # quanto o mergulho acompanha a nave
        self.furioso = False        # fúria: desenha o anel vermelho

    def comecar_entrada(self):
        """Define uma curva que nasce num canto superior e passa pelo meio."""
        canto = random.choice((-50, LARGURA+50))
        self.p0 = (canto, -50)
        self.p1 = (random.randint(100, LARGURA-100), ALTURA*0.55)
        self.estado, self.t, self.duracao = 'ENTRADA', 0.0, 1.5

    def mergulhar(self, alvo_x, duracao, atraso=0.0, persegue=0.0, lado=None):
        """Ataque: sai de lado, faz a curva e fecha sobre a posição da nave.

        atraso: espera (s) antes de partir, para escalonar os
        pássaros de um esquadrão. persegue (0 a 1): quanto maior, mais o ponto
        de chegada acompanha a nave durante o mergulho. lado (-1 ou 1): lado de
        saída; o esquadrão inteiro usa o mesmo.
        """
        self.p0 = (self.x, self.y)
        if lado is None:
            lado = random.choice((-1, 1))
        px = max(40, min(LARGURA-40, self.x + lado*random.randint(120, 240)))
        self.p1 = (px, self.y + 360)
        self.p2 = (max(30, min(LARGURA-30, alvo_x + random.randint(-70, 70))),
                   ALTURA + 60)
        self.persegue = persegue
        self.estado, self.duracao = 'MERGULHO', duracao
        self.t = -atraso/duracao    # t negativo = ainda esperando (curva parada em p0)

    def atualizar(self, dt, slot, alvo_x=None):
        """slot = (x, y) atual do inimigo na formação (que se move);
        alvo_x = posição da nave (usada na perseguição)."""
        self.piscar = max(0.0, self.piscar - dt)
        if self.estado == 'ESPERA':
            self.atraso -= dt
            if self.atraso <= 0:
                self.comecar_entrada()
            return
        if self.estado == 'FORMACAO':
            self.x, self.y = slot
            return
        self.t += dt/self.duracao
        u = max(0.0, min(1.0, self.t))
        if self.estado == 'ENTRADA':
            # O fim da curva é o slot atual, que balança; por isso é
            # recalculado a cada quadro.
            self.x, self.y = bezier(self.p0, self.p1, slot, u)
            if u >= 1.0:
                self.estado = 'FORMACAO'
        elif self.estado == 'MERGULHO':
            if self.persegue > 0 and alvo_x is not None and u < 0.85:
                # Perseguição: o ponto de chegada desliza na
                # direção da nave. Nos 15% finais ele para, dando chance de desviar.
                px = self.p2[0] + (alvo_x - self.p2[0])*min(1.0, self.persegue*2.5*dt)
                self.p2 = (max(30, min(LARGURA-30, px)), self.p2[1])
            self.x, self.y = bezier(self.p0, self.p1, self.p2, u)
            if u >= 1.0:
                # Saiu por baixo: volta a aparecer por cima do slot.
                self.estado, self.t, self.duracao = 'RETORNO', 0.0, 1.0
                self.persegue = 0.0
                self.x, self.y = slot[0], -50.0
        elif self.estado == 'RETORNO':
            self.x = slot[0]
            self.y = -50 + (slot[1]+50)*u
            if u >= 1.0:
                self.estado = 'FORMACAO'

    def retangulo(self):
        return self.sprite.get_rect(center=(int(self.x), int(self.y)))

    def hitbox(self):
        # Caixa de colisão um pouco menor que o sprite: mais justa.
        return self.retangulo().inflate(-8, -8)

    def desenhar(self, tela):
        if self.estado == 'ESPERA':
            return
        if self.piscar > 0 and int(self.piscar*20) % 2 == 0:
            return    # efeito de "pisca" ao levar um tiro sem morrer
        tela.blit(self.sprite, self.retangulo())
        if self.furioso:
            # Anel vermelho: este inimigo está em FÚRIA.
            pygame.draw.ellipse(tela, (255, 60, 40), self.retangulo().inflate(8, 8), 2)

class ChefeGalaga:
    """Chefão da Galaga, inspirado no "Boss Galaga" do jogo original (o
    inseto verde que captura a nave com o RAIO TRATOR).

    Ele desce do topo (invulnerável na entrada) e depois alterna ataques, sempre
    ANUNCIADOS antes de acontecer (difícil, mas justo):
      - LEQUE:   o chefão brilha por 0,4 s e solta uma rajada de tiros abertos;
      - MIRA:    3 tiros em sequência mirados na nave;
      - RAIO:    o chefão se alinha com a nave, trava, o raio pisca (aviso) e
                 depois liga: quem estiver dentro dele é capturado (perde vida);
      - ESPIRAL: dois fluxos de tiros varrendo a tela (só abaixo de 33% de vida);
      - ESCOLTA: convoca pássaros que mergulham (ao cruzar 66% e 33% de vida).
    Vida: 24 + 4 por nível (cada tiro tira 1). A dificuldade vem dos ATAQUES, não de
    uma vida enorme: eles ficam mais frequentes e rápidos conforme o nível e
    conforme a vida cai. (Mesmo um jogador perfeito precisa de ~45 s no nível 10.)
    """
    Y_ALVO = 205            # altura final (abaixo do placar e da barra de vida)

    def __init__(self, sprites, nivel, cfg):
        self.sprite, self.sprite_flash = sprites
        self.nivel = nivel
        self.cfg = cfg                        # parâmetros do nível (chaves 'chefe_*')
        self.hp_max = cfg['chefe_hp']
        self.hp = self.hp_max
        self.x, self.y = LARGURA/2, -130.0
        self.tempo = 0.0
        self.entrando = True
        self.flash = 0.0
        self.morte = 0.0                # > 0 enquanto explode (segundos decorridos)
        self.morto = False
        self.ataque = None              # 'LEQUE', 'MIRA', 'RAIO', 'ESPIRAL' ou None
        self.t_ataque = 0.0
        self.prox_ataque = 2.2
        self.ultimo = None
        self.disparou = False
        self.raio_estado = None         # None, 'AVISO' ou 'LIGADO'
        self.raio_travado = False       # o raio deixa de seguir a nave pouco antes de ligar
        self.cone = None                # superfície do raio ligado (criada ao ligar)
        self.mira_restante = 0
        self.cd_mira = 0.0
        self.cd_espiral = 0.0
        self.angulo_espiral = 0.0
        self.convocacoes = 0            # escoltas já convocadas (0, 1 ou 2)
        self.novos_tiros = []           # a FaseGalaga recolhe estes tiros a cada quadro
        self.novas_escoltas = 0
        self.vel_tiro = cfg['chefe_vel_tiro']
        self.fonte = pygame.font.Font(None, 22)

    # ---- estado ----
    @property
    def fase(self):
        """0 acima de 66% da vida, 1 acima de 33%, 2 abaixo disso."""
        fracao = self.hp/self.hp_max
        return 0 if fracao > 0.66 else (1 if fracao > 0.33 else 2)

    def retangulo(self):
        return self.sprite.get_rect(center=(int(self.x), int(self.y)))

    def hitbox(self):
        return self.retangulo().inflate(-34, -30)

    def meia_largura_raio(self, y):
        """Largura do raio (cone): 22 px na saída, cerca de 114 px no fundo da tela."""
        topo = self.y + 52
        fracao = max(0.0, min(1.0, (y - topo)/(ALTURA - topo)))
        return 22 + 92*fracao

    def nave_no_raio(self, nave_x, nave_y):
        return (self.raio_estado == 'LIGADO'
                and abs(nave_x - self.x) <= self.meia_largura_raio(nave_y))

    def encerrar_raio(self):
        """O raio capturou a nave: ele desliga e o ataque acaba."""
        self.raio_estado = None
        self.cone = None
        self._fim_ataque()

    def levar_tiro(self):
        """Um tiro do jogador acertou. Devolve True se causou dano."""
        if self.entrando or self.morte > 0:
            return False
        self.hp -= 1
        self.flash = 0.08
        if self.hp <= 0:
            self.hp = 0
            self.morte = 0.001                # começa a explodir
            self.ataque = None
            self.raio_estado = None
            self.cone = None
        return True

    # ---- ataques ----
    def _intervalo(self):
        return self.cfg['chefe_intervalo']*(0.75 if self.fase == 2 else 1.0)

    def _escolher_ataque(self):
        opcoes = ['LEQUE', 'MIRA']
        if self.fase >= 1:
            opcoes += ['RAIO', 'RAIO']
        if self.fase >= 2:
            opcoes += ['ESPIRAL']
        if self.ultimo in opcoes and len(opcoes) > 1:
            opcoes = [o for o in opcoes if o != self.ultimo]       # não repete o último
        return random.choice(opcoes)

    def _fim_ataque(self):
        self.ataque = None
        self.disparou = False
        self.prox_ataque = self._intervalo()

    def _tiro(self, ang, velocidade):
        """Tiro saindo do chefão; ang = 0 é reto para baixo (radianos)."""
        self.novos_tiros.append(Tiro(self.x, self.y + 50, velocidade*math.sin(ang),
                                     velocidade*math.cos(ang), False))

    def _ang_para_nave(self, nave_x):
        return math.atan2(nave_x - self.x, Y_NAVE - self.y)

    def _executar_ataque(self, dt, nave_x):
        self.t_ataque += dt
        v = self.vel_tiro
        if self.ataque == 'LEQUE':
            if not self.disparou and self.t_ataque >= 0.4:       # 0,4 s de carga (brilho)
                self.disparou = True
                k = self.cfg['chefe_leque']
                centro = self._ang_para_nave(nave_x)
                for i in range(k):
                    self._tiro(centro + (i - (k-1)/2)*0.20, v)
            if self.t_ataque >= 0.8:
                self._fim_ataque()
        elif self.ataque == 'MIRA':
            if self.t_ataque >= 0.35:
                self.cd_mira -= dt
                if self.cd_mira <= 0:
                    if self.mira_restante > 0:
                        self._tiro(self._ang_para_nave(nave_x), v + 70)
                        self.mira_restante -= 1
                        self.cd_mira = 0.24
                    else:
                        self._fim_ataque()
        elif self.ataque == 'RAIO':
            aviso = self.cfg['chefe_aviso_raio']
            if self.raio_estado == 'AVISO':
                if self.t_ataque >= aviso - 0.45:
                    self.raio_travado = True        # trava a posição: dá 0,45 s para sair de baixo
                if self.t_ataque >= aviso:
                    self.raio_estado = 'LIGADO'
                    self.t_ataque = 0.0
                    self._criar_cone()
            elif self.t_ataque >= 1.3:
                self.raio_estado = None
                self.cone = None
                self._fim_ataque()
        elif self.ataque == 'ESPIRAL':
            if self.t_ataque >= 0.5:
                self.cd_espiral -= dt
                if self.cd_espiral <= 0:
                    self.cd_espiral = 0.09
                    self.angulo_espiral += 0.45
                    self._tiro(1.1*math.sin(self.angulo_espiral), v*0.85)
                    self._tiro(1.1*math.sin(self.angulo_espiral + math.pi/2), v*0.85)
            if self.t_ataque >= 2.6:
                self._fim_ataque()

    def _criar_cone(self):
        """Cria (uma vez) a superfície translúcida do raio ligado."""
        topo = int(self.y + 52)
        cone = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        largura_fundo = self.meia_largura_raio(ALTURA)
        pygame.draw.polygon(cone, (120, 230, 255, 95),
                            [(self.x-22, topo), (self.x+22, topo),
                             (self.x+largura_fundo, ALTURA), (self.x-largura_fundo, ALTURA)])
        self.cone = cone

    def atualizar(self, dt, nave_x):
        self.tempo += dt
        self.flash = max(0.0, self.flash - dt)
        if self.morte > 0:                       # explodindo: só treme e termina
            self.morte += dt
            if self.morte >= 2.2:
                self.morto = True
            return
        if self.entrando:                        # desce do topo (invulnerável)
            self.y += 120*dt
            if self.y >= self.Y_ALVO:
                self.y = float(self.Y_ALVO)
                self.entrando = False
            return
        # Convoca escoltas ao cruzar 66% e 33% da vida.
        if self.fase > self.convocacoes:
            self.convocacoes += 1
            self.novas_escoltas += self.cfg['chefe_escoltas']
        # Movimento horizontal: vai e vem; no RAIO, alinha com a nave e trava.
        vel = self.cfg['chefe_velocidade']
        if self.ataque == 'RAIO' and not self.raio_travado and self.raio_estado == 'AVISO':
            alvo, vel = nave_x, 320
        elif self.ataque == 'RAIO':
            alvo = self.x                        # travado (aviso final e raio ligado)
        else:
            alvo = LARGURA/2 + 170*math.sin(self.tempo*self.cfg['chefe_freq_movimento'])
        passo = vel*dt
        self.x += max(-passo, min(passo, alvo - self.x))
        if self.ataque is None:
            self.prox_ataque -= dt
            if self.prox_ataque <= 0:
                self.ataque = self._escolher_ataque()
                self.ultimo = self.ataque
                self.t_ataque = 0.0
                self.disparou = False
                if self.ataque == 'RAIO':
                    self.raio_estado, self.raio_travado = 'AVISO', False
                elif self.ataque == 'MIRA':
                    self.mira_restante, self.cd_mira = 3, 0.0
                elif self.ataque == 'ESPIRAL':
                    self.cd_espiral = 0.0
        else:
            self._executar_ataque(dt, nave_x)

    def desenhar(self, tela):
        if self.morto:
            return
        x, y = self.x, self.y
        if self.morte > 0:                       # treme durante a explosão
            x += random.randint(-4, 4)
            y += random.randint(-4, 4)
        # Raio trator: aviso (linhas piscando) e raio ligado (cone translúcido).
        topo = int(self.y + 52)
        if self.raio_estado == 'AVISO' and int(self.tempo*8) % 2 == 0:
            fundo = self.meia_largura_raio(ALTURA)
            pygame.draw.line(tela, (150, 240, 255), (int(self.x), topo), (int(self.x), ALTURA), 2)
            pygame.draw.line(tela, (80, 150, 200), (int(self.x-22), topo), (int(self.x-fundo), ALTURA), 1)
            pygame.draw.line(tela, (80, 150, 200), (int(self.x+22), topo), (int(self.x+fundo), ALTURA), 1)
        elif self.raio_estado == 'LIGADO' and self.cone is not None:
            tela.blit(self.cone, (0, 0))
            for k in range(6):                   # anéis subindo pelo raio
                yy = ALTURA - ((self.tempo*260 + k*110) % (ALTURA - topo))
                larg = self.meia_largura_raio(yy)
                pygame.draw.ellipse(tela, (190, 250, 255), (int(self.x-larg), int(yy)-4, int(2*larg), 8), 2)
        sprite = self.sprite_flash if self.flash > 0 else self.sprite
        tela.blit(sprite, sprite.get_rect(center=(int(x), int(y))))
        # Brilho de carga antes do leque / da mira.
        if self.ataque in ('LEQUE', 'MIRA') and self.t_ataque < 0.4:
            raio = int(10 + 60*self.t_ataque)
            pygame.draw.circle(tela, (255, 240, 120), (int(self.x), int(self.y + 50)), raio, 3)
        # Barra de vida (com marcas em 66% e 33%) e nome.
        largura = 340
        x0, y0 = LARGURA//2 - largura//2, 130
        pygame.draw.rect(tela, (30, 30, 44), (x0-3, y0-3, largura+6, 18), border_radius=6)
        cor = (90, 220, 110) if self.fase == 0 else ((255, 200, 50) if self.fase == 1 else (255, 70, 60))
        cheio = int(largura*self.hp/self.hp_max)
        if cheio > 0:
            pygame.draw.rect(tela, cor, (x0, y0, cheio, 12), border_radius=5)
        for marca in (0.66, 0.33):
            pygame.draw.line(tela, (255, 255, 255), (x0 + int(largura*marca), y0-3),
                             (x0 + int(largura*marca), y0+15), 1)
        nome = self.fonte.render('BOSS GALAGA', True, (255, 255, 255))
        tela.blit(nome, nome.get_rect(midbottom=(LARGURA//2, y0-5)))

class FaseGalaga:
    """Mini-jogo estilo Galaga.

    A nave fica embaixo e só anda na horizontal. Uma formação de pássaros
    especiais entra em curva, balança e faz mergulhos de ataque.
    A fase termina quando todos os inimigos são abatidos ou o tempo acaba.

    A dificuldade vem do dicionário cfg (veja parametros_galaga e a curva
    de 25 níveis em difficulty_curve.py).
    A fase é BÔNUS: não soma pontos ao placar; concluir dá vidas extras.

    Comunicação com a ClassicSession (sem a FaseGalaga conhecer a sessão):
      - vidas_ganhas: vidas extras a somar (só quando a fase é CONCLUÍDA);
      - sons: nomes de efeitos a tocar;
      - dano: True quando a nave foi atingida neste quadro;
      - terminou: True quando a fase acabou e a sessão deve voltar ao Flappy.
    """
    def __init__(self, recursos, nivel=0, cfg=None):
        self.recursos = recursos
        self.nivel = nivel          # 0 no nível 1 (só para exibir "NÍVEL n")
        # Toda a dificuldade vem de cfg; sem cfg, usa a tabela do jogo original.
        self.cfg = parametros_galaga(nivel) if cfg is None else cfg
        self.tempo_limite = self.cfg['tempo']
        self.tempo = 0.0
        self.nave_x = LARGURA/2
        self.alvo_x = None          # posição pedida pelo mouse (ou None)
        self.cooldown = 0.0
        self.invulneravel = 0.0
        self.tiros, self.explosoes = [], []
        self.estrelas = [[random.uniform(0, LARGURA),
                          random.uniform(30, ALTURA),
                          random.uniform(40, 200),
                          random.choice((1, 2))] for _ in range(70)]
        self.vidas_ganhas = 0       # vidas extras a entregar à sessão
        self.abates = 0             # inimigos derrubados (estatística; NÃO soma pontos)
        self.sons = []
        self.dano = False
        self.terminou = False
        self.resultado = None       # None, 'VITORIA' ou 'TEMPO'
        self.tempo_resultado = 0.0
        self.mensagem = ''
        self.proximo_mergulho = 3.5     # só mergulham após a entrada
        self.proximo_tiro_inimigo = 2.5
        self.furia = False          # ligada quando restam poucos inimigos
        self.tempo_msg_furia = 0.0
        self.inimigos = []
        self._criar_formacao()
        self.total_inicial = len(self.inimigos)
        # A fase tem dois estágios: 'FORMACAO' (a fase de sempre) e 'CHEFE'.
        self.estagio = 'FORMACAO'
        self.chefe = None
        self.escoltas = []          # pássaros convocados pelo chefão (mergulham uma vez)
        self.tempo_estagio = 0.0    # tempo decorrido no estágio do chefão
        self._cd_explosao = 0.0
        # Power-ups da Galaga: CAÇA GÊMEO, BOMBA NOVA e PROPULSOR TURBO.
        self.capsulas = []                  # CapsulaBonus em queda (no máximo uma)
        self.efeitos = EfeitosAtivos()      # TURBO (único bônus temporizado da Galaga)
        self.gemeo = False                  # Caça Gêmeo: dura até o primeiro golpe
        self.esfriando = 0.0                # s de superaquecimento (canhão travado) depois do Turbo
        self.abates_desde_capsula = 0       # a cada BONUS_ABATES_POR_CAPSULA abates cai uma cápsula
        self.marco_chefe = 0                # último marco de vida do chefão que já soltou cápsula
        self.onda_bomba = 0.0               # s restantes do efeito visual da Bomba (flash + anel)
        self.centro_bomba = (0.0, 0.0)
        self.aviso_bonus, self.aviso_bonus_t = '', 0.0     # dica de 4 s ao coletar um bônus

    def _criar_formacao(self):
        """Cria de 3 a 5 linhas (conforme o nível) de COLUNAS_GALAGA inimigos."""
        linhas = self.cfg['linhas']
        # Cada linha usa uma espécie diferente de pássaro.
        nomes = random.sample(PASSAROS_ESPECIAIS, linhas)
        ordem = 0
        for linha in range(linhas):
            sprite = self.recursos.inimigos[nomes[linha]]
            for col in range(COLUNAS_GALAGA):
                vida = 2 if linha == 0 else 1
                # Atraso crescente: eles entram um depois do outro.
                self.inimigos.append(Inimigo(sprite, col, linha, ordem*0.1, vida))
                ordem += 1

    @property
    def restantes(self):
        return len(self.inimigos)

    def slot(self, inimigo):
        """Posição do inimigo na formação; toda a formação balança em seno.

        A amplitude e a velocidade do balanço crescem com o nível.
        """
        deslocamento = self.cfg['balanco']*math.sin(self.tempo*self.cfg['freq_balanco'])
        x = (LARGURA/2 + (inimigo.col-(COLUNAS_GALAGA-1)/2)*ESPACO_COL
             + deslocamento)
        y = Y_FORMACAO + inimigo.linha*ESPACO_LIN
        return x, y

    def retangulo_nave(self):
        """Retângulo do DESENHO de uma nave."""
        return self.recursos.nave.get_rect(center=(int(self.nave_x), Y_NAVE))

    def caixa_colisao(self):
        """Caixa de colisão da nave (um pouco menor que o sprite: mais justa).
        Com o Caça Gêmeo ela cobre as DUAS naves: o preço do tiro duplo."""
        ret = self.retangulo_nave()
        if self.gemeo:
            ret = ret.inflate(2*DESLOC_GEMEO, 0)
        return ret.inflate(-14, -18)

    @property
    def velocidade_nave(self):
        """Velocidade horizontal da nave (o Turbo a deixa 35% mais rápida)."""
        return VELOCIDADE_NAVE*(TURBO_VEL_NAVE if self.efeitos.ativo('TURBO') else 1.0)

    def reposicionar_jogador(self):
        """Chamado pela sessão após perder uma vida (mas ainda restam vidas).
        Perder uma vida zera os bônus (Gêmeo, Turbo e superaquecimento)."""
        self.nave_x = LARGURA/2
        self.alvo_x = None
        self.tiros = [t for t in self.tiros if t.do_jogador]
        self.efeitos.limpar()
        self.gemeo = False
        self.esfriando = 0.0

    def atirar(self):
        """Dispara respeitando o intervalo mínimo e o limite de tiros.

        CAÇA GÊMEO: cada disparo sai em par (um de cada nave) e o limite de tiros
        dobra. TURBO: 2 tiros a mais na tela e cadência 1,8x. O limite total nunca passa de
        BONUS_MAX_TIROS, então Gêmeo + Turbo não se acumulam. SUPERAQUECIMENTO: canhão travado.
        """
        if self.resultado or self.cooldown > 0 or self.esfriando > 0:
            return
        turbo = self.efeitos.ativo('TURBO')
        limite = min(BONUS_MAX_TIROS,
                     MAX_TIROS_JOGADOR*(2 if self.gemeo else 1) + (2 if turbo else 0))
        if sum(1 for t in self.tiros if t.do_jogador) >= limite:
            return
        for dx in ((-DESLOC_GEMEO, DESLOC_GEMEO) if self.gemeo else (0,)):
            self.tiros.append(Tiro(self.nave_x + dx, Y_NAVE-28, 0, -VELOCIDADE_TIRO, True))
        self.cooldown = INTERVALO_TIRO/(TURBO_CADENCIA if turbo else 1.0)
        self.sons.append('pulo')

    def destruir(self, inimigo, som=True):
        """Remove o inimigo (explosão + som). Não devolve mais pontos.
        A cada BONUS_ABATES_POR_CAPSULA abates (com som) solta uma cápsula."""
        self.inimigos.remove(inimigo)
        self.explosoes.append(Explosao(inimigo.x, inimigo.y))
        if som:
            self.abates += 1
            self.sons.append('ponto')
            self.abates_desde_capsula += 1
            if self.abates_desde_capsula >= BONUS_ABATES_POR_CAPSULA:
                self.abates_desde_capsula = 0
                self.soltar_capsula(inimigo.x, inimigo.y)

    # CAÇA GÊMEO, BOMBA NOVA e PROPULSOR TURBO
    def soltar_capsula(self, x, y, tipo=None):
        """Solta uma cápsula que cai devagar (110 px/s). Só uma por vez. O sorteio não
        oferece o Caça Gêmeo enquanto ele já está ativo."""
        if self.capsulas or self.resultado:
            return
        if tipo is None:
            opcoes = ['TURBO', 'BOMBA'] + ([] if self.gemeo else ['GEMEO', 'GEMEO'])
            tipo = random.choice(opcoes)
        self.capsulas.append(CapsulaBonus(tipo, x, y, 0.0, 110.0))

    def soltar_capsula_teste(self):
        """Atalho de teste (tecla C): faz cair uma cápsula sorteada bem acima da nave."""
        self.capsulas.clear()
        self.soltar_capsula(self.nave_x, Y_NAVE - 260, random.choice(('GEMEO', 'BOMBA', 'TURBO')))

    def _avisar(self, texto):
        self.aviso_bonus, self.aviso_bonus_t = texto, 4.0

    def _aplicar_bonus(self, tipo):
        """A nave encostou numa cápsula."""
        self.sons.append('ponto')
        if tipo == 'GEMEO':
            self.gemeo = True
            self._avisar('CAÇA GÊMEO: tiro duplo (absorve 1 golpe)')
        elif tipo == 'BOMBA':
            self._detonar_bomba()
            self._avisar('BOMBA NOVA: tela limpa!')
        else:
            self.efeitos.ativar('TURBO', TIPOS_BONUS['TURBO'][2])
            self._avisar('TURBO: rápido... e depois superaquece!')

    def _detonar_bomba(self):
        """BOMBA NOVA (defesa): apaga todos os tiros inimigos, destrói mergulhadores e
        escoltas, tira 1 de vida de cada inimigo da formação e tira do chefão no máximo
        BOMBA_DANO_CHEFE (5%, mínimo 1) da vida: ela salva a nave, não pula a luta."""
        self.tiros = [t for t in self.tiros if t.do_jogador]
        for inimigo in list(self.inimigos):
            if inimigo.estado == 'ESPERA':
                continue                               # ainda nem entrou na tela
            if inimigo.estado in ('MERGULHO', 'RETORNO'):
                self.destruir(inimigo, som=False)
            else:
                inimigo.vida -= 1
                if inimigo.vida <= 0:
                    self.destruir(inimigo, som=False)
        for escolta in list(self.escoltas):
            self.escoltas.remove(escolta)
            self.explosoes.append(Explosao(escolta.x, escolta.y))
        if self.chefe and not self.chefe.entrando and self.chefe.morte <= 0:
            for _ in range(max(1, int(BOMBA_DANO_CHEFE*self.chefe.hp_max))):
                self.chefe.levar_tiro()
        self.invulneravel = max(self.invulneravel, BOMBA_INVULNERAVEL)
        self.onda_bomba = 0.5
        self.centro_bomba = (self.nave_x, Y_NAVE)
        self.sons.append('colisao')

    def _pos_quadro_bonus(self):
        """Depois do laço original da fase: o gêmeo absorve o golpe, o chefão solta
        cápsulas nos marcos de vida e as cápsulas caem e são coletadas."""
        if self.dano and self.gemeo:                   # o caça gêmeo toma o golpe no lugar
            self.dano = False
            self.gemeo = False
            self.explosoes.append(Explosao(self.nave_x + DESLOC_GEMEO, Y_NAVE))
            self.sons.append('colisao')
        if self.resultado:
            self.capsulas.clear()
            return
        chefe = self.chefe
        if chefe and not chefe.entrando and chefe.morte <= 0 and chefe.fase > self.marco_chefe:
            self.marco_chefe = chefe.fase              # cruzou 66% ou 33% da vida
            self.soltar_capsula(chefe.x, chefe.y + 40)

    def _lancar_esquadrao(self, disponiveis):
        """O líder mergulha junto com vizinhos da mesma linha.

        O tamanho do esquadrão cresce com o nível (1, 2, 3). Os pássaros saem
        escalonados (0,18 s entre um e outro) e pelo mesmo lado.
        """
        cfg = self.cfg
        lider = random.choice(disponiveis)
        vizinhos = sorted((i for i in disponiveis
                           if i is not lider and i.linha == lider.linha),
                          key=lambda i: abs(i.col - lider.col))
        grupo = [lider] + vizinhos[:cfg['esquadrao'] - 1]
        duracao = cfg['duracao_mergulho']*(0.8 if self.furia else 1.0)
        lado = random.choice((-1, 1))
        for ordem, inimigo in enumerate(grupo):
            inimigo.mergulhar(self.nave_x, duracao, atraso=0.18*ordem,
                              persegue=self.cfg['persegue'], lado=lado)

    def _atirar_inimigo(self, atirador):
        """Um tiro mirado de leve na nave. A partir do nível 2, os chefes
        (linha 0) atiram em LEQUE: 3 tiros abertos de uma vez."""
        v = self.cfg['velocidade_tiro']*(1.15 if self.furia else 1.0)
        vx = max(-120, min(120, (self.nave_x - atirador.x)*0.35))
        if self.cfg['leque'] and atirador.linha == 0:
            n = self.cfg['leque']
            for angulo in [(i - (n-1)/2)*0.3 for i in range(n)]:   # radianos; 0 = reto para baixo
                self.tiros.append(Tiro(atirador.x, atirador.y+20,
                                       vx + v*math.sin(angulo), v*math.cos(angulo), False))
        else:
            self.tiros.append(Tiro(atirador.x, atirador.y+20, vx, v, False))

    def atualizar(self, dt, esquerda, direita, atirando):
        """Um quadro da fase: timers dos bônus -> laço original -> efeitos pós-quadro.
        O laço original (formação ou chefão) continua em _atualizar_nucleo."""
        for acabou in self.efeitos.atualizar(dt):
            if acabou == 'TURBO':
                self.esfriando = BONUS_SUPERAQUECIMENTO        # o preço do Turbo
        self.esfriando = max(0.0, self.esfriando - dt)
        self.onda_bomba = max(0.0, self.onda_bomba - dt)
        self.aviso_bonus_t = max(0.0, self.aviso_bonus_t - dt)
        self._atualizar_nucleo(dt, esquerda, direita, atirando)
        self._pos_quadro_bonus()
        for capsula in self.capsulas:
            capsula.atualizar(dt)
        for capsula in list(self.capsulas):
            if capsula.retangulo().colliderect(self.caixa_colisao()):
                self.capsulas.remove(capsula)
                self._aplicar_bonus(capsula.tipo)
        self.capsulas = [c for c in self.capsulas if not c.fora_da_tela()]

    def _atualizar_nucleo(self, dt, esquerda, direita, atirando):
        cfg = self.cfg
        self.tempo += dt
        self.cooldown = max(0.0, self.cooldown - dt)
        self.invulneravel = max(0.0, self.invulneravel - dt)
        self.tempo_msg_furia = max(0.0, self.tempo_msg_furia - dt)

        # Fundo de estrelas: cada uma cai com sua própria velocidade.
        for estrela in self.estrelas:
            estrela[1] += estrela[2]*dt
            if estrela[1] > ALTURA:
                estrela[0], estrela[1] = random.uniform(0, LARGURA), 30
        for explosao in self.explosoes:
            explosao.atualizar(dt)
        self.explosoes = [e for e in self.explosoes if e.ativa]

        # --- Movimento da nave: teclado tem prioridade sobre o mouse ---
        direcao = (1 if direita else 0) - (1 if esquerda else 0)
        if direcao:
            self.nave_x += direcao*self.velocidade_nave*dt     # o Turbo acelera a nave
            self.alvo_x = None
        elif self.alvo_x is not None:
            passo = self.velocidade_nave*1.5*dt
            self.nave_x += max(-passo, min(passo, self.alvo_x-self.nave_x))
        margem = self.recursos.nave.get_width()//2 + 6
        self.nave_x = max(margem, min(LARGURA-margem, self.nave_x))

        # --- Fase já decidida: só mostra a mensagem por 2 s e termina ---
        if self.resultado:
            self.tempo_resultado += dt
            if self.tempo_resultado >= 2.0:
                self.terminou = True
            return
        if self.estagio == 'CHEFE':
            # Formação derrubada: a luta contra o chefão tem o seu próprio laço.
            self._atualizar_chefe(dt, atirando)
            return
        self.mensagem = 'FASE GALAGA!' if self.tempo < 2.0 else ''
        if self.tempo_msg_furia > 0:
            self.mensagem = 'FÚRIA!'

        if atirando:
            self.atirar()

        # --- Inimigos ---
        for inimigo in self.inimigos:
            inimigo.atualizar(dt, self.slot(inimigo), self.nave_x)

        entrada_completa = all(i.estado not in ('ESPERA', 'ENTRADA')
                               for i in self.inimigos)

        # FÚRIA: com poucos inimigos vivos, os sobreviventes
        # enlouquecem (mergulham e atiram mais depressa). Também evita que o
        # último pássaro fique "escondido" na formação.
        if (entrada_completa and not self.furia and self.inimigos
                and len(self.inimigos) <= self.total_inicial*cfg['furia']):
            self.furia = True
            self.tempo_msg_furia = 1.5
            for inimigo in self.inimigos:
                inimigo.furioso = True
        ritmo = 0.55 if self.furia else 1.0     # multiplica os intervalos

        if entrada_completa:
            self.proximo_mergulho -= dt
            if self.proximo_mergulho <= 0:
                mergulhando = sum(1 for i in self.inimigos
                                  if i.estado == 'MERGULHO')
                disponiveis = [i for i in self.inimigos
                               if i.estado == 'FORMACAO']
                limite = cfg['max_mergulhos'] + (1 if self.furia else 0)
                if disponiveis and mergulhando < limite:
                    self._lancar_esquadrao(disponiveis)
                base = cfg['intervalo_mergulho']*ritmo
                self.proximo_mergulho = random.uniform(base, base + ritmo)

        # Tiros dos inimigos.
        self.proximo_tiro_inimigo -= dt
        if self.proximo_tiro_inimigo <= 0:
            atiradores = [i for i in self.inimigos
                          if i.estado in ('FORMACAO', 'MERGULHO')]
            tiros_inimigos = sum(1 for t in self.tiros if not t.do_jogador)
            limite_tiros = cfg['max_tiros'] + max(0, cfg['leque'] - 1)
            if atiradores and tiros_inimigos < limite_tiros:
                self._atirar_inimigo(random.choice(atiradores))
            self.proximo_tiro_inimigo = (random.uniform(0.7, 1.6)
                                         * cfg['multiplicador_tiro'] * ritmo)

        # --- Tiros: movimento e remoção dos que saíram da tela ---
        for tiro in self.tiros:
            tiro.atualizar(dt)
        self.tiros = [t for t in self.tiros if not t.fora_da_tela()]

        # Tiros do jogador x inimigos.
        for tiro in [t for t in self.tiros if t.do_jogador]:
            for inimigo in self.inimigos:
                if inimigo.estado == 'ESPERA':
                    continue
                if tiro.retangulo().colliderect(inimigo.hitbox()):
                    self.tiros.remove(tiro)
                    inimigo.vida -= 1
                    if inimigo.vida <= 0:
                        self.destruir(inimigo)
                    else:
                        inimigo.piscar = 0.3
                    break   # este tiro já foi usado

        # Nave x tiros inimigos / inimigos (só se não estiver invulnerável).
        if self.invulneravel <= 0:
            caixa = self.caixa_colisao()     # com o Caça Gêmeo cobre as duas naves
            atingida = False
            for tiro in [t for t in self.tiros if not t.do_jogador]:
                if tiro.retangulo().colliderect(caixa):
                    self.tiros.remove(tiro)
                    atingida = True
                    break
            if not atingida:
                for inimigo in self.inimigos:
                    if (inimigo.estado != 'ESPERA'
                            and inimigo.hitbox().colliderect(caixa)):
                        self.destruir(inimigo, som=False)   # abalroou
                        atingida = True
                        break
            if atingida:
                self.dano = True
                self.invulneravel = TEMPO_INVULNERAVEL_MS/1000
                self.explosoes.append(Explosao(self.nave_x, Y_NAVE))

        # --- Fim de fase ---
        if not self.inimigos:
            # Formação derrubada: agora vem o CHEFÃO (se a fase tiver um; as casas
            # do mapa sem chefão terminam aqui). A vida extra vem com a vitória.
            if self.cfg.get('chefe', True):
                self._iniciar_chefe()
            else:
                self.resultado = 'VITORIA'
                self.vidas_ganhas += VIDAS_POR_FASE_ESPECIAL
                self.mensagem = 'FORMAÇÃO DERROTADA!'
                self.tiros = []
                self.sons.append('ponto')
        elif self.tempo >= self.tempo_limite:
            self.resultado = 'TEMPO'
            self.mensagem = 'TEMPO ESGOTADO'
            self.tiros = []

    # ESTÁGIO DO CHEFÃO
    def _iniciar_chefe(self):
        """A formação acabou: o Boss Galaga entra em cena."""
        self.estagio = 'CHEFE'
        self.tempo_estagio = 0.0
        self.chefe = ChefeGalaga((self.recursos.chefe_galaga, self.recursos.chefe_galaga_flash),
                                 self.nivel, self.cfg)
        self.tiros = [t for t in self.tiros if t.do_jogador]
        self.escoltas = []
        self.mensagem = 'CHEFÃO!\nBOSS GALAGA'
        self.sons.append('ponto')

    def pular_para_chefe(self):
        """Atalho de teste (tecla B): vai direto ao chefão."""
        if self.estagio == 'FORMACAO' and not self.resultado:
            self.inimigos = []
            self._iniciar_chefe()

    def _criar_escolta(self):
        """Pássaro convocado: sai do chefão e mergulha uma vez em direção à nave."""
        c = self.chefe
        nome = random.choice(PASSAROS_ESPECIAIS)
        e = Inimigo(self.recursos.inimigos[nome], 0, 3, 0.0, 1)
        e.x, e.y = c.x + random.randint(-50, 50), c.y + 40
        e.furioso = True
        e.mergulhar(self.nave_x, self.cfg['escolta_duracao_mergulho'], atraso=random.random()*0.5,
                    persegue=self.cfg['persegue'], lado=random.choice((-1, 1)))
        self.escoltas.append(e)

    def _atualizar_chefe(self, dt, atirando):
        """Um quadro da luta contra o chefão (a nave já foi movida em atualizar)."""
        c = self.chefe
        self.tempo_estagio += dt
        if c.entrando:
            self.mensagem = 'CHEFÃO!\nBOSS GALAGA'
        elif c.morte > 0:
            self.mensagem = 'CHEFÃO DERROTADO!'
        else:
            self.mensagem = ''
        if atirando:
            self.atirar()
        c.atualizar(dt, self.nave_x)
        self.tiros.extend(c.novos_tiros)
        c.novos_tiros = []
        for _ in range(c.novas_escoltas):
            self._criar_escolta()
        c.novas_escoltas = 0
        for e in self.escoltas:
            e.atualizar(dt, (0, 0), self.nave_x)
        self.escoltas = [e for e in self.escoltas if e.estado == 'MERGULHO']
        for tiro in self.tiros:
            tiro.atualizar(dt)
        self.tiros = [t for t in self.tiros if not t.fora_da_tela()]
        # Explosões em cadeia enquanto o chefão morre.
        if c.morte > 0 and not c.morto:
            self._cd_explosao -= dt
            if self._cd_explosao <= 0:
                self._cd_explosao = 0.12
                r = c.retangulo()
                self.explosoes.append(Explosao(random.randint(r.left, r.right),
                                               random.randint(r.top, r.bottom)))
        # Tiros do jogador x chefão / escoltas.
        for tiro in [t for t in self.tiros if t.do_jogador]:
            if c.morte <= 0 and tiro.retangulo().colliderect(c.hitbox()):
                self.tiros.remove(tiro)
                if c.levar_tiro():
                    self.sons.append('colisao')
                continue
            for e in self.escoltas:
                if tiro.retangulo().colliderect(e.hitbox()):
                    self.tiros.remove(tiro)
                    self.escoltas.remove(e)
                    self.explosoes.append(Explosao(e.x, e.y))
                    self.sons.append('ponto')
                    break
        # Nave x tiros inimigos / escoltas / raio trator.
        if self.invulneravel <= 0 and c.morte <= 0:
            caixa = self.caixa_colisao()     # com o Caça Gêmeo cobre as duas naves
            atingida = False
            for tiro in [t for t in self.tiros if not t.do_jogador]:
                if tiro.retangulo().colliderect(caixa):
                    self.tiros.remove(tiro)
                    atingida = True
                    break
            if not atingida:
                for e in self.escoltas:
                    if e.hitbox().colliderect(caixa):
                        self.escoltas.remove(e)
                        self.explosoes.append(Explosao(e.x, e.y))
                        atingida = True
                        break
            if not atingida and c.nave_no_raio(self.nave_x, Y_NAVE):
                atingida = True
                c.encerrar_raio()
            if atingida:
                self.dano = True
                self.invulneravel = TEMPO_INVULNERAVEL_MS/1000
                self.explosoes.append(Explosao(self.nave_x, Y_NAVE))
        # Fim do estágio.
        if c.morto:
            self.resultado = 'VITORIA'
            self.vidas_ganhas += VIDAS_POR_FASE_ESPECIAL            #
            self.mensagem = f'CHEFÃO DERROTADO!\n{texto_vidas_extras()}'
            self.tiros, self.escoltas = [], []
        elif self.tempo_estagio >= TEMPO_CHEFE_GALAGA:
            self.resultado = 'TEMPO'
            self.mensagem = 'O CHEFÃO FUGIU!'
            self.tiros, self.escoltas = [], []

    @property
    def texto_status(self):
        """Linha de informação exibida na parte de baixo da tela."""
        if self.estagio == 'CHEFE' and self.chefe:
            restante = max(0, int(TEMPO_CHEFE_GALAGA - self.tempo_estagio))
            return f'CHEFÃO   VIDA: {self.chefe.hp}/{self.chefe.hp_max}   TEMPO: {restante} s'
        restante = max(0, int(self.tempo_limite - self.tempo))
        return f'NÍVEL {self.nivel+1}   INIMIGOS: {self.restantes}   TEMPO: {restante} s'

    @property
    def dica(self):
        """Instrução exibida no começo de cada estágio ('' = nada)."""
        if self.aviso_bonus_t > 0:                 # dica do bônus recém-coletado
            return self.aviso_bonus
        if self.estagio == 'FORMACAO' and self.tempo < 5:
            return 'SETAS ou A/D: mover | ESPACO ou clique: atirar'
        if self.estagio == 'CHEFE' and self.tempo_estagio < 5:
            return 'Cuidado com o RAIO TRATOR: saia de baixo dele!'
        return ''

    cenario = None      # CenarioNaFase nas sessões com cenários comprados (o clássico não tem)

    def desenhar_fundo(self, tela):
        if self.cenario is None:
            tela.fill((6, 6, 28))
        else:
            self.cenario.desenhar_galaga(tela, self.estagio == 'CHEFE', self.tempo_estagio)

    def desenhar(self, tela):
        self.desenhar_fundo(tela)
        for x, y, velocidade, tamanho in self.estrelas:
            brilho = min(255, 100 + int(velocidade))
            pygame.draw.rect(tela, (brilho, brilho, brilho),
                             (int(x), int(y), tamanho, tamanho))
        for inimigo in self.inimigos:
            inimigo.desenhar(tela)
        for inimigo in self.escoltas:          # pássaros convocados
            inimigo.desenhar(tela)
        if self.chefe:                         # chefão, raio trator e barra de vida
            self.chefe.desenhar(tela)
        for tiro in self.tiros:
            tiro.desenhar(tela)
        for explosao in self.explosoes:
            explosao.desenhar(tela)
        # A nave pisca (aparece/some) enquanto está invulnerável.
        # Com o Caça Gêmeo são duas naves lado a lado; com o Turbo ganham chamas.
        if self.invulneravel <= 0 or int(self.invulneravel*10) % 2 == 0:
            for dx in ((-DESLOC_GEMEO, DESLOC_GEMEO) if self.gemeo else (0,)):
                tela.blit(self.recursos.nave, self.retangulo_nave().move(dx, 0))
                if self.efeitos.ativo('TURBO'):
                    x, y = int(self.nave_x + dx), Y_NAVE + 30
                    comprimento = 16 + 8*(int(self.tempo*20) % 2)       # a chama tremula
                    pygame.draw.polygon(tela, (255, 160, 40), [(x-9, y), (x+9, y), (x, y+comprimento)])
                    pygame.draw.polygon(tela, (255, 240, 130), [(x-4, y), (x+4, y), (x, y+comprimento*0.6)])
        for capsula in self.capsulas:
            capsula.desenhar(tela, self.tempo)
        if self.onda_bomba > 0:
            # Bomba Nova: um anel de choque cresce a partir da nave e a tela "pisca" em branco.
            progresso = 1 - self.onda_bomba/0.5
            cx, cy = self.centro_bomba
            pygame.draw.circle(tela, (255, 200, 120), (int(cx), int(cy)), int(40 + 760*progresso), 6)
            clarao = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            clarao.fill((255, 255, 255, int(170*(1 - progresso))))
            tela.blit(clarao, (0, 0))
        linhas = []
        if self.gemeo:
            linhas.append(('CAÇA GÊMEO (absorve 1 golpe)', TIPOS_BONUS['GEMEO'][0]))
        for nome, restante in self.efeitos.tempo.items():
            linhas.append((f'{nome} {restante:0.0f}s', TIPOS_BONUS[nome][0]))
        if self.esfriando > 0:
            linhas.append(('SUPERAQUECIDO!', (255, 90, 90)))
        desenhar_hud_bonus(tela, linhas)
