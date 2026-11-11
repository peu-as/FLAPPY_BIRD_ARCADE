"""Mundo físico do Estilingue (pymunk): peças, dano, explosões e habilidades.

Não desenha nada: a sessão lê as peças e os eventos e o visual desenha.
Tudo acontece em passos fixos (SUBPASSOS por quadro), então a mesma
jogada dá sempre o mesmo resultado. Nada aqui usa o `random` do jogo.

Dano: cada batida gera um impulso; o que passa de IMPULSO_MINIMO vira dano
nas duas peças (blocos, insetos, chefes e barris; pássaros não sofrem dano).
"""
import math
from dataclasses import dataclass, field

import pymunk

from ...config import estilingue as cfg
from ...config.constants import Y_CHAO

BLOCO, INSETO, CHEFE, BARRIL, PASSARO = 'bloco', 'inseto', 'chefe', 'barril', 'passaro'

# medidas das peças dos módulos (px)
PILAR = (20, 86)
PILAR_CASINHA = (20, 64)
PILAR_FORTE = (24, 110)
PILAR_TOPO = (20, 70)
CAIXA = 40
ESPESSURA_TABUA = 18
RAIO_BARRIL = 24


@dataclass(eq=False)
class Peca:
    tipo: str
    corpo: pymunk.Body
    forma: pymunk.Shape
    vida: float = 1.0
    vida_max: float = 1.0
    material: str = ''                    # blocos
    tamanho: tuple = (0, 0)               # blocos: (largura, altura)
    raio: float = 0.0                     # círculos
    nome: str = ''                        # chefe: 'rei_inseto' / 'kong'; pássaro: tipo
    pontos: int = 0
    morta: bool = False
    # pássaros
    habilidade_usada: bool = False
    bateu: bool = False
    tempo_voo: float = 0.0
    tempo_parado: float = 0.0
    tempo_desde_batida: float = 0.0
    disparou: bool = False                # Semente-Foguete depois do clique
    filhote: bool = False                 # um dos três da Pena Dupla
    extras: dict = field(default_factory=dict)

    @property
    def posicao(self):
        return self.corpo.position

    @property
    def dano(self):
        """0 = inteiro, 1 = quase quebrando (para o desenho mostrar rachaduras)."""
        return 0.0 if self.vida_max <= 0 else max(0.0, 1 - self.vida / self.vida_max)


