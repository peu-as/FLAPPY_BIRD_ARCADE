"""Sprites desenhados por código (tema Donkey Kong e chefões).

Nenhum PNG novo: tudo é feito com pygame.draw em escala maior e reduzido com
suavização, o que dá bordas limpas.
"""
import math
import random

import pygame

from ..config.constants import ALTURA, LARGURA, Y_CHAO


# Os sprites abaixo são DESENHADOS POR CÓDIGO (pygame.draw), sem arquivos
# PNG novos: a fase funciona com os mesmos assets que o jogo já tem.
# Truque de qualidade: desenha-se em escala maior e reduz-se com
# smoothscale (supersampling), o que suaviza as bordas serrilhadas.
COR_MADEIRA       = (176, 98, 38)

COR_MADEIRA_ESC   = (96, 50, 18)

COR_AROS          = (70, 72, 84)

COR_AROS_BRILHO   = (150, 154, 170)

COR_PELO_KONG     = (98, 56, 28)

COR_FACE_KONG     = (224, 168, 114)

def _barril_lateral(superficie, ret):
    """Barril visto de lado (em pé): corpo de madeira, tábuas e dois aros."""
    pygame.draw.rect(superficie, COR_MADEIRA_ESC, ret, border_radius=16)
    pygame.draw.rect(superficie, COR_MADEIRA, ret.inflate(-6, -6), border_radius=14)
    for fracao in (0.25, 0.5, 0.75):                 # tábuas
        x = ret.left + int(ret.width*fracao)
        pygame.draw.line(superficie, COR_MADEIRA_ESC, (x, ret.top+6), (x, ret.bottom-6), 2)
    for fracao in (0.2, 0.8):                        # aros metálicos
        y = ret.top + int(ret.height*fracao)
        pygame.draw.rect(superficie, COR_AROS, (ret.left+1, y-5, ret.width-2, 10), border_radius=3)
        pygame.draw.line(superficie, COR_AROS_BRILHO, (ret.left+5, y-3), (ret.right-6, y-3), 2)
    pygame.draw.line(superficie, (226, 156, 86), (ret.left+10, ret.top+16),
                     (ret.left+10, ret.bottom-16), 3)   # brilho

