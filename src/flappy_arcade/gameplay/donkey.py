"""Fase especial Donkey Kong: selva, barris, bananas e o Kong Furioso."""
import math
import random

import pygame

from ..config.constants import (
    BONUS_BANANAS_POR_CAPSULA,
    BUMERANGUE_AJUDA_NO_CHEFE,
    CARGAS_BUMERANGUE,
    DESVIO_APICE_BARRIL,
    ESPACO_ENTRE_CANOS,
    FPS,
    LARGURA,
    MOLA_GRAVIDADE,
    MOLA_IMPULSO,
    TEMPO_CHEFE_DONKEY,
    TEMPO_DONKEY,
    TIPOS_BONUS,
    VELOCIDADE_BUMERANGUE,
    VIDAS_POR_FASE_ESPECIAL,
    Y_CHAO,
)
from .difficulty import desvio_maximo_passagem, parametros_donkey, sortear_topo_passagem
from .effects import Explosao
from .flappy import Obstaculo
from .geometry import colide_circulo
from .hud import desenhar_hud_bonus, texto_vidas_extras
from .powerups import CapsulaBonus, EfeitosAtivos


# Assim como a FaseGalaga, a FaseDonkey cuida de tudo que é interno a ela
# (obstáculos, barris, bananas, cenário, cronômetro) e só se comunica com
# a sessão por atributos: vidas_ganhas, sons, dano e terminou.
#
# Diferença importante: a Galaga usa px/segundo (× dt), enquanto a fase
# Donkey mantém a física do Flappy original em px/QUADRO (o pássaro e os
# obstáculos andam uma quantidade fixa por quadro). Só o cronômetro da
# fase usa dt (segundos reais).

class ObstaculoSelva(Obstaculo):
    """Par temático: cipó pendurado no teto + pilha de barris no chão.

    Herda toda a lógica (posição, colisão por máscara, desenho) de Obstaculo;
    só troca os sprites, sobrescrevendo criar_sprites().
    """
    def criar_sprites(self, recursos, especial, tema):
        return recursos.selva_cipo, recursos.selva_barris

class BarrilRolante:
    """Barril ARREMESSADO por Kong em arco alto.

    O barril sai das mãos do Kong (y_inicial), sobe em parábola até um ápice
    (y_apice) e passa pelo pássaro justamente nesse ponto mais alto. Perto do
    ápice a subida/queda é lenta: o barril "paira" na altura da passagem
    seguinte, e o jogador precisa escolher entre passar por cima ou por baixo,
    sem errar a faixa. Depois do ápice ele cai e, se chegar ao chão, quica.

    Horizontalmente continua "parado" em relação às pilhas (anda na mesma
    velocidade da rolagem), então nunca atravessa uma pilha: a justiça da
    fase é a mesma de antes. Só a ALTURA mudou (antes: quique de 70 a 150 px).
    """
    RAIO = 26

    def __init__(self, x, velocidade, sprite, y_inicial, y_apice, quadros_ate_apice):
        self.x = float(x)
        self.velocidade = velocidade
        self.sprite = sprite
        self.angulo = 0.0                       # rotação visual, em graus
        self.y = float(y_inicial)               # centro do barril
        # Física por quadro:  vy += g;  y += vy.  Para o ápice acontecer em
        # n quadros, exatamente em y_apice, resolvemos as duas equações
        # vy0 = -g*n      e      y_apice = y0 - g*n*(n-1)/2
        # => g = 2*(y0 - y_apice) / (n*(n-1)).
        n = max(3, int(round(quadros_ate_apice)))
        self.gravidade = 2*(y_inicial - y_apice)/(n*(n-1))
        self.vy = -self.gravidade*n

    def atualizar(self):
        self.x -= self.velocidade
        self.vy += self.gravidade
        self.y += self.vy
        chao = Y_CHAO - self.RAIO
        if self.y > chao:                       # tocou o chão: quica perdendo energia
            self.y = float(chao)
            self.vy = -abs(self.vy)*0.6
        # O barril gira enquanto voa e rola.
        self.angulo += math.degrees(self.velocidade/self.RAIO)

    def colide(self, passaro):
        """Círculo x retângulo: acha o ponto do retângulo mais próximo do
        centro do círculo e compara a distância com o raio."""
        caixa = passaro.retangulo().inflate(-16, -12)   # caixa menor que o sprite: mais justa
        px = max(caixa.left, min(self.x, caixa.right))
        py = max(caixa.top, min(self.y, caixa.bottom))
        return (self.x-px)**2 + (self.y-py)**2 < (self.RAIO-4)**2

    def desenhar(self, tela):
        giro = pygame.transform.rotate(self.sprite, self.angulo)
        tela.blit(giro, giro.get_rect(center=(int(self.x), int(self.y))))

class Banana:
    """Coletável: encostar nela soma 1 ao contador de bananas da fase.

    Não vale pontos: as fases especiais são bônus.
    """
    def __init__(self, x, y, velocidade, sprite):
        self.x, self.y = float(x), float(y)
        self.velocidade = velocidade
        self.sprite = sprite
        self.coletada = False

    def atualizar(self):
        self.x -= self.velocidade

    def retangulo(self):
        return self.sprite.get_rect(center=(int(self.x), int(self.y)))

    def desenhar(self, tela, tempo):
        if self.coletada:
            return
        # Flutuação puramente visual; a colisão usa a posição real (sem o seno).
        flutua = int(4*math.sin(tempo*6 + self.x*0.05))
        tela.blit(self.sprite, self.retangulo().move(0, flutua))