class Mundo:
    def __init__(self, casa):
        self.casa = casa
        self.space = pymunk.Space()
        self.space.gravity = (0, cfg.GRAVIDADE)
        self.space.iterations = cfg.ITERACOES
        self.space.sleep_time_threshold = 0.6
        self.space.collision_slop = 0.3
        self.pecas = []
        self.passaros_no_ar = []
        self.eventos = []                 # (tipo, dados) — a sessão consome a cada quadro
        self._por_forma = {}
        self._danos = {}
        self._explosoes = []
        self.tempo = 0.0
        # o segmento tem 2 px de raio: o centro fica 2 px abaixo para a superfície ser a linha do chão
        chao = pymunk.Segment(self.space.static_body, (-600, Y_CHAO + 2), (cfg.LARGURA_MUNDO + 600, Y_CHAO + 2), 2)
        chao.friction, chao.elasticity = 0.9, 0.05
        self.space.add(chao)
        self.space.on_collision(post_solve=self._depois_da_batida, begin=self._ao_tocar)
        self._montar()

    # ------------------------------------------------------------ montagem
    def _adicionar(self, peca):
        self.space.add(peca.corpo, peca.forma)
        self._por_forma[peca.forma] = peca
        self.pecas.append(peca)
        return peca

    def bloco(self, material, cx, base, largura, altura, angulo=0.0):
        """Bloco retangular apoiado em `base` (px acima do chão)."""
        m = cfg.MATERIAIS[material]
        corpo = pymunk.Body()
        corpo.position = (cx, Y_CHAO - base - altura / 2)
        corpo.angle = angulo
        forma = pymunk.Poly.create_box(corpo, (largura, altura))
        forma.density = m.densidade / 1000
        forma.friction, forma.elasticity = m.atrito, m.elasticidade
        return self._adicionar(Peca(BLOCO, corpo, forma, m.vida, m.vida, material, (largura, altura),
                                    pontos=m.pontos))

    def _circulo(self, tipo, cx, base, raio, densidade, vida, nome='', pontos=0):
        corpo = pymunk.Body()
        corpo.position = (cx, Y_CHAO - base - raio)
        forma = pymunk.Circle(corpo, raio)
        forma.density = densidade / 1000
        forma.friction, forma.elasticity = 0.7, 0.15
        return self._adicionar(Peca(tipo, corpo, forma, vida, vida, raio=raio, nome=nome, pontos=pontos))

    def inseto(self, cx, base):
        return self._circulo(INSETO, cx, base, cfg.RAIO_INSETO, 0.8, cfg.VIDA_INSETO, pontos=cfg.PONTOS_INSETO)

    def chefe(self, nome, cx, base):
        vida, raio, pontos = cfg.CHEFES[nome]
        return self._circulo(CHEFE, cx, base, raio, 1.2, vida, nome, pontos)

    def barril(self, cx, base=0):
        return self._circulo(BARRIL, cx, base, RAIO_BARRIL, 0.9, cfg.VIDA_BARRIL, pontos=cfg.PONTOS_BARRIL)

    def _montar(self):
        chefes = [c for c in self.casa.chefe.split('+') if c]
        for modulo, x, opcoes in self.casa.modulos:
            if modulo == 'fortaleza':
                getattr(self, '_m_fortaleza')(x, chefe=chefes.pop(0) if chefes else '', **opcoes)
            else:
                getattr(self, f'_m_{modulo}')(x, **opcoes)

    def _m_torre(self, x, andares, material, largura=100):
        pw, ph = PILAR
        base = 0
        for andar in range(andares):
            for lado in (-1, 1):
                self.bloco(material, x + lado * (largura / 2 - pw / 2), base, pw, ph)
            if andar == 0 and andares >= 2:
                self.inseto(x, base)                       # um no térreo, entre os pilares
            base += ph
            self.bloco(material, x, base, largura + 24, ESPESSURA_TABUA)
            base += ESPESSURA_TABUA
        self.inseto(x, base)                               # e um no topo

    def _m_casinha(self, x, material):
        pw, ph = PILAR_CASINHA
        for lado in (-1, 1):
            self.bloco(material, x + lado * 40, 0, pw, ph)
        self.bloco(material, x, ph, 112, ESPESSURA_TABUA)
        self.inseto(x, 0)

    def _m_piramide(self, x, niveis, material, alvos=1):
        for nivel in range(niveis):
            n = niveis - nivel
            for i in range(n):
                self.bloco(material, x + (i - (n - 1) / 2) * (CAIXA + 1), nivel * CAIXA, CAIXA, CAIXA)
        self.inseto(x, niveis * CAIXA)
        largura = niveis * (CAIXA + 1) / 2
        if alvos >= 2:
            self.inseto(x + largura + 26, 0)
        if alvos >= 3:
            self.inseto(x - largura - 26, 0)

    def _m_muro(self, x, altura, material):
        for i in range(altura):
            self.bloco(material, x, i * CAIXA, CAIXA, CAIXA)

    def _m_barril(self, x):
        self.barril(x)

    def _m_fortaleza(self, x, material, chefe='', barris=False):
        pw, ph = PILAR_FORTE
        for lado in (-1, 1):
            self.bloco(material, x + lado * 70, 0, pw, ph)
        if chefe:
            self.chefe(chefe, x, 0)
        else:
            self.inseto(x, 0)
        self.bloco(material, x, ph, 188, 20)
        tw, th = PILAR_TOPO
        for lado in (-1, 1):
            self.bloco(material, x + lado * 50, ph + 20, tw, th)
        self.inseto(x, ph + 20)
        self.bloco(material, x, ph + 20 + th, 140, ESPESSURA_TABUA)
        self.inseto(x, ph + 20 + th + ESPESSURA_TABUA)
        if barris:
            for lado in (-1, 1):
                self.barril(x + lado * 122)

    # ------------------------------------------------------------ pássaros
    def lancar(self, tipo, posicao, velocidade, escala=1.0, filhote=False):
        t = cfg.PASSAROS[tipo]
        corpo = pymunk.Body()
        corpo.position = posicao
        raio = t.raio * escala
        forma = pymunk.Circle(corpo, raio)
        forma.density = t.massa * escala ** 2 / (math.pi * raio * raio)
        forma.friction, forma.elasticity = 0.6, 0.25
        corpo.velocity = velocidade
        peca = self._adicionar(Peca(PASSARO, corpo, forma, raio=raio, nome=tipo, filhote=filhote,
                                    habilidade_usada=filhote or tipo == 'comum'))
        self.passaros_no_ar.append(peca)
        self.eventos.append(('lancou', peca))
        return peca

    def pode_ativar(self, passaro):
        if passaro.morta or passaro.habilidade_usada:
            return False
        return passaro.nome == 'ovo' or not passaro.bateu

    def ativar(self, passaro):
        """Clique no ar: a habilidade do pássaro (uma vez só)."""
        if not self.pode_ativar(passaro):
            return False
        passaro.habilidade_usada = True
        v = passaro.corpo.velocity
        if passaro.nome == 'pena':
            pos = passaro.corpo.position
            self._remover(passaro)
            for graus in (-cfg.PENA_ABERTURA, 0, cfg.PENA_ABERTURA):
                self.lancar('pena', pos + v.rotated_degrees(graus).normalized() * (graus / 2),
                            v.rotated_degrees(graus), escala=cfg.PENA_ESCALA, filhote=True)
        elif passaro.nome == 'foguete':
            direcao = v.normalized() if v.length > 1 else pymunk.Vec2d(1, 0)
            passaro.corpo.velocity = direcao * cfg.FOGUETE_VELOCIDADE
            passaro.disparou = True
        elif passaro.nome == 'ovo':
            self._explodir(passaro.corpo.position, cfg.ESCALA_EXPLOSAO_OVO)
            self._remover(passaro)
        self.eventos.append(('habilidade', passaro))
        return True

    # ------------------------------------------------------------ colisões
    def _ao_tocar(self, arbiter, space, dados):
        for forma in arbiter.shapes:
            peca = self._por_forma.get(forma)
            if peca is not None and peca.tipo == PASSARO and not peca.bateu:
                peca.bateu = True
                self.eventos.append(('bateu', peca))

    def _depois_da_batida(self, arbiter, space, dados):
        impulso = arbiter.total_impulse.length
        if impulso <= cfg.IMPULSO_MINIMO:
            return
        dano = (impulso - cfg.IMPULSO_MINIMO) * cfg.DANO_POR_IMPULSO
        a, b = (self._por_forma.get(f) for f in arbiter.shapes)
        for alvo, outro in ((a, b), (b, a)):
            if alvo is None or alvo.tipo == PASSARO or alvo.morta:
                continue
            fator = 1.0
            if (outro is not None and outro.tipo == PASSARO and outro.disparou
                    and alvo.material == 'madeira'):
                fator = cfg.FOGUETE_MULTIPLICADOR_MADEIRA
            self._danos[alvo] = self._danos.get(alvo, 0.0) + dano * fator

    # ------------------------------------------------------------ passo
    def passo(self, dt):
        """Um quadro do jogo: SUBPASSOS passos de física + dano + explosões."""
        sub = dt / cfg.SUBPASSOS
        for _ in range(cfg.SUBPASSOS):
            self.space.step(sub)
            self._aplicar_danos()
        self.tempo += dt
        for p in list(self.passaros_no_ar):
            self._cuidar_do_passaro(p, dt)
        for peca in self.pecas:                  # saiu do mundo = derrubado (como no original)
            if not peca.morta and peca.tipo != PASSARO and self._fora(peca.corpo.position):
                self._remover(peca)
                self.eventos.append(('quebrou', peca))

    @staticmethod
    def _fora(posicao):
        x, y = posicao
        return x < -150 or x > cfg.LARGURA_MUNDO + 250 or y > Y_CHAO + 150

    def _aplicar_danos(self):
        while self._danos or self._explosoes:
            danos, self._danos = self._danos, {}
            for peca, dano in danos.items():
                self.ferir(peca, dano)
            explosoes, self._explosoes = self._explosoes, []
            for centro, escala in explosoes:
                self._explosao_agora(centro, escala)

    def ferir(self, peca, dano):
        if peca.morta or peca.tipo == PASSARO:
            return
        peca.vida -= dano
        if peca.vida <= 0:
            self._remover(peca)
            self.eventos.append(('quebrou', peca))
            if peca.tipo == BARRIL:
                self._explodir(peca.corpo.position, 1.0)

    def _explodir(self, centro, escala):
        self._explosoes.append((pymunk.Vec2d(*centro), escala))

    def _explosao_agora(self, centro, escala):
        raio = cfg.RAIO_EXPLOSAO * escala
        self.eventos.append(('explodiu', (centro, raio)))
        for peca in list(self.pecas):
            if peca.morta or peca.tipo == PASSARO:
                continue
            delta = peca.corpo.position - centro
            distancia = max(1.0, delta.length - (peca.raio or max(peca.tamanho) / 2))
            if distancia >= raio:
                continue
            fator = 1 - distancia / raio
            empurrao = delta.normalized() * cfg.IMPULSO_EXPLOSAO * fator * escala
            peca.corpo.activate()
            peca.corpo.apply_impulse_at_world_point(empurrao * min(1.0, peca.corpo.mass / 6) ** 0.5,
                                                    peca.corpo.position)
            self.ferir(peca, cfg.DANO_EXPLOSAO * fator * escala)

    def _cuidar_do_passaro(self, p, dt):
        if p.morta:
            self.passaros_no_ar.remove(p)
            return
        p.tempo_voo += dt
        if p.bateu:
            p.tempo_desde_batida += dt
        if p.nome == 'ovo' and p.bateu and not p.habilidade_usada and p.tempo_desde_batida >= cfg.OVO_ESPERA_APOS_BATER:
            self.ativar(p)
            return
        x, y = p.corpo.position
        p.tempo_parado = p.tempo_parado + dt if p.corpo.velocity.length < 25 else 0.0
        rolando_demais = p.bateu and p.tempo_desde_batida > cfg.TEMPO_DEPOIS_DE_BATER
        ovo_armado = p.nome == 'ovo' and not p.habilidade_usada          # ainda vai explodir
        cansou = not ovo_armado and (p.tempo_parado > 1.0 or rolando_demais or p.tempo_voo > cfg.LIMITE_JOGADA)
        if self._fora((x, y)) or cansou:
            self._remover(p)
            self.eventos.append(('sumiu', p))

    def _remover(self, peca):
        if peca.morta:
            return
        peca.morta = True
        self.space.remove(peca.corpo, peca.forma)
        self._por_forma.pop(peca.forma, None)
        if peca in self.passaros_no_ar:
            self.passaros_no_ar.remove(peca)

    # ------------------------------------------------------------ consultas
    def vivos(self, *tipos):
        return [p for p in self.pecas if not p.morta and p.tipo in tipos]

    @property
    def alvos(self):
        return self.vivos(INSETO, CHEFE)

    def em_movimento(self):
        """Alguma coisa ainda se mexendo (ou pássaro no ar, ou explosão pendente)?"""
        if self.passaros_no_ar or self._explosoes:
            return True
        return any(not p.corpo.is_sleeping and p.corpo.velocity.length > cfg.VELOCIDADE_CALMA
                   for p in self.pecas if not p.morta)

    def consumir_eventos(self):
        eventos, self.eventos = self.eventos, []
        return eventos
