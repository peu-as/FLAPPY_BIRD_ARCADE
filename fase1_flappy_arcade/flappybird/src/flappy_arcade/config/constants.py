"""Constantes do jogo: física, dificuldade, fases especiais e interface.

Valores em pixels da superfície lógica (575x860) e em quadros (30 FPS).
Alterar um valor aqui altera a jogabilidade: a física original depende deles.

Ciclo de cada nível no jogo clássico:
  1) uma fase especial (Donkey Kong ou Galaga) no próximo múltiplo de 35 pontos,
     terminando em um chefão;
  2) a outra fase especial, no múltiplo de 35 seguinte;
  3) a fase dos pássaros, 20 pontos depois das duas especiais.
  Ao fim dela o nível sobe. Concluir o nível 10 mostra a tela de Honra Máxima.
"""

# As coordenadas são expressas em pixels da superfície lógica.
# FPS indica quantos quadros são processados por segundo.
LARGURA, ALTURA, FPS = 575, 860, 30

FATOR_TELA = 0.85

# IMPULSO negativo faz o pássaro subir: no Pygame, y cresce para baixo.
# GRAVIDADE é uma variação de velocidade por quadro, em px/quadro²;
# não representa diretamente a aceleração gravitacional em m/s².
GRAVIDADE, IMPULSO = 1.1, -8

VELOCIDADE_CANOS, VELOCIDADE_CHAO = 4, 4

# ABERTURA_CANOS é a passagem vertical entre os obstáculos.
# ESPACO_ENTRE_CANOS determina o espaçamento horizontal de geração.
ABERTURA_CANOS, ESPACO_ENTRE_CANOS = 290, 300

VIDAS_INICIAIS = 6

TEMPO_TEMA = 20

TEMPO_INVULNERAVEL_MS = 1200

USAR_MASCARAS = True

# Níveis e dificuldade progressiva (modo clássico)
# A dificuldade segue o NÍVEL (1 a NIVEL_MAXIMO) = o ciclo em que o jogador está. Cada nível tem a
# sua gravidade, abertura entre os canos e velocidade (veja parametros_nivel).
# As fases especiais usam a tabela do mesmo nível, mas com regras próprias
# (parametros_galaga e parametros_donkey).
NIVEL_MAXIMO = 10

GRAVIDADE_POR_NIVEL = 0.06     # px/quadro² a mais por nível   (1,10 -> 1,64)

ABERTURA_POR_NIVEL = 11        # px a menos de passagem por nível (290 -> 191)

VELOCIDADE_POR_NIVEL = 0.15    # px/quadro a mais por nível (canos e chão: 4,0 -> 5,35)

# Compensação do impulso: a altura de um bater de asas é v²/(2g). Se só a
# gravidade subisse, o pássaro subiria cada vez menos por toque. O impulso
# cresce na proporção (g/g0)**COMPENSACAO_IMPULSO para a dificuldade subir
# sem tornar o jogo injusto. Use 0 para desligar a compensação.
COMPENSACAO_IMPULSO = 0.35

MAX_ICONES_VIDA = 8            # acima disso, as vidas viram "ícone + xN"

# Ciclo de cada nível (veja o resumo no topo do arquivo).
PONTOS_ENTRE_ESPECIAIS = 35    # as fases especiais aparecem nos múltiplos de 35 pontos

PONTOS_ANTES_PASSAROS = 20     # pontos, após as duas especiais, para liberar a fase dos pássaros

# Ritmo humano usado no cálculo de justiça das passagens (veja
# desvio_maximo_passagem): 6 toques por segundo a 30 FPS = 1 toque a cada 5 quadros.
QUADROS_ENTRE_TOQUES = 5

# Parâmetros da fase GALAGA
# Diferente do Flappy (que usa px/quadro), a fase Galaga usa
# velocidades em px/segundo multiplicadas por dt. Assim o movimento
# não depende de quantos quadros por segundo o computador consegue.
TEMPO_GALAGA = 60         # duração máxima da fase, em segundos

TAMANHO_INIMIGO = 46      # maior lado (px) do sprite de cada inimigo

TAMANHO_NAVE = 60         # maior lado (px) do sprite da nave

VELOCIDADE_NAVE = 380     # px/s — movimento horizontal da nave

VELOCIDADE_TIRO = 560     # px/s — tiro do jogador (sobe)

VELOCIDADE_TIRO_INIMIGO = 280  # px/s — tiro dos inimigos (desce)