class BolaDeFogo:
    """"Chama viva" do Donkey Kong: voa para a esquerda ondulando de leve.
    Aparece no chefão, sempre depois de um aviso (seta + linha tracejada)."""
    RAIO = 18

    def __init__(self, x, y, velocidade, sprite):
        self.x, self.y0 = float(x), float(y)
        self.velocidade = velocidade
        self.sprite = sprite
        self.t = 0

    @property
    def y(self):
        return self.y0 + 14*math.sin(self.t*0.18)

    def atualizar(self):
        self.x -= self.velocidade
        self.t += 1

    def colide(self, passaro):
        # A "cabeça" da chama fica à esquerda do sprite (a cauda vai para a direita).
        return colide_circulo(self.x - 10, self.y, self.RAIO,
                              passaro.retangulo().inflate(-16, -12))

    def desenhar(self, tela):
        tela.blit(self.sprite, self.sprite.get_rect(center=(int(self.x), int(self.y))))

class Rebite(Banana):
    """Rebite dourado: o ponto fraco da estrutura do Kong furioso (referência
    à fase dos rebites do Donkey Kong original). Coletar todos derrota o chefão.
    Herda de Banana: mesma lógica de posição, rolagem e coleta; muda o desenho."""
    def desenhar(self, tela, tempo):
        if self.coletada:
            return
        flutua = int(5*math.sin(tempo*5 + self.x*0.03))
        ret = self.retangulo().move(0, flutua)
        raio = 28 + int(4*math.sin(tempo*9))              # halo pulsando
        pygame.draw.circle(tela, (255, 232, 120), ret.center, raio, 3)
        tela.blit(self.sprite, ret)