def criar_pilha_barris(largura=96, altura=350):
    """Pilha de barris em pé. O topo da imagem é o topo da pilha; o que passa
    do chão fica escondido pelo desenho do chão."""
    sup = pygame.Surface((largura, altura), pygame.SRCALPHA)
    alt_barril = 70
    for i in range(-(-altura//alt_barril)):          # divisão com arredondamento p/ cima
        _barril_lateral(sup, pygame.Rect(0, i*alt_barril, largura, alt_barril))
    return sup

def criar_cipo(largura=96, altura=420):
    """Cipó pendurado do teto: dois fios trançados, folhas e um tufo na ponta.
    A ponta (parte de baixo da imagem) é a que fica junto à passagem."""
    sup = pygame.Surface((largura, altura), pygame.SRCALPHA)
    meio = largura//2
    verde_esc, verde, verde_claro = (22, 84, 38), (38, 128, 56), (84, 190, 92)
    for y in range(0, altura-30, 3):                 # dois fios que se cruzam (seno)
        dx = 11*math.sin(y/26)
        pygame.draw.circle(sup, verde_esc, (int(meio+dx), y), 8)
        pygame.draw.circle(sup, verde, (int(meio-dx), y), 7)
    for i, y in enumerate(range(50, altura-80, 64)): # folhas laterais alternadas
        lado = -1 if i % 2 == 0 else 1
        folha = pygame.Rect(0, 0, 38, 17)
        folha.center = (meio + lado*26, y)
        pygame.draw.ellipse(sup, verde_claro, folha)
        pygame.draw.ellipse(sup, verde_esc, folha, 2)
    base = altura-34                                 # tufo de folhas na ponta
    for ang in (-62, -31, 0, 31, 62):
        a = math.radians(ang)
        raiz = (meio, base-14)
        ponta = (meio + 44*math.sin(a), base + 40*math.cos(a))
        centro = ((raiz[0]+ponta[0])/2, (raiz[1]+ponta[1])/2)
        # Folha = losango: raiz, dois pontos laterais (perpendiculares ao eixo), ponta.
        eixo = (ponta[0]-raiz[0], ponta[1]-raiz[1])
        comp = math.hypot(*eixo)
        normal = (-eixo[1]/comp*11, eixo[0]/comp*11)
        pontos = [raiz, (centro[0]+normal[0], centro[1]+normal[1]), ponta,
                  (centro[0]-normal[0], centro[1]-normal[1])]
        pygame.draw.polygon(sup, verde_claro, pontos)
        pygame.draw.polygon(sup, verde_esc, pontos, 2)
    pygame.draw.circle(sup, verde, (meio, base), 12)
    pygame.draw.circle(sup, verde_esc, (meio, base), 12, 2)
    return sup

def criar_barril_rolante(diametro=52):
    """Barril visto de frente (o "fundo" redondo), como nos barris rolantes do
    arcade. Cunhas de cores alternadas deixam a rotação visível."""
    k = 4                                            # fator de supersampling
    D = diametro*k
    sup = pygame.Surface((D, D), pygame.SRCALPHA)
    c, r = D//2, D//2
    pygame.draw.circle(sup, COR_AROS, (c, c), r)                 # aro metálico
    pygame.draw.circle(sup, COR_AROS_BRILHO, (c, c), r, 2*k)
    r_int = r - 4*k
    for i in range(8):                                           # cunhas de madeira
        a0, a1 = math.radians(i*45), math.radians(i*45+45)
        pontos = [(c, c)] + [(c + r_int*math.cos(a0 + (a1-a0)*t/6),
                              c + r_int*math.sin(a0 + (a1-a0)*t/6)) for t in range(7)]
        pygame.draw.polygon(sup, COR_MADEIRA if i % 2 == 0 else (150, 80, 30), pontos)
    pygame.draw.circle(sup, COR_MADEIRA_ESC, (c, c), r_int, 2*k)
    pygame.draw.circle(sup, COR_AROS, (c, c), 5*k)               # cubo central
    return pygame.transform.smoothscale(sup, (diametro, diametro))

def criar_banana(tamanho=44):
    """Banana em forma de meia-lua (polígono entre duas curvas elípticas)."""
    k = 4
    T = tamanho*k
    sup = pygame.Surface((T, T), pygame.SRCALPHA)
    cx, cy, rx, ry, esp = T/2, T*0.25, T*0.42, T*0.50, T*0.20
    n = 24
    borda_cima, borda_baixo = [], []
    for i in range(n+1):
        u = i/n
        ang = math.radians(205 + 130*u)              # arco inferior (sorriso)
        afina = math.sin(math.pi*u)                  # 0 nas pontas, 1 no meio
        borda_cima.append((cx + rx*math.cos(ang), cy - ry*math.sin(ang)))
        borda_baixo.append((cx + rx*math.cos(ang), cy - (ry + esp*afina)*math.sin(ang)))
    pontos = borda_cima + borda_baixo[::-1]
    pygame.draw.polygon(sup, (255, 224, 56), pontos)
    pygame.draw.polygon(sup, (150, 100, 12), pontos, 2*k)
    for ponta in (borda_cima[0], borda_cima[-1]):    # pontinhas escuras
        pygame.draw.circle(sup, (84, 52, 12), (int(ponta[0]), int(ponta[1])), 2*k)
    return pygame.transform.smoothscale(sup, (tamanho, tamanho))

def criar_kong(lancando, com_barril=True):
    """Donkey Kong de corpo inteiro (150x170 px).

    lancando=False: braços baixos (parado).
    lancando=True : braços erguidos; com_barril=True segura um barril sobre a
                    cabeça (preparo do arremesso) e com_barril=False está de
                    mãos vazias (acabou de arremessar).
    """
    k = 3
    L, A, oy = 150, 170, 30                          # tamanho final e deslocamento vertical
    sup = pygame.Surface((L*k, A*k), pygame.SRCALPHA)

    def P(x, y):                                     # ponto no espaço final -> espaço ampliado
        return (int(x*k), int((y+oy)*k))
    def elipse(cx, cy, w, h, cor):
        pygame.draw.ellipse(sup, cor, pygame.Rect(P(cx-w/2, cy-h/2), (int(w*k), int(h*k))))
    def braco(ombro, mao):
        pygame.draw.line(sup, COR_PELO_KONG, P(*ombro), P(*mao), 22*k)
        pygame.draw.circle(sup, COR_PELO_KONG, P(*mao), 13*k)
        pygame.draw.circle(sup, COR_PELO_KONG, P(*ombro), 11*k)

    pes_cor = (66, 36, 16)
    elipse(48, 128, 40, 18, pes_cor)                 # pés
    elipse(102, 128, 40, 18, pes_cor)
    elipse(75, 92, 100, 80, COR_PELO_KONG)           # tronco
    elipse(75, 99, 58, 48, COR_FACE_KONG)            # peito
    pygame.draw.polygon(sup, (206, 34, 34), [P(68, 80), P(82, 80), P(80, 88), P(86, 112),
                                             P(75, 121), P(64, 112), P(70, 88)])   # gravata
    pygame.draw.line(sup, (255, 214, 60), P(70, 100), P(80, 100), 2*k)             # "DK" estilizado
    pygame.draw.line(sup, (255, 214, 60), P(70, 106), P(80, 106), 2*k)
    if lancando:
        braco((34, 70), (50, 10))      # mãos nos cantos de baixo do barril,
        braco((116, 70), (100, 10))    # fora da cabeça (que vai de x=41 a 109)
    else:
        braco((34, 70), (17, 114))
        braco((116, 70), (133, 114))
    elipse(75, 44, 68, 58, COR_PELO_KONG)            # cabeça
    pygame.draw.polygon(sup, (70, 38, 16), [P(62, 20), P(67, 8), P(74, 17), P(80, 6), P(86, 20)])  # topete
    elipse(75, 52, 48, 38, COR_FACE_KONG)            # máscara da face
    elipse(75, 33, 52, 14, (70, 38, 16))             # sobrancelha
    for cx in (65, 85):                              # olhos
        elipse(cx, 43, 14, 13, (255, 255, 255))
        pygame.draw.circle(sup, (0, 0, 0), P(cx, 44), 3*k)
    pygame.draw.line(sup, (60, 30, 12), P(55, 33), P(71, 41), 4*k)   # cenho
    pygame.draw.line(sup, (60, 30, 12), P(95, 33), P(79, 41), 4*k)
    for cx in (71, 79):                              # narinas
        pygame.draw.circle(sup, (90, 50, 24), P(cx, 53), 2*k)
    elipse(75, 62, 28, 11, (120, 24, 24))            # boca
    pygame.draw.rect(sup, (255, 255, 255), pygame.Rect(P(65, 57), (20*k, 4*k)))
    if lancando and com_barril:                                     # barril acima da cabeça
        barril = pygame.Rect(P(50, -30), (50*k, 40*k))
        _barril_lateral(sup, barril)
    return pygame.transform.smoothscale(sup, (L, A))

def criar_fundo_selva():
    """Céu noturno em degradê (roxo -> verde-selva), estrelas e lua. É estático:
    a sensação de movimento vem das camadas de palmeiras e do chão."""
    sup = pygame.Surface((LARGURA, ALTURA))
    topo, base = (16, 8, 48), (12, 78, 66)
    for y in range(ALTURA):
        t = y/(ALTURA-1)
        pygame.draw.line(sup, tuple(int(a+(b-a)*t) for a, b in zip(topo, base)),
                         (0, y), (LARGURA, y))
    rnd = random.Random(7)                           # semente fixa: sempre o mesmo céu
    for _ in range(70):
        pygame.draw.circle(sup, (225, 225, 255),
                           (rnd.randrange(LARGURA), rnd.randrange(30, 430)), rnd.choice((1, 1, 2)))
    halo = pygame.Surface((220, 220), pygame.SRCALPHA)
    pygame.draw.circle(halo, (250, 240, 190, 40), (110, 110), 100)
    pygame.draw.circle(halo, (250, 240, 190, 60), (110, 110), 72)
    sup.blit(halo, (110-110, 190-110))
    pygame.draw.circle(sup, (252, 246, 205), (110, 190), 40)
    pygame.draw.circle(sup, (232, 222, 178), (96, 180), 8)       # crateras
    pygame.draw.circle(sup, (232, 222, 178), (124, 204), 6)
    return sup

def _palmeira(superficie, x, y_base, altura, cor, inclinacao):
    """Silhueta de palmeira: tronco levemente inclinado + folhas em leque."""
    topo = (x + inclinacao, y_base - altura)
    pygame.draw.polygon(superficie, cor, [(x-8, y_base), (x+8, y_base),
                                          (topo[0]+3, topo[1]), (topo[0]-3, topo[1])])
    comp = altura*0.42
    for ang in (15, 45, 80, 100, 135, 165, 195, 345):
        a = math.radians(ang)
        direcao = (math.cos(a), -math.sin(a))
        ponta = (topo[0] + direcao[0]*comp, topo[1] + direcao[1]*comp + comp*0.38)
        meio = ((topo[0]+ponta[0])/2, (topo[1]+ponta[1])/2 - comp*0.12)
        normal = (-direcao[1]*comp*0.13, direcao[0]*comp*0.13)
        pygame.draw.polygon(superficie, cor, [topo, (meio[0]+normal[0], meio[1]+normal[1]),
                                              ponta, (meio[0]-normal[0], meio[1]-normal[1])])

def criar_camada_palmeiras(cor, altura_min, altura_max, quantidade, semente):
    """Faixa de palmeiras com largura LARGURA que se repete SEM emenda: cada
    árvore é desenhada também deslocada de ±LARGURA, então o que sai por uma
    borda entra pela outra durante a rolagem (parallax)."""
    sup = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    rnd = random.Random(semente)
    for i in range(quantidade):
        x = (i + rnd.uniform(0.25, 0.75))*LARGURA/quantidade
        altura = rnd.randint(altura_min, altura_max)
        inclinacao = rnd.randint(-30, 30)
        for deslocamento in (-LARGURA, 0, LARGURA):
            _palmeira(sup, x+deslocamento, Y_CHAO+10, altura, cor, inclinacao)
    return sup

def criar_viga(largura=96, altura=100):
    """Trecho de viga de aço vermelha (marca registrada do Donkey Kong), com
    vigas cruzadas em "X". Encaixa horizontalmente sem emendas (tiling)."""
    sup = pygame.Surface((largura, altura))
    sup.fill((24, 10, 24))                           # vãos escuros entre as vigas
    vermelho, claro, escuro = (208, 54, 62), (246, 124, 124), (122, 24, 36)
    pygame.draw.line(sup, vermelho, (0, 16), (largura, altura-16), 11)
    pygame.draw.line(sup, vermelho, (largura, 16), (0, altura-16), 11)
    pygame.draw.rect(sup, vermelho, (0, 0, largura, 18))
    pygame.draw.rect(sup, claro, (0, 0, largura, 5))
    pygame.draw.rect(sup, escuro, (0, 15, largura, 3))
    pygame.draw.rect(sup, vermelho, (0, altura-18, largura, 18))
    pygame.draw.rect(sup, escuro, (0, altura-18, largura, 3))
    for x in (12, largura-12):                       # rebites
        pygame.draw.circle(sup, claro, (x, 9), 3)
        pygame.draw.circle(sup, claro, (x, altura-9), 3)
    return sup

def tingir(sprite, cor):
    """Cópia do sprite com 'cor' somada aos canais RGB (clareia/avermelha)
    sem mexer na transparência. Usado no flash do chefão e no Kong furioso."""
    copia = sprite.copy()
    copia.fill(tuple(cor) + (0,), special_flags=pygame.BLEND_RGB_ADD)
    return copia

def criar_chefe_galaga(largura=150, altura=118):
    """"Boss Galaga" desenhado por código: inseto verde de asas roxas, olhos
    amarelos e mandíbulas (inspirado no chefe do Galaga original).
    Devolve (sprite normal, sprite "flash" mais claro, usado ao levar um tiro)."""
    k = 3                                                  # supersampling
    sup = pygame.Surface((largura*k, altura*k), pygame.SRCALPHA)
    cx = largura/2
    def pts(lista):
        return [(int(x*k), int(y*k)) for x, y in lista]
    def ret(x, y, w, h):
        return pygame.Rect(int(x*k), int(y*k), int(w*k), int(h*k))
    roxo, roxo_esc = (126, 82, 220), (66, 36, 140)
    verde, verde_esc, verde_cl = (70, 196, 104), (30, 118, 62), (158, 236, 168)
    for lado in (-1, 1):                                   # asas e manchas
        asa = pts([(cx+lado*18, 42), (cx+lado*70, 6), (cx+lado*73, 66),
                   (cx+lado*54, 104), (cx+lado*20, 84)])
        pygame.draw.polygon(sup, roxo, asa)
        pygame.draw.polygon(sup, roxo_esc, asa, 2*k)
        for mx, my in ((46, 30), (54, 52), (46, 76)):
            pygame.draw.circle(sup, (235, 70, 80), (int((cx+lado*mx)*k), int(my*k)), 5*k)
    pygame.draw.ellipse(sup, verde, ret(cx-34, 34, 68, 78))             # corpo
    pygame.draw.ellipse(sup, verde_esc, ret(cx-34, 34, 68, 78), 2*k)
    pygame.draw.ellipse(sup, verde_cl, ret(cx-20, 58, 40, 46))          # barriga
    for i in range(3):
        y = 68 + i*11
        pygame.draw.line(sup, verde, pts([(cx-15, y)])[0], pts([(cx+15, y)])[0], k)
    pygame.draw.ellipse(sup, verde, ret(cx-30, 8, 60, 46))              # cabeça
    pygame.draw.ellipse(sup, verde_esc, ret(cx-30, 8, 60, 46), 2*k)
    for lado in (-1, 1):
        base, ponta = pts([(cx+lado*12, 12)])[0], pts([(cx+lado*26, 3)])[0]
        pygame.draw.line(sup, verde_esc, base, ponta, 2*k)              # antenas
        pygame.draw.circle(sup, (250, 220, 90), ponta, 3*k)
        olho = (int((cx+lado*14)*k), int(30*k))
        pygame.draw.circle(sup, (255, 232, 70), olho, 9*k)              # olhos
        pygame.draw.circle(sup, (200, 30, 40), olho, 4*k)
        pygame.draw.circle(sup, (255, 255, 255), (olho[0]-k, olho[1]-k), k)
        pygame.draw.polygon(sup, (250, 222, 96),                        # mandíbulas
                            pts([(cx+lado*4, 48), (cx+lado*17, 50), (cx+lado*10, 70)]))
    normal = pygame.transform.smoothscale(sup, (largura, altura))
    return normal, tingir(normal, (110, 110, 110))

def criar_rebite(tamanho=44):
    """Rebite dourado (cabeça redonda com fenda em cruz): o "ponto fraco"
    do Kong furioso, em referência à fase dos rebites do Donkey Kong original."""
    k = 3
    s = tamanho*k
    sup = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s//2
    pygame.draw.circle(sup, (96, 66, 10), (c, c), c-1)
    pygame.draw.circle(sup, (252, 206, 52), (c, c), c - 3*k)
    pygame.draw.circle(sup, (255, 242, 160), (c - c//3, c - c//3), c//3)
    pygame.draw.line(sup, (128, 90, 16), (c - c//2, c), (c + c//2, c), 2*k)
    pygame.draw.line(sup, (128, 90, 16), (c, c - c//2), (c, c + c//2), 2*k)
    return pygame.transform.smoothscale(sup, (tamanho, tamanho))

def criar_bola_fogo(largura=64, altura=44):
    """"Chama viva" do Donkey Kong: cabeça de fogo com olhos e cauda de
    chamas para a direita (ela voa para a esquerda)."""
    k = 3
    sup = pygame.Surface((largura*k, altura*k), pygame.SRCALPHA)
    def pts(lista):
        return [(int(x*k), int(y*k)) for x, y in lista]
    pygame.draw.polygon(sup, (210, 50, 30), pts([(24, 4), (62, 14), (44, 22), (62, 30), (24, 40)]))
    pygame.draw.polygon(sup, (255, 140, 30), pts([(24, 9), (52, 17), (40, 22), (52, 27), (24, 35)]))
    pygame.draw.circle(sup, (255, 140, 30), (22*k, 22*k), 18*k)
    pygame.draw.circle(sup, (255, 212, 80), (22*k, 24*k), 12*k)
    for ex in (15, 28):
        pygame.draw.circle(sup, (255, 255, 255), (ex*k, 19*k), 4*k)
        pygame.draw.circle(sup, (20, 20, 20), ((ex-1)*k, 20*k), 2*k)
    return pygame.transform.smoothscale(sup, (largura, altura))