INTERVALO_TIRO = 0.22     # s mínimos entre dois tiros do jogador

MAX_TIROS_JOGADOR = 3     # tiros do jogador simultâneos na tela

# As fases especiais não somam pontos ao placar: valem vidas extras
# (veja VIDAS_POR_FASE_ESPECIAL).
COLUNAS_GALAGA = 7        # colunas da formação (linhas: 3 a 5 conforme o nível)

ESPACO_COL, ESPACO_LIN = 64, 58   # distância entre inimigos (px)

Y_FORMACAO = 175          # y da primeira linha da formação

Y_NAVE = ALTURA - 120     # y fixo da nave (a nave só anda na horizontal)

# Sistema de fases especiais por pontuação
# As fases especiais agora ocorrem a cada múltiplo de
# PONTOS_ENTRE_ESPECIAIS (35, 70, 105...) e cada ciclo (nível) tem exatamente
# duas delas (Galaga e Donkey Kong), seguidas da fase dos pássaros. Isto
# substitui PONTOS_PRIMEIRA_ESPECIAL e INTERVALO_ESPECIAL (50, 150, 250...).
TEMPO_ALERTA = 5.0        # s de aviso/contagem regressiva antes da fase

# Ordem das duas fases especiais de cada ciclo: nos níveis ímpares começa pelo
# Donkey Kong; nos pares, pela Galaga (veja ClassicSession.ordem_especiais).
ORDEM_FASES_ESPECIAIS = ('DONKEY', 'GALAGA')

# Texto do alerta de cada variante: (nome, dica, cor do nome).
NOMES_FASES = {
    'GALAGA': ('GALAGA', 'Derrube a formação e enfrente o CHEFÃO!', (90, 220, 255)),
    'DONKEY': ('DONKEY KONG', 'Desvie dos barris e derrote o KONG!', (255, 150, 40)),
    'PASSAROS': ('FASE DOS PÁSSAROS', 'Passe entre os pássaros: vale pontos!', (255, 225, 90)),
}

# Estados em que a partida está "rodando" (valem pausa, placar, etc.).
ESTADOS_ATIVOS = ('JOGO', 'ALERTA', 'GALAGA', 'DONKEY')

# As fases especiais são BÔNUS: não somam pontos ao placar.
# Em troca, COMPLETAR a fase (Galaga: derrubar toda a formação; Donkey Kong:
# sobreviver até o fim da travessia) dá vidas extras. Se o tempo da Galaga
# esgotar sem concluí-la, não há vida extra.
VIDAS_POR_FASE_ESPECIAL = 1

# Parâmetros da fase DONKEY KONG
# Esta fase mantém a física do Flappy (px/quadro), mas troca os canos
# por cipós + pilhas de barris, e ajusta a dinâmica de leve:
# - rolagem 25% mais rápida e abertura um pouco maior (compensa);
# - Kong arremessa barris em ARCO ALTO entre as pilhas;
# - bananas no meio das passagens são coletáveis (só um contador:).
Y_CHAO = ALTURA - 100     # topo do chão (mesmo valor usado na classe Chao)

TEMPO_DONKEY = 45         # duração da fase, em segundos

VELOCIDADE_DONKEY = 5     # px/quadro (o Flappy normal usa VELOCIDADE_CANOS = 4)

ABERTURA_DONKEY = 300     # passagem vertical (o normal usa ABERTURA_CANOS = 290)

# As bananas são só um contador da fase; o bônus é +1 vida.
CHANCE_BARRIL = 0.5       # probabilidade de haver barril entre duas pilhas (sobe com o nível)

# Kong ARREMESSA o barril para o alto. O barril sai das mãos do Kong, sobe em parábola e passa
# pelo pássaro no ponto mais alto do arco, na altura da passagem seguinte
# (± DESVIO_APICE_BARRIL px). Ali ele "paira": o jogador precisa escolher entre
# passar por cima ou por baixo dele, sem errar a faixa. Como o ápice acompanha a
# passagem, sempre sobra espaço para os dois lados (a fase continua justa).
DESVIO_APICE_BARRIL = 25  # px de variação do ápice em torno do centro da passagem

FRAMES_ANTECIPACAO_KONG = 14   # quadros (~0,5 s) em que Kong ergue o barril antes de soltar