class FaseDonkey:
    """Fase especial Donkey Kong: o pássaro atravessa uma selva noturna.

    A fase tem dois estágios:
      1) TRAVESSIA: cipós + pilhas de barris (ObstaculoSelva) e Kong arremessando
         barris em arco ALTO entre as pilhas. A dificuldade vem do nível do jogo:
         salvas de 1, 2 ou 3 barris, rolagem mais rápida, abertura menor (veja
         parametros_donkey). Bananas flutuam nas passagens (só um contador).
      2) CHEFÃO "KONG FURIOSO": sem pilhas, em céu aberto. Kong, maior, ataca com
         salvas de barris (com um túnel livre), bolas de fogo avisadas por uma seta
         e fica mais rápido a cada rebite coletado. Para vencer, colete todos os
         REBITES dourados que passam voando (a estrutura desaba e Kong cai).
    Vencer o chefão dá +1 vida; a fase não soma pontos ao placar.

    Comunicação com a ClassicSession (a fase não conhece a sessão):
      - vidas_ganhas: vidas extras a somar (só ao derrotar o chefão);
      - sons: nomes de efeitos a tocar;
      - dano: True quando o pássaro foi atingido neste quadro;
      - terminou: True quando a fase acabou e a sessão deve voltar ao Flappy.
    """
    X_KONG = LARGURA - 80          # centro horizontal do Kong
    # Centro do barril quando Kong o segura sobre a cabeça (altura das mãos):
    # topo do sprite do Kong (Y_CHAO + 8 - 170) + metade da altura do barril (20).
    Y_MAO_KONG = Y_CHAO + 8 - 170 + 20
    # No chefão o Kong é 35% maior: mesma conta com o sprite ampliado.
    Y_MAO_CHEFE = Y_CHAO + 8 - int(170*1.35) + 27
    X_MAO_CHEFE = 500.0            # x de onde os barris saem no chefão

    def __init__(self, recursos, nivel=0, cfg=None):
        self.recursos = recursos
        self.nivel = nivel          # 0 no nível 1 (só para exibir "NÍVEL n")
        # Toda a dificuldade vem de cfg; sem cfg, usa a tabela do jogo original.
        self.cfg = parametros_donkey(nivel) if cfg is None else cfg
        self.tempo = 0.0
        self.velocidade = self.cfg['velocidade']
        self.chance_barril = self.cfg['chance_barril']
        self.obstaculos, self.barris, self.bananas = [], [], []
        self.bananas_coletadas = 0
        self.rolagem = 0.0          # quanto o cenário já andou (px)
        self.kong_lancando = 0.0    # tempo restante da pose "arremessou"
        self.carregando = False     # Kong segura um barril (preparo do arremesso)
        self.decidido = False       # já sorteou se haverá barril neste intervalo
        self.vidas_ganhas = 0       # vidas extras a entregar à sessão
        self.sons = []
        self.dano = False
        self.terminou = False
        self.resultado = None       # None, 'VITORIA' ou 'TEMPO'
        self.tempo_resultado = 0.0
        self.mensagem = ''
        # Estágio do chefão.
        self.estagio = 'TRAVESSIA'
        self.tempo_chefe = 0.0
        self.intro_chefe = 0.0      # s restantes da apresentação do chefão
        self.ataque = None          # 'SALVA' em preparo (ou None)
        self.ultimo_ataque = None
        self.prox_ataque = 0.0
        self.preparo = 0.0
        self.fogos, self.avisos_fogo, self.rebites = [], [], []   # avisos: [y, restante]
        self.rebites_total = self.cfg['rebites']
        self.rebites_coletados = 0
        self.prox_rebite = 0.0
        self.ultima_faixa = None    # altura do último túnel livre (os rebites aparecem por ali)
        self.tremor = 0.0           # Kong estremece ao perder um rebite
        self.derrotado = False
        self.fonte = pygame.font.Font(None, 22)
        # Power-ups do Donkey: BANANA-RANG e PULO DE MOLA.
        self.explosoes = []                 # o Donkey não tinha explosões; o Banana-rang as usa
        self.capsulas = []                  # CapsulaBonus a caminho (no máximo uma)
        self.efeitos = EfeitosAtivos()      # MOLA (temporizado)
        self.cargas = 0                     # cargas do Banana-rang
        self.bumerangues = []               # bumerangues em voo (no máximo um)
        self.marco_bananas = 0              # quantas cápsulas as bananas já geraram
        self.fisica_original = None         # (gravidade, impulso) guardados enquanto a Mola durar
        self.aviso_bonus, self.aviso_bonus_t = '', 0.0     # dica de 4 s ao coletar um bônus

    def reposicionar(self):
        """Chamado pela sessão após perder uma vida (mas ainda restam vidas):
        limpa a pista para o jogador recomeçar sem colisões imediatas."""
        self.obstaculos, self.barris, self.bananas = [], [], []
        self.fogos, self.avisos_fogo, self.rebites = [], [], []
        self.carregando = False     # cancela um arremesso que estava em preparo
        self.decidido = False
        self.ataque = None
        self.preparo = 0.0
        # Perder uma vida zera os bônus (o pássaro novo já vem com a física normal).
        self.efeitos.limpar()
        self.capsulas, self.bumerangues = [], []
        self.cargas = 0
        self.fisica_original = None
        if self.estagio == 'CHEFE':
            self.prox_ataque = max(self.prox_ataque, 1.5)
            self.prox_rebite = max(self.prox_rebite, 1.0)

    def pular_para_chefe(self):
        """Atalho de teste (tecla B): vai direto ao chefão."""
        if self.estagio == 'TRAVESSIA' and not self.resultado:
            self._iniciar_chefe()

    # BANANA-RANG e PULO DE MOLA
    def soltar_capsula(self, tipo=None):
        """Faz uma cápsula entrar pela direita, no centro da próxima passagem (ou a meia
        altura, no chefão), acompanhando a rolagem. Só uma por vez."""
        if self.capsulas or self.resultado:
            return
        if tipo is None:
            tipo = random.choice(('BUMERANGUE', 'MOLA'))
        y = (self.obstaculos[-1].topo_passagem + self.cfg['abertura']/2
             if self.obstaculos else 370)
        self.capsulas.append(CapsulaBonus(tipo, LARGURA + 20, y, -self.velocidade*FPS, 0.0))

    def soltar_capsula_teste(self):
        """Atalho de teste (tecla C): solta uma cápsula agora."""
        self.capsulas.clear()
        self.soltar_capsula()

    def _avisar(self, texto):
        self.aviso_bonus, self.aviso_bonus_t = texto, 4.0

    def lancar_bumerangue(self, passaro):
        """BANANA-RANG (tecla X): lança uma banana que vai até o canto direito e volta,
        destruindo barris e chamas pelo caminho. Um por vez; gasta 1 das cargas."""
        if self.cargas <= 0 or self.bumerangues or self.resultado:
            return
        self.cargas -= 1
        self.bumerangues.append({'x': passaro.x + 50, 'y': passaro.y + passaro.sprite.get_height()/2,
                                 'volta': False, 'angulo': 0.0})
        self.sons.append('pulo')

    def _golpe_bumerangue(self, b):
        """Destrói o que o bumerangue tocou. Devolve True se acertou algo."""
        acertou = False

        def perto(objeto, raio):
            return math.hypot(objeto.x - b['x'], objeto.y - b['y']) < raio + 16
        for barril in list(self.barris):
            if perto(barril, barril.RAIO):
                self.barris.remove(barril)
                self.explosoes.append(Explosao(barril.x, barril.y))
                acertou = True
        for fogo in list(self.fogos):
            if perto(fogo, 18):
                self.fogos.remove(fogo)
                self.explosoes.append(Explosao(fogo.x, fogo.y))
                acertou = True
        if BUMERANGUE_AJUDA_NO_CHEFE:
            for rebite in self.rebites:
                if not rebite.coletada and perto(rebite, 20):
                    rebite.coletada = True
                    self.rebites_coletados += 1
                    self.sons.append('ponto')
                    acertou = True
        return acertou

    def _atualizar_bonus(self, dt, passaro):
        """Um quadro dos bônus do Donkey: timers, Pulo de Mola, cápsulas e bumerangues."""
        self.aviso_bonus_t = max(0.0, self.aviso_bonus_t - dt)
        self.efeitos.atualizar(dt)
        for explosao in self.explosoes:
            explosao.atualizar(dt)
        self.explosoes = [e for e in self.explosoes if e.ativa]
        if self.resultado:                              # fase decidida: some tudo
            self.efeitos.limpar()
            self.capsulas.clear()
            self.bumerangues.clear()
        # PULO DE MOLA: gravidade x0,8 e impulso x1,05 enquanto durar (e restaura depois).
        if self.efeitos.ativo('MOLA'):
            if self.fisica_original is None:
                self.fisica_original = (passaro.gravidade, passaro.impulso)
            passaro.gravidade = self.fisica_original[0]*MOLA_GRAVIDADE
            passaro.impulso = self.fisica_original[1]*MOLA_IMPULSO
        elif self.fisica_original is not None:
            passaro.gravidade, passaro.impulso = self.fisica_original
            self.fisica_original = None
        if self.resultado:
            return
        # Bananas viram combustível: a cada BONUS_BANANAS_POR_CAPSULA cai uma cápsula.
        if (self.estagio == 'TRAVESSIA' and not self.capsulas
                and self.bananas_coletadas//BONUS_BANANAS_POR_CAPSULA > self.marco_bananas):
            self.marco_bananas += 1
            self.soltar_capsula()
        for capsula in self.capsulas:
            capsula.atualizar(dt)
        for capsula in list(self.capsulas):
            if capsula.retangulo().colliderect(passaro.retangulo()):
                self.capsulas.remove(capsula)
                self.sons.append('ponto')
                if capsula.tipo == 'BUMERANGUE':
                    self.cargas = CARGAS_BUMERANGUE
                    self._avisar(f'BANANA-RANG x{self.cargas}: aperte X para lançar')
                else:
                    self.efeitos.ativar('MOLA', TIPOS_BONUS['MOLA'][2])
                    self._avisar('PULO DE MOLA: salto maior por 7 s')
        self.capsulas = [c for c in self.capsulas if not c.fora_da_tela()]
        # Bumerangues: ida a 520 px/s até perto da borda, depois volta até o pássaro.
        for b in self.bumerangues:
            b['angulo'] += 900*dt
            b['x'] += (-1 if b['volta'] else 1)*VELOCIDADE_BUMERANGUE*dt
            if self._golpe_bumerangue(b):
                self.sons.append('colisao')
            if not b['volta'] and b['x'] >= LARGURA - 70:
                b['volta'] = True
        self.bumerangues = [b for b in self.bumerangues
                            if not (b['volta'] and b['x'] <= passaro.x + 30)]

    def _desenhar_bonus(self, tela, passaro):
        """Cápsulas, bumerangues, mola sob o pássaro, explosões e a lista de bônus ativos."""
        estilo = self.estilo_bonus
        if estilo:
            self._desenhar_bonus_novo(tela, passaro, estilo)
        else:
            for capsula in self.capsulas:
                capsula.desenhar(tela, self.tempo)
            if self.efeitos.ativo('MOLA'):                  # mola verde sob o pássaro
                ret = passaro.retangulo()
                pontos = [(ret.centerx + (-10 if i % 2 else 10), ret.bottom + 3 + i*4) for i in range(6)]
                pygame.draw.lines(tela, (120, 255, 140), False, pontos, 3)
            for b in self.bumerangues:
                giro = pygame.transform.rotate(self.recursos.banana, b['angulo'])
                tela.blit(giro, giro.get_rect(center=(int(b['x']), int(b['y']))))
        for explosao in self.explosoes:
            explosao.desenhar(tela)
        linhas = []
        if self.cargas:
            linhas.append((f'BANANA-RANG x{self.cargas}  [X]', TIPOS_BONUS['BUMERANGUE'][0]))
        for nome, restante in self.efeitos.tempo.items():
            linhas.append((f'{nome} {restante:0.0f}s', TIPOS_BONUS[nome][0]))
        if estilo:
            linhas = [(estilo.nome(texto), cor) for texto, cor in linhas]
        desenhar_hud_bonus(tela, linhas)

    def _desenhar_bonus_novo(self, tela, passaro, estilo):
        """Modos novos: folha, cacho e itens em pixel art (veja bonus_visuals.py)."""
        for capsula in self.capsulas:
            estilo.desenhar_item(tela, capsula, self.tempo)
        if self.efeitos.ativo('MOLA'):
            estilo.desenhar_mola(tela, passaro)
        else:
            estilo.esquecer_mola()
        estilo.desenhar_bumerangues(tela, self.bumerangues)

    @property
    def texto_status(self):
        """Linha de informação exibida na parte de baixo da tela."""
        if self.estagio == 'CHEFE':
            restante = max(0, math.ceil(TEMPO_CHEFE_DONKEY - self.tempo_chefe))
            return (f'KONG FURIOSO   REBITES: {self.rebites_coletados}/{self.rebites_total}'
                    f'   TEMPO: {restante} s')
        restante = max(0, math.ceil(TEMPO_DONKEY - self.tempo))
        return f'NÍVEL {self.nivel+1}   TEMPO: {restante} s   BANANAS: {self.bananas_coletadas}'

    @property
    def dica(self):
        """Instrução exibida no começo de cada estágio ('' = nada)."""
        if self.aviso_bonus_t > 0:                 # dica do bônus recém-coletado
            return self.estilo_bonus.nome(self.aviso_bonus) if self.estilo_bonus else self.aviso_bonus
        if self.estagio == 'TRAVESSIA' and self.tempo < 5:
            return 'ESPACO ou clique: bater asas | desvie dos barris!'
        if self.estagio == 'CHEFE' and self.tempo_chefe < 5:
            return 'Pegue os REBITES dourados! Cuidado com barris e chamas.'
        return ''

    # TRAVESSIA: barris arremessados em arco alto, em salvas de 1 a 3
    @staticmethod
    def _slots(k):
        """Deslocamentos (px) dos barris de uma salva em relação ao centro do
        corredor. O corredor entre as pilhas tem 204 px; barris de 52 px nestas
        posições ainda deixam ~10 px até as pilhas (nunca as atravessam)."""
        return {1: (0,), 2: (-45, 45), 3: (-65, 0, 65)}[k]

    def _tamanho_salva(self):
        cfg = self.cfg
        if cfg['salva_max'] == 1:
            return 1
        if cfg['salva_max'] == 3 and random.random() < cfg['chance_tres']:
            return 3
        return cfg['salva_min']

    def _alturas_salva(self, k, novo, anterior):
        """Altura (y do ápice) de cada barril de uma salva de k barris.

        k = 1: no centro da passagem seguinte (± DESVIO_APICE_BARRIL).
        k >= 2: abre-se um TÚNEL livre de cfg['faixa'] px dentro da passagem
        seguinte, ao alcance do pássaro a partir da passagem anterior; os barris
        ficam alternadamente acima e abaixo do túnel (cada um "pairando" na hora
        em que cruza com o pássaro). Quem mantiver o pássaro no túnel passa.
        """
        cfg = self.cfg
        abertura = cfg['abertura']
        y_max = self.Y_MAO_KONG - 40          # o ápice precisa ficar acima das mãos do Kong
        if k == 1:
            centro = novo.topo_passagem + abertura/2
            y = centro + random.randint(-DESVIO_APICE_BARRIL, DESVIO_APICE_BARRIL)
            return [min(y, y_max)]
        faixa = cfg['faixa']
        # Centros possíveis do túnel dentro da passagem seguinte (com folga de 12 px)...
        lo = novo.topo_passagem + faixa/2 + 12
        hi = novo.topo_passagem + abertura - faixa/2 - 12
        if anterior is not None:
            # ...que também fiquem ao alcance (~70 px) de quem acabou de sair da
            # passagem anterior.
            alcance_lo = anterior.topo_passagem - 46
            alcance_hi = anterior.topo_passagem + anterior.abertura + 46
            if lo > alcance_hi:                # passagens em extremos opostos: o ponto mais próximo
                hi = lo
            elif hi < alcance_lo:
                lo = hi
            else:
                lo, hi = max(lo, alcance_lo), min(hi, alcance_hi)
        centro_faixa = random.uniform(lo, hi)
        lado = random.choice((-1, 1))
        alturas = []
        for i in range(k):
            sinal = lado if i % 2 == 0 else -lado
            desloc = faixa/2 + 22 + random.randint(0, 25)
            y = centro_faixa + sinal*desloc
            if y > y_max:                     # não dá para arremessar tão baixo: vai para cima do túnel
                y = centro_faixa - desloc
            alturas.append(max(70.0, y))
        return alturas

    def _sortear_topo(self, anterior, passaro):
        """Topo da próxima passagem, sem exigir uma subida impossível
        em relação à passagem anterior."""
        if anterior is None:
            return sortear_topo_passagem(None, 0)
        desvio = desvio_maximo_passagem(
            self.cfg['abertura'], self.velocidade, passaro.gravidade, passaro.impulso,
            self.recursos.selva_barris.get_width(),
            passaro.sprite.get_width(), passaro.sprite.get_height())
        return sortear_topo_passagem(anterior.topo_passagem, desvio)

    def _gerar_par(self, passaro):
        """Cria uma pilha+cipó na borda direita e, às vezes, uma banana e uma salva
        de barris. O barril só sai se Kong estiver "carregando" (sorteado ~0,5 s
        antes, para a pose de preparo aparecer)."""
        cfg = self.cfg
        anterior = self.obstaculos[-1] if self.obstaculos else None
        novo = ObstaculoSelva(LARGURA, self.recursos, velocidade=self.velocidade,
                              abertura=cfg['abertura'],
                              topo=self._sortear_topo(anterior, passaro))   #
        self.obstaculos.append(novo)
        # Banana em altura aleatória dentro da passagem (±70 px do centro).
        y_banana = novo.topo_passagem + cfg['abertura']/2 + random.randint(-70, 70)
        self.bananas.append(Banana(novo.x + novo.largura/2, y_banana,
                                   self.velocidade, self.recursos.banana))
        if anterior and self.carregando:
            centro_corredor = (anterior.x + anterior.largura + novo.x)/2
            k = self._tamanho_salva()
            alturas = self._alturas_salva(k, novo, anterior)
            x_passaro = passaro.x + passaro.sprite.get_width()/2
            for dx, y_apice in zip(self._slots(k), alturas):
                x_barril = centro_corredor + dx
                # O ápice deve acontecer quando o barril estiver na altura do
                # pássaro: quantos quadros ele leva para andar até lá?
                quadros = (x_barril - x_passaro)/self.velocidade
                self.barris.append(BarrilRolante(x_barril, self.velocidade,
                                                 self.recursos.barril, self.Y_MAO_KONG,
                                                 y_apice, quadros))
            self.kong_lancando = 0.6        # Kong fica de mãos vazias por 0,6 s
            self.sons.append('pulo')
        self.carregando = False
        self.decidido = False

    def _atualizar_travessia(self, dt, passaro):
        cfg = self.cfg
        self.mensagem = 'FASE DONKEY KONG!' if self.tempo < 2.0 else ''
        # Geração: mesma regra de espaçamento do Flappy original.
        if not self.obstaculos or self.obstaculos[-1].x < LARGURA - ESPACO_ENTRE_CANOS:
            self._gerar_par(passaro)
        # Antecipação: ~0,5 s antes da próxima pilha, Kong decide se vai arremessar e
        # ergue o barril. O preparo fica mais curto nos níveis altos.
        if (self.obstaculos and not self.decidido
                and self.obstaculos[-1].x < LARGURA - ESPACO_ENTRE_CANOS
                + self.velocidade*cfg['antecipacao']):
            self.decidido = True
            self.carregando = random.random() < self.chance_barril
        for objeto in self.obstaculos + self.barris + self.bananas:
            objeto.atualizar()
        # Colisões.
        for obstaculo in self.obstaculos:
            if obstaculo.colide(passaro):
                self.dano = True
                break
            if not obstaculo.passou and obstaculo.x + obstaculo.largura < passaro.x:
                obstaculo.passou = True
                self.sons.append('ponto')      # só o som: a fase não soma pontos
        if any(barril.colide(passaro) for barril in self.barris):
            self.dano = True
        for banana in self.bananas:
            if not banana.coletada and banana.retangulo().colliderect(passaro.retangulo()):
                banana.coletada = True
                self.bananas_coletadas += 1    # só contador: não soma pontos
                self.sons.append('ponto')
        # Teto e chão matam, como no Flappy normal.
        if passaro.y < 30 or passaro.retangulo().bottom >= Y_CHAO:
            self.dano = True
        # Remove o que já saiu pela esquerda.
        self.obstaculos = [o for o in self.obstaculos if o.x + o.largura >= 0]
        self.barris = [b for b in self.barris if b.x + b.RAIO >= 0]
        self.bananas = [b for b in self.bananas if b.x + 30 >= 0]
        # Fim da travessia: o cronômetro zerou com o pássaro vivo -> CHEFÃO.
        if self.tempo >= TEMPO_DONKEY and not self.dano:
            if self.cfg.get('chefe', True):
                self._iniciar_chefe()
            else:                       # casa do mapa sem chefão: a travessia basta
                self.resultado = 'VITORIA'
                self.vidas_ganhas += VIDAS_POR_FASE_ESPECIAL
                self.mensagem = 'TRAVESSIA CONCLUÍDA!'
                self.barris, self.fogos = [], []
                self.sons.append('ponto')

    # CHEFÃO: Kong furioso (rebites, salvas de barris e bolas de fogo)
    def _iniciar_chefe(self):
        """A travessia acabou: limpa a pista e apresenta o chefão."""
        self.estagio = 'CHEFE'
        self.tempo_chefe = 0.0
        self.intro_chefe = 2.5
        self.obstaculos, self.barris, self.bananas = [], [], []
        self.carregando = False
        self.decidido = False
        self.prox_ataque = 1.0
        self.prox_rebite = 1.5
        self.mensagem = 'CHEFÃO!\nKONG FURIOSO'
        self.sons.append('ponto')

    def _escolher_ataque(self):
        """SALVA de barris ou FOGO (as chamas entram a partir do nível 2)."""
        opcoes = ['SALVA']
        if self.cfg['fogo']:
            opcoes += ['SALVA', 'FOGO']
        if self.ultimo_ataque == 'FOGO':
            opcoes = [o for o in opcoes if o != 'FOGO']      # não repete o fogo
        return random.choice(opcoes)

    def _ataques_do_chefe(self, dt, passaro):
        cfg = self.cfg
        # Depois de coletar metade dos rebites, Kong acelera (intervalos 25% menores).
        raiva = 0.75 if self.rebites_coletados*2 >= self.rebites_total else 1.0
        if self.ataque == 'SALVA':                   # Kong está erguendo o barril
            self.preparo -= dt
            if self.preparo <= 0:
                self._lancar_salva_chefe(passaro)
                self.carregando = False
                self.ataque = None
                self.prox_ataque = cfg['chefe_intervalo']*raiva
            return
        self.prox_ataque -= dt
        # Só ataca de novo quando a pista está livre: os ataques nunca se sobrepõem.
        if self.prox_ataque > 0 or self.barris or self.fogos or self.avisos_fogo:
            return
        escolhido = self._escolher_ataque()
        self.ultimo_ataque = escolhido
        if escolhido == 'SALVA':
            self.ataque = 'SALVA'
            self.preparo = 0.6*raiva
            self.carregando = True
        else:                                        # FOGO: avisa antes de soltar
            quantas = self.cfg['fogo_chamas']
            centro = passaro.y + passaro.sprite.get_height()/2
            for i in range(quantas):
                desvio = random.randint(-40, 40) if i == 0 else random.choice((-1, 1))*random.randint(110, 170)
                y = max(90.0, min(Y_CHAO - 50.0, centro + desvio))
                self.avisos_fogo.append([y, 0.9 + 0.35*i])
            self.prox_ataque = cfg['chefe_intervalo']*raiva

    def _lancar_salva_chefe(self, passaro):
        """Kong arremessa k barris de uma vez, deixando um túnel livre (a altura
        do túnel fica perto do pássaro, ±80 px, mas dentro da região dos barris)."""
        cfg = self.cfg
        k = cfg['chefe_barris']
        faixa = cfg['faixa']
        y_max = self.Y_MAO_CHEFE - 40
        lo, hi = 210.0, max(240.0, y_max - faixa/2 - 47)
        alvo = passaro.y + passaro.sprite.get_height()/2
        centro_faixa = max(lo, min(hi, alvo + random.randint(-80, 80)))
        self.ultima_faixa = centro_faixa
        x_passaro = passaro.x + passaro.sprite.get_width()/2
        lado = random.choice((-1, 1))
        for i in range(k):
            sinal = lado if i % 2 == 0 else -lado
            desloc = faixa/2 + 22 + random.randint(0, 25)
            y = centro_faixa + sinal*desloc
            if y > y_max:
                y = centro_faixa - desloc
            velocidade = cfg['chefe_vel_barril']*(1 + 0.1*i)     # chegam um pouco escalonados
            quadros = (self.X_MAO_CHEFE - x_passaro)/velocidade
            self.barris.append(BarrilRolante(self.X_MAO_CHEFE, velocidade, self.recursos.barril,
                                             self.Y_MAO_CHEFE, max(70.0, y), quadros))
        self.kong_lancando = 0.7
        self.sons.append('pulo')

    def _rebites_do_chefe(self, dt, passaro):
        """Mantém um rebite por vez voando pela tela, até faltar nenhum."""
        faltam = self.rebites_total - self.rebites_coletados
        self.prox_rebite -= dt
        if not self.rebites and faltam > 0 and self.prox_rebite <= 0:
            if self.ultima_faixa is not None and random.random() < 0.6:
                y = self.ultima_faixa + random.randint(-40, 40)    # perto do último túnel livre
            else:
                y = random.randint(200, 600)
            y = max(150, min(Y_CHAO - 90, y))
            self.rebites.append(Rebite(LARGURA + 30, y, 4.5, self.recursos.rebite))
            self.prox_rebite = 2.5

    def _atualizar_chefe(self, dt, passaro):
        cfg = self.cfg
        self.tempo_chefe += dt
        if self.intro_chefe > 0:
            self.intro_chefe -= dt
            self.mensagem = 'CHEFÃO!\nKONG FURIOSO'
        else:
            self.mensagem = ''
            self._ataques_do_chefe(dt, passaro)
            self._rebites_do_chefe(dt, passaro)
        for objeto in self.barris + self.fogos + self.rebites:
            objeto.atualizar()
        # Avisos de fogo: quando o tempo zera, a bola de fogo sai pela borda direita.
        for aviso in self.avisos_fogo:
            aviso[1] -= dt
        for y, restante in [a for a in self.avisos_fogo if a[1] <= 0]:
            self.fogos.append(BolaDeFogo(LARGURA + 40, y, cfg['chefe_vel_fogo'], self.recursos.bola_fogo))
            self.sons.append('pulo')
        self.avisos_fogo = [a for a in self.avisos_fogo if a[1] > 0]
        # Colisões.
        if (any(b.colide(passaro) for b in self.barris)
                or any(f.colide(passaro) for f in self.fogos)):
            self.dano = True
        if passaro.y < 30 or passaro.retangulo().bottom >= Y_CHAO:
            self.dano = True
        for rebite in self.rebites:
            if not rebite.coletada and rebite.retangulo().colliderect(passaro.retangulo()):
                rebite.coletada = True
                self.rebites_coletados += 1
                self.tremor = 0.5
                self.kong_lancando = 0.35
                self.sons.append('ponto')
        self.rebites = [r for r in self.rebites if not r.coletada and r.x + 30 >= 0]
        self.barris = [b for b in self.barris if b.x + b.RAIO >= 0]
        self.fogos = [f for f in self.fogos if f.x + f.RAIO >= 0]
        # Fim do chefão.
        if self.rebites_coletados >= self.rebites_total:
            self.derrotado = True
            self.resultado = 'VITORIA'
            self.vidas_ganhas += VIDAS_POR_FASE_ESPECIAL              #
            self.mensagem = f'KONG DERROTADO!\n{texto_vidas_extras()}'
            self.barris, self.fogos, self.avisos_fogo, self.rebites = [], [], [], []
            self.dano = False                 # a vitória cancela uma colisão do mesmo quadro
        elif self.tempo_chefe >= TEMPO_CHEFE_DONKEY:
            self.resultado = 'TEMPO'
            self.mensagem = 'O KONG ESCAPOU!'
            self.barris, self.fogos, self.avisos_fogo, self.rebites = [], [], [], []

    # Laço da fase
    def atualizar(self, dt, passaro):
        """Um quadro da fase. O pássaro já foi atualizado pelo ClassicSession."""
        self.kong_lancando = max(0.0, self.kong_lancando - dt)
        self.tremor = max(0.0, self.tremor - dt)
        self._atualizar_bonus(dt, passaro)      # timers, Mola, cápsulas e bumerangues
        # --- Fase já decidida: mostra a mensagem por 2 s e termina ---
        if self.resultado:
            self.tempo_resultado += dt
            if self.tempo_resultado >= 2.0:
                self.terminou = True
            return
        self.tempo += dt
        self.rolagem += self.velocidade
        if self.estagio == 'TRAVESSIA':
            self._atualizar_travessia(dt, passaro)
        else:
            self._atualizar_chefe(dt, passaro)

    # Desenho
    cenario = None      # CenarioNaFase nas sessões com cenários comprados (o clássico não tem)
    estilo_bonus = None  # EstiloBonus nos modos novos (o clássico mantém as cápsulas)

    def desenhar_fundo(self, tela):
        r = self.recursos
        if self.cenario is None:
            tela.blit(r.fundo_selva, (0, 0))
        else:
            self.cenario.desenhar_donkey(tela, self.rolagem)
        # Parallax: camadas distantes andam mais devagar que as próximas.
        for camada, fator in ((r.palmeiras_longe, 0.15), (r.palmeiras_perto, 0.35)):
            x = -int(self.rolagem*fator) % LARGURA
            tela.blit(camada, (x - LARGURA, 0))
            tela.blit(camada, (x, 0))

    def desenhar(self, tela, passaro):
        """Desenha, de trás para frente: céu, palmeiras, Kong, obstáculos,
        barris, bananas/rebites, chamas, chão e, por último, o pássaro."""
        r = self.recursos
        self.desenhar_fundo(tela)
        self._desenhar_kong(tela)
        for obstaculo in self.obstaculos:
            obstaculo.desenhar(tela)
        for barril in self.barris:
            barril.desenhar(tela)
        for banana in self.bananas:
            banana.desenhar(tela, self.tempo)
        for rebite in self.rebites:
            rebite.desenhar(tela, self.tempo)
        self._desenhar_avisos_fogo(tela)
        for fogo in self.fogos:
            fogo.desenhar(tela)
        # Chão de viga: repete o tile e desliza junto com a rolagem.
        largura_tile = r.viga.get_width()
        x = -int(self.rolagem) % largura_tile - largura_tile
        while x < LARGURA:
            tela.blit(r.viga, (x, Y_CHAO))
            x += largura_tile
        passaro.desenhar(tela)
        self._desenhar_bonus(tela, passaro)      #
        if self.estagio == 'CHEFE':
            self._desenhar_barra_rebites(tela)

    def _desenhar_kong(self, tela):
        """Kong respira de leve (±2 px). Três poses: com o barril erguido (preparo),
        de mãos vazias (acabou de soltar) e parado. No chefão ele é maior, fica
        vermelho depois de metade dos rebites, estremece ao perder um rebite e,
        derrotado, gira e cai para fora da tela."""
        r = self.recursos
        if self.estagio == 'CHEFE':
            furioso = self.rebites_coletados*2 >= self.rebites_total
            conjunto = r.kong_furioso if furioso else r.kong_boss
            x_base = self.X_KONG + 20
        else:
            conjunto = r.kong
            x_base = self.X_KONG
        if self.carregando:
            pose = conjunto['lanca']
        elif self.kong_lancando > 0:
            pose = conjunto['arremessou']
        else:
            pose = conjunto['parado']
        respira = int(2*math.sin(self.tempo*4))
        tremor = random.randint(-4, 4) if self.tremor > 0 else 0
        if self.derrotado:
            queda = self.tempo_resultado
            pose = pygame.transform.rotate(pose, -35*min(queda, 1.5))
            tela.blit(pose, pose.get_rect(midbottom=(x_base + int(30*queda),
                                                     Y_CHAO + 8 + int(260*queda*queda))))
        else:
            tela.blit(pose, pose.get_rect(midbottom=(x_base + tremor, Y_CHAO + 8 + respira)))

    def _desenhar_avisos_fogo(self, tela):
        """Aviso de bola de fogo: linha tracejada pela altura do ataque e uma seta
        piscando na borda direita (a bola sai quando o aviso termina)."""
        for y, restante in self.avisos_fogo:
            if int(restante*10) % 2 == 0:
                for xx in range(0, LARGURA, 28):
                    pygame.draw.line(tela, (255, 120, 50), (xx, int(y)), (xx + 12, int(y)), 2)
                pygame.draw.polygon(tela, (255, 70, 40), [(LARGURA-58, int(y)-20),
                                                          (LARGURA-14, int(y)),
                                                          (LARGURA-58, int(y)+20)])

    def _desenhar_barra_rebites(self, tela):
        """"Barra de vida" do Kong: uma bolinha por rebite (dourada = coletado)."""
        total = self.rebites_total
        nome = self.fonte.render('REBITES', True, (255, 255, 255))
        tela.blit(nome, nome.get_rect(midbottom=(LARGURA//2, 118)))
        for i in range(total):
            x = LARGURA//2 + int((i - (total - 1)/2)*34)
            cor = (252, 206, 52) if i < self.rebites_coletados else (60, 60, 76)
            pygame.draw.circle(tela, cor, (x, 134), 11)
            pygame.draw.circle(tela, (255, 255, 255), (x, 134), 11, 2)