# Chefões. Cada fase especial termina com um chefão (veja ChefeGalaga e
# FaseDonkey._atualizar_chefe). Se o tempo do chefão esgotar, ele "foge": a fase
# termina sem a vida extra.
TEMPO_CHEFE_GALAGA = 90   # s

TEMPO_CHEFE_DONKEY = 90   # s

# Power-ups das fases especiais (veja a seção 4A)
# Cada fase especial solta CÁPSULAS coloridas. Regras gerais (valem para os 5 bônus):
# - só existe uma cápsula na tela por vez e só um bônus TEMPORIZADO fica ativo por vez;
# - nenhum bônus soma pontos (as fases especiais já são bônus de vidas) e todos
# acabam quando o jogador perde uma vida;
# - nenhum bônus encurta a luta contra o chefão em mais de ~40% (veja BONUS_MAX_TIROS).
# GALAGA: CAÇA GÊMEO (ataque), BOMBA NOVA (defesa) e PROPULSOR TURBO (velocidade).
# DONKEY KONG: BANANA-RANG (ataque à distância) e PULO DE MOLA (agilidade).
TIPOS_BONUS = {
    # nome: (cor da cápsula, letra, duração em s; None = sem timer)
    'GEMEO':      ((110, 210, 255), 'G', None),
    'BOMBA':      ((255, 120, 70),  'B', None),
    'TURBO':      ((255, 225, 70),  'T', 8.0),
    'BUMERANGUE': ((255, 150, 220), 'R', None),   # rosa: não se confunde com o rebite dourado do Kong
    'MOLA':       ((120, 255, 140), 'M', 7.0),
}

BONUS_ABATES_POR_CAPSULA = 8      # Galaga: uma cápsula a cada 8 abates (e nos marcos de 66% e 33% do chefão)

BONUS_BANANAS_POR_CAPSULA = 5     # Donkey: uma cápsula a cada 5 bananas coletadas

BONUS_MAX_TIROS = 6               # teto de tiros simultâneos: Gêmeo + Turbo não se acumulam além disso

DESLOC_GEMEO = 22                 # px do centro até cada uma das duas naves do Caça Gêmeo

BOMBA_DANO_CHEFE = 0.05           # a Bomba Nova tira no máximo 5% da vida do chefão (mínimo 1)

BOMBA_INVULNERAVEL = 2.0          # s de invulnerabilidade depois da Bomba Nova

TURBO_VEL_NAVE = 1.35             # nave 35% mais rápida (380 -> 513 px/s)

TURBO_CADENCIA = 1.8              # o intervalo entre tiros é dividido por 1,8

BONUS_SUPERAQUECIMENTO = 1.5      # s de canhão travado depois do Turbo (o preço do bônus)

CARGAS_BUMERANGUE = 3             # cargas do Banana-rang (tecla X)

VELOCIDADE_BUMERANGUE = 520       # px/s

MOLA_GRAVIDADE = 0.8              # gravidade x0,8 e impulso x1,05: salto 43% mais alto e 36% mais longo

MOLA_IMPULSO = 1.05

# O Banana-rang ajuda no chefão? False: só destrói barris e chamas (defesa). True: também
# coleta rebites à distância, o que esvazia a mecânica central do chefão (mantenha False).
BUMERANGUE_AJUDA_NO_CHEFE = False

MAX_NOME = 16              # tamanho máximo do nome do jogador

TOP_RANKING = 10           # quantos recordes aparecem na tabela do GAME OVER

MAX_REGISTROS = 100        # quantos ficam guardados no arquivo

Y_TABELA_RANKING = 556     # y do topo da tabela (suba/desça se ela encostar na moldura)

# Cada entrada da lista ocupa TEMPO_TEMA segundos. Repetições são
# intencionais e fazem parte da sequência de fundos do jogo.
TEMAS = ['bg','bg1','night','bg2','bg3','bg4','bg5','bg6',
         'background','bg7','bg8','bg1','night']

TEMAS_DIA = {'bg','bg2','bg3','bg6','background'}

TEMAS_TARDE = {'bg1','bg4','bg7','bg8'}

PASSAROS_ESPECIAIS = ['Blue','Bubble','Chuck','Doge','Dude','Fishy',
    'FloatKirby','Floppy','Girl','Glasses','Gray','Green','GreenFish',
    'Grellow','HOTpink','Jungle','Kirby','Lime','Orange','ParasolKirby',
    'Pink','Police','Propellor','Purple','Rainbow','Red','Sad','Speed',
    'Ukraine','Yellow']
