# ================================================================
# FLAPPY BIRD — SPRINT 04 AMPLIADA | Programação para Engenharia
# Código didático: classes, eventos, estados, sprites, áudio e JSON
# + FASE ESPECIAL GALAGA (estado 'GALAGA')
# + [NOVO] SISTEMA DE FASES ESPECIAIS POR PONTUAÇÃO (50, 150, 250, ...)
# + [NOVO] ALERTA DE 5 SEGUNDOS ANTES DE CADA FASE ESPECIAL (estado 'ALERTA')
# + [NOVO] FASE ESPECIAL DONKEY KONG (estado 'DONKEY')
# + [MELHORIA 1] DIFICULDADE PROGRESSIVA NO MODO CLÁSSICO (agora por NÍVEL: veja [V4.2])
# + [MELHORIA 2] FASES ESPECIAIS COMO BÔNUS: não somam pontos e dão +1 vida
# + [MELHORIA 3] DONKEY ARREMESSA OS BARRIS MAIS ALTO; GALAGA MAIS DIFÍCIL A CADA VEZ
# + [MELHORIA 4] CADASTRO DO JOGADOR (estado 'CADASTRO') E RANKING TOP 10
# + [V4.1] CORREÇÃO: os pássaros de cima da FASE DOS PÁSSAROS agora ficam em pé
# + [V4.2] 10 NÍVEIS (CICLOS) COM FASES ESPECIAIS A CADA MÚLTIPLO DE 35 PONTOS,
#          FASE DOS PÁSSAROS NO FIM DE CADA CICLO E TELA DE HONRA MÁXIMA
# + [V4.3] DONKEY COM SALVAS DE 2 A 3 BARRIS E CHEFÕES (BOSS GALAGA E KONG FURIOSO)
# + [V4.4] ATALHOS NUMÉRICOS DE NÍVEL (1 a 9 e 0 = nível 10) NO MODO DE TESTE
# + [FUSÃO]  este arquivo une o main__4_ (base: chefões Boss Galaga e Kong com rebites) aos
#            HELPERS DE JUSTIÇA do main__3_ (desvio_maximo_passagem, sortear_topo_passagem)
#            e ao ranking que ignora partidas de teste (ATALHO_INVALIDA_RANKING)
# + [BÔNUS]  5 POWER-UPS NAS FASES ESPECIAIS, embutidos nas classes das fases:
#            Galaga: CAÇA GÊMEO (ataque), BOMBA NOVA (defesa), PROPULSOR TURBO (velocidade)
#            Donkey: BANANA-RANG (ataque à distância, tecla X), PULO DE MOLA (agilidade)
# ================================================================
# Esta versão acrescenta as quatro melhorias acima. Cada trecho novo ou
# alterado por elas traz a etiqueta [MELHORIA n] (n = 1 a 4) nos comentários;
# o que veio das versões anteriores segue marcado com [NOVO] ou [ALTERADO].
# As mudanças desta rodada (níveis, chefões, atalhos) vêm marcadas com [V4.n].
#
# Fluxo da partida:
#   MENU --> CADASTRO (nome do jogador) --> JOGO --> ... --> GAMEOVER (Top 10)
#
# [V4.2] Estrutura do jogo: 10 NÍVEIS (ciclos). Cada ciclo tem, nesta ordem:
#   1) uma fase especial (Donkey Kong ou Galaga) quando a pontuação chega ao
#      próximo múltiplo de 35 (35, 70, 105...); cada uma termina em um CHEFÃO;
#   2) a outra fase especial, no múltiplo de 35 seguinte;
#   3) a FASE DOS PÁSSAROS, 20 pontos depois de concluídas as duas especiais.
#   Durante a fase dos pássaros as fases especiais NÃO são acionadas. Ao fim
#   dela o nível sobe (mais gravidade, mais velocidade e canos mais fechados).
#   Concluir o nível 10 mostra a tela de HONRA MÁXIMA.
#   JOGO --(múltiplo de 35)--> ALERTA (5 s) --> GALAGA ou DONKEY --> JOGO
#   JOGO --(+20 pontos após as duas)--> ALERTA --> FASE DOS PÁSSAROS --> próximo nível
#
# Teclas de teste (somente com MODO_TESTE = True):
#   G = alerta + Galaga | K = alerta + Donkey Kong | F = alerta + fase dos pássaros
#   T = põe a pontuação 1 ponto abaixo do próximo gatilho
#   B = (dentro da Galaga ou do Donkey) pula direto para o CHEFÃO
#   V = vai direto à tela de HONRA MÁXIMA
#   1 a 9 e 0 (= nível 10) = muda NA HORA para aquele nível. [V4.4] Os números são
#   ignorados na tela de cadastro, para o nome poder ter dígitos.
#   C = (dentro da Galaga ou do Donkey) solta uma cápsula de bônus   [BÔNUS]
#   Partida em que algum atalho foi usado vira "teste": não entra no ranking   [FUSÃO]
# Tecla do jogo (não é de teste): X = lança o BANANA-RANG no Donkey, se houver cargas.   [BÔNUS]
from pathlib import Path
import os   # Acessa LOCALAPPDATA para guardar dados persistentes no Windows.
import sys  # Detecta execução empacotada pelo PyInstaller.
import json
import math  # [NOVO] Seno/cosseno: balanço da formação (Galaga), quique dos barris e animações (Donkey).
import random
import time
import pygame

# ================================================================
# 1. CONFIGURAÇÕES GERAIS, FÍSICA E DIFICULDADE
# ================================================================
# Constantes em maiúsculas reúnem parâmetros que o estudante pode
# localizar e ajustar sem procurar valores espalhados pelo programa.
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
# [ALTERADO] [V4.2] TEMPO_FASE (fase dos pássaros por tempo) foi removido: a fase dos
# pássaros agora faz parte do ciclo de cada nível (veja parametros_nivel).
TEMPO_INVULNERAVEL_MS = 1200
USAR_MASCARAS = True

# ---------------------------------------------------------------
# [MELHORIA 1] [V4.2] Níveis e dificuldade progressiva (modo clássico)
# ---------------------------------------------------------------
# [ALTERADO] A dificuldade deixou de depender de "pontos // 100": agora segue
# o NÍVEL (1 a NIVEL_MAXIMO) = o ciclo em que o jogador está. Cada nível tem a
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
MAX_ICONES_VIDA = 8            # [MELHORIA 2] acima disso, as vidas viram "ícone + xN"
# [V4.2] Ciclo de cada nível (veja o resumo no topo do arquivo).
PONTOS_ENTRE_ESPECIAIS = 35    # as fases especiais aparecem nos múltiplos de 35 pontos
PONTOS_ANTES_PASSAROS = 20     # pontos, após as duas especiais, para liberar a fase dos pássaros
# [V4.4] Teclas numéricas de teste -> nível (1 a 9; 0 = nível 10; teclado numérico também).
TECLAS_NIVEL = {}
for _nivel in range(1, NIVEL_MAXIMO + 1):
    _digito = _nivel % 10
    TECLAS_NIVEL[getattr(pygame, f'K_{_digito}')] = _nivel
    TECLAS_NIVEL[getattr(pygame, f'K_KP{_digito}')] = _nivel
# [JUSTIÇA] [FUSÃO] Ritmo humano usado no cálculo de justiça das passagens (veja
# desvio_maximo_passagem): 6 toques por segundo a 30 FPS = 1 toque a cada 5 quadros.
QUADROS_ENTRE_TOQUES = 5

# ---------------------------------------------------------------
# [NOVO] Parâmetros da fase GALAGA
# ---------------------------------------------------------------
# Diferente do Flappy (que usa px/quadro), a fase Galaga usa
# velocidades em px/segundo multiplicadas por dt. Assim o movimento
# não depende de quantos quadros por segundo o computador consegue.
TEMPO_GALAGA = 60         # duração máxima da fase, em segundos
MODO_TESTE = True         # True: atalhos de teste G/K/F/T/B/V/C e números 1-9/0 de nível ativos (False p/ entregar)  [V4.4]
ATALHO_INVALIDA_RANKING = True   # [FUSÃO] partida em que um atalho foi usado NÃO entra no ranking (veja Jogo.registrar_partida)
TAMANHO_INIMIGO = 46      # maior lado (px) do sprite de cada inimigo
TAMANHO_NAVE = 60         # maior lado (px) do sprite da nave
VELOCIDADE_NAVE = 380     # px/s — movimento horizontal da nave
VELOCIDADE_TIRO = 560     # px/s — tiro do jogador (sobe)
VELOCIDADE_TIRO_INIMIGO = 280  # px/s — tiro dos inimigos (desce)
INTERVALO_TIRO = 0.22     # s mínimos entre dois tiros do jogador
MAX_TIROS_JOGADOR = 3     # tiros do jogador simultâneos na tela
# [ALTERADO] [MELHORIA 2] PONTOS_ABATE, PONTOS_ABATE_MERGULHO e BONUS_FASE_GALAGA
# deixaram de existir: as fases especiais não somam pontos ao placar
# (veja VIDAS_POR_FASE_ESPECIAL, na seção do cronograma das fases).
COLUNAS_GALAGA = 7        # colunas da formação (linhas: 3 a 5 conforme o nível)
ESPACO_COL, ESPACO_LIN = 64, 58   # distância entre inimigos (px)
Y_FORMACAO = 175          # y da primeira linha da formação
Y_NAVE = ALTURA - 120     # y fixo da nave (a nave só anda na horizontal)

# ---------------------------------------------------------------
# [NOVO] Sistema de fases especiais por pontuação
# ---------------------------------------------------------------
# [ALTERADO] [V4.2] As fases especiais agora ocorrem a cada múltiplo de
# PONTOS_ENTRE_ESPECIAIS (35, 70, 105...) e cada ciclo (nível) tem exatamente
# duas delas (Galaga e Donkey Kong), seguidas da fase dos pássaros. Isto
# substitui PONTOS_PRIMEIRA_ESPECIAL e INTERVALO_ESPECIAL (50, 150, 250...).
TEMPO_ALERTA = 5.0        # s de aviso/contagem regressiva antes da fase
# Ordem das duas fases especiais de cada ciclo: nos níveis ímpares começa pelo
# Donkey Kong; nos pares, pela Galaga (veja Jogo.ordem_especiais).
ORDEM_FASES_ESPECIAIS = ('DONKEY', 'GALAGA')
# Texto do alerta de cada variante: (nome, dica, cor do nome).
NOMES_FASES = {
    'GALAGA': ('GALAGA', 'Derrube a formação e enfrente o CHEFÃO!', (90, 220, 255)),
    'DONKEY': ('DONKEY KONG', 'Desvie dos barris e derrote o KONG!', (255, 150, 40)),
    'PASSAROS': ('FASE DOS PÁSSAROS', 'Passe entre os pássaros: vale pontos!', (255, 225, 90)),
}
# Estados em que a partida está "rodando" (valem pausa, placar, etc.).
ESTADOS_ATIVOS = ('JOGO', 'ALERTA', 'GALAGA', 'DONKEY')
# [MELHORIA 2] As fases especiais são BÔNUS: não somam pontos ao placar.
# Em troca, COMPLETAR a fase (Galaga: derrubar toda a formação; Donkey Kong:
# sobreviver até o fim da travessia) dá vidas extras. Se o tempo da Galaga
# esgotar sem concluí-la, não há vida extra.
VIDAS_POR_FASE_ESPECIAL = 1

# ---------------------------------------------------------------
# [NOVO] Parâmetros da fase DONKEY KONG
# ---------------------------------------------------------------
# Esta fase mantém a física do Flappy (px/quadro), mas troca os canos
# por cipós + pilhas de barris, e ajusta a dinâmica de leve:
#   - rolagem 25% mais rápida e abertura um pouco maior (compensa);
#   - Kong arremessa barris em ARCO ALTO entre as pilhas [MELHORIA 3];
#   - bananas no meio das passagens são coletáveis (só um contador: [MELHORIA 2]).
Y_CHAO = ALTURA - 100     # topo do chão (mesmo valor usado na classe Chao)
TEMPO_DONKEY = 45         # duração da fase, em segundos
VELOCIDADE_DONKEY = 5     # px/quadro (o Flappy normal usa VELOCIDADE_CANOS = 4)
ABERTURA_DONKEY = 300     # passagem vertical (o normal usa ABERTURA_CANOS = 290)
# [ALTERADO] [MELHORIA 2] PONTOS_BANANA e BONUS_FASE_DONKEY foram removidos: as
# bananas viram só um contador da fase e o bônus passou a ser +1 vida.
CHANCE_BARRIL = 0.5       # probabilidade de haver barril entre duas pilhas (sobe com o nível)
# [MELHORIA 3] Kong agora ARREMESSA o barril para o alto (antes ele só quicava
# até 150 px do chão). O barril sai das mãos do Kong, sobe em parábola e passa
# pelo pássaro no ponto mais alto do arco, na altura da passagem seguinte
# (± DESVIO_APICE_BARRIL px). Ali ele "paira": o jogador precisa escolher entre
# passar por cima ou por baixo dele, sem errar a faixa. Como o ápice acompanha a
# passagem, sempre sobra espaço para os dois lados (a fase continua justa).
DESVIO_APICE_BARRIL = 25  # px de variação do ápice em torno do centro da passagem
FRAMES_ANTECIPACAO_KONG = 14   # quadros (~0,5 s) em que Kong ergue o barril antes de soltar
# [V4.3] Chefões. Cada fase especial termina com um chefão (veja ChefeGalaga e
# FaseDonkey._atualizar_chefe). Se o tempo do chefão esgotar, ele "foge": a fase
# termina sem a vida extra.
TEMPO_CHEFE_GALAGA = 90   # s
TEMPO_CHEFE_DONKEY = 90   # s

# ---------------------------------------------------------------
# [BÔNUS] Power-ups das fases especiais (veja a seção 4A)
# ---------------------------------------------------------------
# Cada fase especial solta CÁPSULAS coloridas. Regras gerais (valem para os 5 bônus):
#   - só existe uma cápsula na tela por vez e só um bônus TEMPORIZADO fica ativo por vez;
#   - nenhum bônus soma pontos (as fases especiais já são bônus de vidas) e todos
#     acabam quando o jogador perde uma vida;
#   - nenhum bônus encurta a luta contra o chefão em mais de ~40% (veja BONUS_MAX_TIROS).
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


# __file__ é o caminho deste script; parent.parent sobe de src/
# para a raiz do projeto. Assim os recursos não dependem do terminal.
# Os recursos (imagens/sons) são somente leitura; os recordes precisam
# de um diretório gravável e permanente, mesmo no modo --onefile.
if getattr(sys, 'frozen', False):
    # O PyInstaller extrai os recursos incorporados para esta pasta.
    RAIZ_RECURSOS = Path(sys._MEIPASS)
    # LOCALAPPDATA persiste entre execuções e não depende de onde o .exe está.
    pasta_local = os.environ.get('LOCALAPPDATA')
    RAIZ_DADOS = (Path(pasta_local) if pasta_local else Path.home() / 'AppData' / 'Local') / 'FlappyBird'
else:
    # main.py está em src/: subir duas pastas alcança a raiz do projeto.
    RAIZ_RECURSOS = Path(__file__).resolve().parent.parent
    RAIZ_DADOS = RAIZ_RECURSOS
IMAGENS = RAIZ_RECURSOS / 'assets' / 'imgs'
AUDIOS = RAIZ_RECURSOS / 'assets' / 'audio'
ARQUIVO_RECORDE = RAIZ_DADOS / 'data' / 'recorde.json'
# [MELHORIA 4] Ranking com jogadores (substitui o recorde único). O arquivo
# antigo recorde.json ainda é lido UMA vez, só para importar o recorde anterior.
ARQUIVO_RANKING = RAIZ_DADOS / 'data' / 'ranking.json'
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

# ================================================================
# 2. FUNÇÕES AUXILIARES — IMAGENS, SONS E ARQUIVO JSON
# ================================================================
# Função: bloco reutilizável definido com def; pode receber parâmetros
# e devolver um resultado com return.

def imagem(nome, fator=2):
    """Carrega um PNG com transparência e amplia suas dimensões.

    fator=2 significa largura e altura duplicadas; a área quadruplica.
    """
    img = pygame.image.load(str(IMAGENS / nome)).convert_alpha()
    return pygame.transform.scale(img, (img.get_width()*fator,
                                        img.get_height()*fator))

def ajustar_sprite(sprite, lado):
    """[NOVO] Redimensiona mantendo a proporção: o maior lado passa a
    medir 'lado' pixels. Garante inimigos de tamanho parecido mesmo que
    os PNGs originais tenham dimensões diferentes.
    """
    escala = lado / max(sprite.get_width(), sprite.get_height())
    return pygame.transform.smoothscale(
        sprite, (max(1, int(sprite.get_width()*escala)),
                 max(1, int(sprite.get_height()*escala))))

def bezier(p0, p1, p2, t):
    """[NOVO] Ponto de uma curva de Bézier quadrática, com t de 0 a 1.

    B(t) = (1-t)²·P0 + 2(1-t)t·P1 + t²·P2
    P0 é o início, P2 é o fim e P1 (ponto de controle) "puxa" a curva.
    É assim que os inimigos fazem trajetórias curvas de entrada e mergulho.
    """
    u = 1 - t
    return (u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
            u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1])

def som(nome):
    """Tenta carregar um efeito sonoro; retorna None se indisponível.

    None permite ao jogo prosseguir mesmo sem dispositivo de áudio.
    """
    if not pygame.mixer.get_init():
        return None
    try:
        return pygame.mixer.Sound(str(AUDIOS / nome))
    except (OSError, pygame.error) as erro:
        print(f'Aviso: som {nome} indisponível: {erro}')
        return None

def ler_recorde():
    """[ALTERADO] [MELHORIA 4] Lê o recorde do formato ANTIGO (recorde.json).
    Hoje só serve para importar o recorde anterior para o ranking novo.

    O bloco with fecha o arquivo automaticamente, inclusive em erros.
    """
    try:
        with ARQUIVO_RECORDE.open(encoding='utf-8') as arq:
            dados = json.load(arq)
        pontos = dados.get('pontos', 0)
        nome = dados.get('nome', 'Anônimo')
        return (pontos if type(pontos) is int and pontos >= 0 else 0,
                nome if isinstance(nome, str) else 'Anônimo')
    except (OSError, ValueError, TypeError):
        return 0, 'Anônimo'

# ----------------------------------------------------------------
# [MELHORIA 4] Jogadores e ranking (Top 10)
# ----------------------------------------------------------------
# O arquivo data/ranking.json guarda o último jogador e uma lista de
# registros. Cada partida com pontuação maior que 0 vira UM registro:
#     {"nome": "Ana", "pontos": 120, "data": "2026-10-28 15:42"}
# A lista é mantida ordenada: mais pontos primeiro; em caso de empate,
# quem chegou primeiro fica na frente.

def limpar_nome(texto):
    """Remove espaços das pontas e repetidos e limita o tamanho a MAX_NOME.

    Devolve '' se não sobrar nenhum caractere visível.
    """
    return ' '.join(str(texto).split())[:MAX_NOME].strip()

def texto_vidas_extras():
    """[MELHORIA 2] '+1 VIDA' ou '+2 VIDAS', conforme VIDAS_POR_FASE_ESPECIAL."""
    n = VIDAS_POR_FASE_ESPECIAL
    return f'+{n} VIDA' if n == 1 else f'+{n} VIDAS'

def _registro_valido(registro):
    """True se o item lido do JSON tem nome (texto) e pontos (inteiro > 0)."""
    return (isinstance(registro, dict)
            and isinstance(registro.get('nome'), str)
            and bool(limpar_nome(registro['nome']))
            and type(registro.get('pontos')) is int
            and registro['pontos'] > 0)

def ordenar_ranking(registros):
    """Ordena do melhor para o pior; a data desempata (o mais antigo vence)."""
    return sorted(registros, key=lambda r: (-r['pontos'], r.get('data', '')))

def ler_ranking():
    """Lê o ranking do JSON. Devolve (registros ordenados, último jogador).

    Se o arquivo não existir (ou estiver corrompido), começa vazio, mas
    aproveita o recorde do formato antigo (recorde.json), quando houver.
    Registros inválidos são ignorados em vez de derrubar o jogo.
    """
    registros, ultimo = [], ''
    try:
        with ARQUIVO_RANKING.open(encoding='utf-8') as arq:
            dados = json.load(arq)
        for r in dados.get('registros', []):
            if _registro_valido(r):
                nivel = r.get('nivel', 0)
                registros.append({'nome': limpar_nome(r['nome']),
                                  'pontos': r['pontos'],
                                  'data': str(r.get('data', '')),
                                  # [V4.2] nível alcançado e se a pessoa zerou o jogo
                                  'nivel': nivel if type(nivel) is int and 0 <= nivel <= NIVEL_MAXIMO else 0,
                                  'zerou': r.get('zerou') is True})
        ultimo = dados.get('ultimo_jogador', '')
        ultimo = limpar_nome(ultimo) if isinstance(ultimo, str) else ''
    except (OSError, ValueError, TypeError, AttributeError):
        pontos, nome = ler_recorde()
        if pontos > 0:
            registros.append({'nome': nome, 'pontos': pontos, 'data': '',
                              'nivel': 0, 'zerou': False})
    return ordenar_ranking(registros)[:MAX_REGISTROS], ultimo

def salvar_ranking(registros, ultimo_jogador):
    """Grava o ranking em JSON UTF-8 e devolve True/False.

    A escrita é "atômica": grava num arquivo temporário e só então troca o
    arquivo definitivo (os.replace). Se o jogo fechar no meio, o ranking
    antigo continua íntegro.
    """
    try:
        ARQUIVO_RANKING.parent.mkdir(parents=True, exist_ok=True)
        temporario = ARQUIVO_RANKING.with_suffix('.tmp')
        with temporario.open('w', encoding='utf-8') as arq:
            # ensure_ascii=False mantém acentos; indent=2 formata o JSON.
            json.dump({'ultimo_jogador': ultimo_jogador,
                       'registros': registros[:MAX_REGISTROS]},
                      arq, ensure_ascii=False, indent=2)
        os.replace(temporario, ARQUIVO_RANKING)
        return True
    except OSError as erro:
        print(f'Aviso: não foi possível gravar o ranking: {erro}')
        return False

def adicionar_registro(registros, nome, pontos, nivel=1, zerou=False):
    """Insere uma partida no ranking.

    [ALTERADO] [V4.2] Cada registro também guarda o NÍVEL alcançado e se o
    jogador ZEROU o jogo (concluiu o nível 10).

    Devolve (nova lista ordenada, posição da partida) com posição a partir
    de 1. Partidas com 0 pontos não entram: a posição volta None.
    """
    if pontos <= 0:
        return registros, None
    novo = {'nome': nome, 'pontos': pontos,
            'data': time.strftime('%Y-%m-%d %H:%M'),
            'nivel': nivel, 'zerou': bool(zerou)}
    ordenados = ordenar_ranking(registros + [novo])
    posicao = next(i for i, r in enumerate(ordenados, start=1) if r is novo)
    return ordenados[:MAX_REGISTROS], posicao

# ================================================================
# 2B. [NOVO] FUNÇÃO DE CRONOGRAMA E SPRITES DO TEMA DONKEY KONG
# ================================================================

def parametros_nivel(nivel):
    """[V4.2] Tabela de dificuldade do modo clássico para o nível 1 a NIVEL_MAXIMO.

    nível 1: gravidade 1,10 | abertura 290 px | velocidade 4,00 px/quadro
    nível 10: gravidade 1,64 | abertura 191 px | velocidade 5,35 px/quadro
    (a abertura final é cerca de 4 alturas do pássaro, como no jogo original).
    'pontos_passaros' = quantos pássaros-obstáculo passar na fase dos pássaros do
    nível; 'oscilacao_passaros' = quanto (px) os pássaros sobem e descem
    (só a partir do nível 4), o que obriga a acompanhar a passagem.
    """
    n = max(1, min(NIVEL_MAXIMO, int(nivel))) - 1          # 0 a 9
    return {
        'gravidade': GRAVIDADE + GRAVIDADE_POR_NIVEL*n,
        'abertura': ABERTURA_CANOS - ABERTURA_POR_NIVEL*n,
        'velocidade': VELOCIDADE_CANOS + VELOCIDADE_POR_NIVEL*n,
        'pontos_passaros': 15 + n,
        'oscilacao_passaros': 0 if n < 3 else min(36, 9*(n - 2)),
    }

def proximo_multiplo(pontos):
    """[V4.2] Menor múltiplo de PONTOS_ENTRE_ESPECIAIS ESTRITAMENTE maior que 'pontos'.

    0 -> 35, 34 -> 35, 35 -> 70, 69 -> 70, 70 -> 105... Função pura: fácil de testar.
    """
    return (pontos // PONTOS_ENTRE_ESPECIAIS + 1)*PONTOS_ENTRE_ESPECIAIS

def desvio_maximo_passagem(abertura, velocidade, gravidade, impulso,
                           largura_cano, largura_passaro, altura_passaro):
    """[JUSTIÇA] [FUSÃO] (helper do main__3_) Maior diferença de altura aceitável entre
    duas passagens seguidas.

    Entre o fim de um par de obstáculos e o começo do próximo o pássaro tem uma
    janela horizontal de (espaço - largura do cano - largura do pássaro) px, ou
    seja, janela/velocidade quadros. Batendo asas a cada QUADROS_ENTRE_TOQUES
    quadros ele sobe, em média, impulso - g*(k+1)/2 px por quadro (soma de
    -v0 + g*i para i = 1..k, dividida por k). A folga dentro da própria passagem
    (abertura - altura do pássaro) também conta. Usamos 75% da subida teórica
    para sobrar margem a quem joga: a fase fica difícil, mas nunca impossível.
    """
    janela = ESPACO_ENTRE_CANOS - largura_cano - largura_passaro
    quadros = janela/velocidade
    subida = max(1.0, abs(impulso) - gravidade*(QUADROS_ENTRE_TOQUES + 1)/2)
    folga = max(0.0, abertura - altura_passaro)
    return int(folga + 0.75*subida*quadros)

def sortear_topo_passagem(topo_anterior, desvio_max):
    """[JUSTIÇA] [FUSÃO] Sorteia o topo da próxima passagem (150 a 400 px), limitando a
    distância até a passagem anterior a desvio_max (veja a função acima)."""
    topo = random.randint(150, 400)
    if topo_anterior is not None:
        topo = max(topo_anterior - desvio_max, min(topo_anterior + desvio_max, topo))
        topo = max(150, min(400, topo))
    return topo

def colide_circulo(cx, cy, raio, caixa):
    """[V4.3] Colisão círculo x retângulo: acha o ponto do retângulo mais próximo
    do centro do círculo e compara a distância com o raio."""
    px = max(caixa.left, min(cx, caixa.right))
    py = max(caixa.top, min(cy, caixa.bottom))
    return (cx - px)**2 + (cy - py)**2 < raio**2

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
                    mãos vazias (acabou de arremessar).  [MELHORIA 3]
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
    """[V4.3] Cópia do sprite com 'cor' somada aos canais RGB (clareia/avermelha)
    sem mexer na transparência. Usado no flash do chefão e no Kong furioso."""
    copia = sprite.copy()
    copia.fill(tuple(cor) + (0,), special_flags=pygame.BLEND_RGB_ADD)
    return copia

def criar_chefe_galaga(largura=150, altura=118):
    """[V4.3] "Boss Galaga" desenhado por código: inseto verde de asas roxas, olhos
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
    """[V4.3] Rebite dourado (cabeça redonda com fenda em cruz): o "ponto fraco"
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
    """[V4.3] "Chama viva" do Donkey Kong: cabeça de fogo com olhos e cauda de
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

# ================================================================
# 3. CLASSE RECURSOS — CARREGAMENTO CENTRALIZADO
# ================================================================
# Classe é um molde para criar objetos. Aqui agrupamos imagens e sons
# para carregá-los uma vez, em vez de reler arquivos a cada quadro.
class Recursos:
    """Reúne sprites de cenários, personagens, interface e efeitos."""

    def __init__(self):
        # Dicionário: cada chave identifica o recurso correspondente.
        self.fundos = {nome: imagem(nome+'.png') for nome in set(TEMAS)}
        self.chao = imagem('base.png')
        self.cano_dia = imagem('pipe.png')
        self.cano_noite = imagem('pipe_night.png')
        self.passaros = {
            'dia': [imagem(f'bird{i}.png') for i in (1,2,3)],
            'tarde': [imagem(f'bird{i}_tarde.png') for i in (1,2,3)],
            'noite': [imagem(f'bird{i}_night.png') for i in (1,2,3)],
        }
        self.especiais = {nome: imagem(nome+'.png')
                          for nome in PASSAROS_ESPECIAIS}
        # [NOVO] Sprites da fase Galaga, derivados dos que já foram carregados.
        # Inimigos: os pássaros especiais reduzidos a um tamanho padrão.
        self.inimigos = {nome: ajustar_sprite(sprite, TAMANHO_INIMIGO)
                         for nome, sprite in self.especiais.items()}
        # Nave: o próprio pássaro girado 90° (anti-horário) para "apontar" para
        # cima. Se o seu sprite não olhar para a direita, ajuste o ângulo.
        self.nave = pygame.transform.rotate(
            ajustar_sprite(self.passaros['dia'][1], TAMANHO_NAVE), 90)
        # [NOVO] Sprites da fase Donkey Kong (gerados por código; ver seção 2B).
        # convert_alpha() acelera o blit; exige que a janela já exista.
        self.selva_cipo = criar_cipo().convert_alpha()
        self.selva_barris = criar_pilha_barris().convert_alpha()
        self.barril = criar_barril_rolante().convert_alpha()
        self.banana = criar_banana().convert_alpha()
        # [MELHORIA 3] Três poses: parado, 'lanca' (barril erguido: preparo do
        # arremesso) e 'arremessou' (braços erguidos, mãos vazias: barril solto).
        self.kong = {'parado': criar_kong(False).convert_alpha(),
                     'lanca': criar_kong(True).convert_alpha(),
                     'arremessou': criar_kong(True, False).convert_alpha()}
        # [V4.3] Chefões: Kong maior (e uma versão avermelhada, "furioso"), Boss
        # Galaga (normal e flash), rebite e bola de fogo, tudo desenhado por código.
        self.kong_boss = {nome: pygame.transform.smoothscale(
                              sprite, (int(sprite.get_width()*1.35), int(sprite.get_height()*1.35)))
                          for nome, sprite in self.kong.items()}
        self.kong_furioso = {nome: tingir(sprite, (110, 0, 0))
                             for nome, sprite in self.kong_boss.items()}
        self.chefe_galaga, self.chefe_galaga_flash = [
            sprite.convert_alpha() for sprite in criar_chefe_galaga()]
        self.rebite = criar_rebite().convert_alpha()
        self.bola_fogo = criar_bola_fogo().convert_alpha()
        self.fundo_selva = criar_fundo_selva().convert()
        self.palmeiras_longe = criar_camada_palmeiras((14, 52, 50), 330, 470, 7, 11).convert_alpha()
        self.palmeiras_perto = criar_camada_palmeiras((6, 30, 32), 250, 380, 5, 23).convert_alpha()
        self.viga = criar_viga().convert()
        self.logo = imagem('Flappy_Bird_logo.png')
        self.gameover = imagem('gameover.png')
        self.moldura = imagem('moldura.png')
        self.medalhas = {nome: imagem(nome+'.png')
                         for nome in ('bronze','prata','ouro')}
        self.numeros = {str(i): imagem(f'{i}.png') for i in range(10)}
        self.sons = {nome: som(arquivo) for nome,arquivo in {
            'pulo':'wing.wav', 'ponto':'point.wav', 'colisao':'hit.wav',
            'morte':'die.wav', 'inicio':'chiptune_begin.mp3',
            'fim':'game_over.mp3', 'arcade':'game_over_arcade.mp3'
        }.items()}

# ================================================================
# 4. OBJETOS DO JOGO — PROGRAMAÇÃO ORIENTADA A OBJETOS
# ================================================================
# Atributos guardam o estado do objeto; métodos definem ações.
# self identifica a instância que está executando o método.
class Passaro:
    """Representa o jogador: posição, velocidade e animação."""
    def __init__(self, recursos):
        self.recursos = recursos
        self.x, self.y, self.vy = 200.0, 350.0, 0.0
        self.indice, self.contador = 0, 0
        self.familia = 'dia'
        # [MELHORIA 1] Gravidade e impulso viram ATRIBUTOS: o modo clássico os
        # ajusta a cada nível (aplicar_dificuldade); as fases especiais usam
        # os valores base, por isso não herdam a dificuldade do modo clássico.
        self.gravidade = GRAVIDADE
        self.impulso = IMPULSO

    def aplicar_dificuldade(self, gravidade):
        """[MELHORIA 1] Define a gravidade do nível atual e compensa o impulso.

        A altura de um bater de asas é v²/(2g). Se só a gravidade subisse, o
        pássaro subiria cada vez menos a cada toque. Por isso o impulso cresce
        na proporção (g/g0)**COMPENSACAO_IMPULSO: compensação parcial, que
        deixa o jogo mais difícil sem torná-lo injusto.
        """
        self.gravidade = gravidade
        self.impulso = IMPULSO*(gravidade/GRAVIDADE)**COMPENSACAO_IMPULSO

    def pular(self):
        """Aplica impulso vertical quando há clique ou barra de espaço."""
        self.vy = self.impulso      # [ALTERADO] antes: IMPULSO (constante)

    def atualizar(self):
        # Integração discreta: primeiro velocidade, depois posição.
        # A cada quadro: vy <- vy + gravidade; y <- y + vy.
        # min(..., 16) limita a velocidade de queda.
        self.vy = min(self.vy + self.gravidade, 16)   # [ALTERADO] antes: GRAVIDADE
        self.y += self.vy
        self.contador += 1
        if self.contador >= 5:
            self.contador = 0
            self.indice = (self.indice + 1) % 3

    @property
    def sprite(self):
        """Seleciona o quadro atual; acesso como atributo: self.sprite.

        @property permite consultar o método sem escrever self.sprite().
        """
        return self.recursos.passaros[self.familia][self.indice]

    def retangulo(self):
        return self.sprite.get_rect(topleft=(int(self.x), int(self.y)))

    def desenhar(self, tela):
        # A rotação é visual; o retângulo/máscara usa sprite sem giro.
        angulo = max(-75, min(25, -self.vy*5))
        rot = pygame.transform.rotate(self.sprite, angulo)
        tela.blit(rot, rot.get_rect(center=self.retangulo().center))

class Obstaculo:
    """Representa um par de canos ou de pássaros da fase especial.

    [ALTERADO] Velocidade e abertura agora são atributos (com os valores
    antigos como padrão) e os sprites são montados em criar_sprites().
    Assim, uma subclasse (ObstaculoSelva, na fase Donkey Kong) pode mudar
    a aparência e a dinâmica sem copiar o resto da classe.
    """
    def __init__(self, x, recursos, especial=False, tema='bg',
                 velocidade=VELOCIDADE_CANOS, abertura=ABERTURA_CANOS, oscilacao=0.0, topo=None):
        self.x = float(x)
        # [JUSTIÇA] 'topo' vem de sortear_topo_passagem (limita a distância até a passagem
        # anterior); sem ele, sorteia livremente como antes.
        self.topo_passagem = topo if topo is not None else random.randint(150, 400)
        self.passou = False
        self.especial = especial
        # [V4.2] Oscilação (fase dos pássaros nos níveis altos): a passagem inteira
        # sobe e desce até `oscilacao` px em torno da posição base, SEM mudar o
        # tamanho da abertura (os dois pássaros se movem juntos).
        self.topo_base = float(self.topo_passagem)
        self.oscilacao = oscilacao
        self.fase_osc = random.uniform(0, 2*math.pi)
        self.tempo_osc = 0
        self.velocidade = velocidade      # [NOVO] px/quadro de rolagem
        self.abertura = abertura          # [NOVO] passagem vertical em px
        self.cima, self.baixo = self.criar_sprites(recursos, especial, tema)
        self.largura = max(self.cima.get_width(), self.baixo.get_width())

    def criar_sprites(self, recursos, especial, tema):
        """[NOVO] Devolve (sprite_de_cima, sprite_de_baixo). É o ponto que
        as subclasses sobrescrevem para trocar o visual do obstáculo."""
        if especial:
            nomes = random.sample(PASSAROS_ESPECIAIS, 2)
            # [V4.1] CORREÇÃO DE BUG: antes o pássaro de cima era girado 180° e
            # aparecia de cabeça para baixo. Agora os dois usam o sprite original,
            # virados para cima (o de cima fica "pendurado" acima da passagem).
            cima = recursos.especiais[nomes[0]]
            baixo = recursos.especiais[nomes[1]]
        else:
            baixo = (recursos.cano_dia if tema != 'night' and tema != 'bg5'
                     else recursos.cano_noite)
            cima = pygame.transform.flip(baixo, False, True)
        return cima, baixo

    def atualizar(self):
        self.x -= self.velocidade   # [ALTERADO] era VELOCIDADE_CANOS fixo
        if self.oscilacao:
            # [V4.2] Movimento senoidal: período de ~3 s (0,07 rad/quadro a 30 FPS).
            self.tempo_osc += 1
            self.topo_passagem = (self.topo_base
                                  + self.oscilacao*math.sin(self.fase_osc + self.tempo_osc*0.07))

    def retangulos(self):
        x = int(self.x)
        topo = self.cima.get_rect(bottomleft=(x, self.topo_passagem))
        base = self.baixo.get_rect(topleft=(x, self.topo_passagem+self.abertura))   # [ALTERADO] usa self.abertura
        return topo, base

    def desenhar(self, tela):
        a,b = self.retangulos()
        tela.blit(self.cima, a)
        tela.blit(self.baixo, b)

    def colide(self, passaro):
        """Verifica colisão usando retângulos e, opcionalmente, máscaras.

        Retângulos fazem o teste rápido; máscaras refinam pixel a pixel.
        """
        ret_p = passaro.retangulo()
        # A máscara distingue pixels opacos dos transparentes no PNG.
        mascara_p = pygame.mask.from_surface(passaro.sprite) if USAR_MASCARAS else None
        for sprite,ret in zip((self.cima,self.baixo),self.retangulos()):
            if not ret_p.colliderect(ret):
                continue
            if not USAR_MASCARAS:
                return True
            mascara = pygame.mask.from_surface(sprite)
            desloc = (ret.x-ret_p.x,ret.y-ret_p.y)
            if mascara_p.overlap(mascara, desloc) is not None:
                return True
        return False

class Chao:
    """Desenha uma faixa de chão repetida para simular movimento."""
    def __init__(self, sprite):
        self.sprite = sprite
        self.x = 0
        self.y = Y_CHAO   # [ALTERADO] era ALTURA - 100; agora vem da constante compartilhada

    def atualizar(self, velocidade=VELOCIDADE_CHAO):
        # [ALTERADO] [V4.2] A velocidade do chão acompanha a do nível.
        self.x = (self.x-velocidade) % self.sprite.get_width()

    def desenhar(self, tela):
        # A imagem é repetida sem deixar lacunas no eixo horizontal.
        x = int(self.x)-self.sprite.get_width()
        while x < LARGURA:
            tela.blit(self.sprite,(x,self.y))
            x += self.sprite.get_width()

# ================================================================
# 4A. [BÔNUS] SISTEMA DE POWER-UPS (compartilhado pela Galaga e pelo Donkey Kong)
# ================================================================
# As fases (FaseGalaga e FaseDonkey) continuam falando com o Jogo só por sons, dano,
# vidas_ganhas e terminou; os bônus vivem DENTRO delas. Esta seção reúne as peças comuns:
# EfeitosAtivos (timers), CapsulaBonus (o item coletável) e o HUD dos bônus ativos.

class EfeitosAtivos:
    """Timers dos bônus temporizados: nome -> segundos restantes."""
    def __init__(self):
        self.tempo = {}

    def ativar(self, nome, duracao):
        self.tempo[nome] = duracao

    def ativo(self, nome):
        return self.tempo.get(nome, 0) > 0

    def atualizar(self, dt):
        """Avança os timers e devolve os nomes dos efeitos que ACABARAM neste quadro
        (a Galaga usa isso para ligar o superaquecimento depois do Turbo)."""
        acabaram = []
        for nome in list(self.tempo):
            self.tempo[nome] -= dt
            if self.tempo[nome] <= 0:
                del self.tempo[nome]
                acabaram.append(nome)
        return acabaram

    def limpar(self):
        self.tempo.clear()

class CapsulaBonus:
    """Cápsula coletável (círculo colorido com uma letra), desenhada por código.

    Na Galaga cai devagar (vy > 0); no Donkey acompanha a rolagem (vx < 0). As
    velocidades são em px/s, como na fase Galaga."""
    RAIO = 17
    fonte = None            # criada na primeira vez que é desenhada

    def __init__(self, tipo, x, y, vx=0.0, vy=0.0):
        self.tipo = tipo
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy

    def atualizar(self, dt):
        self.x += self.vx*dt
        self.y += self.vy*dt

    def retangulo(self):
        return pygame.Rect(int(self.x - self.RAIO), int(self.y - self.RAIO),
                           2*self.RAIO, 2*self.RAIO)

    def fora_da_tela(self):
        return self.y > ALTURA + 30 or self.x < -40

    def desenhar(self, tela, tempo):
        cor, letra, _ = TIPOS_BONUS[self.tipo]
        if CapsulaBonus.fonte is None:
            CapsulaBonus.fonte = pygame.font.Font(None, 26)
        centro = (int(self.x), int(self.y + 3*math.sin(tempo*6)))      # flutua um pouco
        pygame.draw.circle(tela, cor, centro, self.RAIO + 4 + int(2*math.sin(tempo*9)), 2)  # halo pulsante
        pygame.draw.circle(tela, cor, centro, self.RAIO)
        pygame.draw.circle(tela, (255, 255, 255), centro, self.RAIO, 2)
        letra_img = CapsulaBonus.fonte.render(letra, True, (20, 20, 40))
        tela.blit(letra_img, letra_img.get_rect(center=centro))

def desenhar_hud_bonus(tela, linhas):
    """Lista de bônus ativos no canto inferior esquerdo (acima do texto de status).
    linhas = [(texto, cor), ...]"""
    fonte = pygame.font.Font(None, 24)
    for i, (texto, cor) in enumerate(linhas):
        img = fonte.render(texto, True, cor)
        fundo = pygame.Surface((img.get_width() + 10, img.get_height() + 2), pygame.SRCALPHA)
        fundo.fill((0, 0, 0, 150))
        tela.blit(fundo, (6, ALTURA - 190 + i*24))
        tela.blit(img, (11, ALTURA - 189 + i*24))

# ================================================================
# 4B. [NOVO] OBJETOS DA FASE GALAGA
# ================================================================
# A fase Galaga é um "mini-jogo" dentro do jogo. A classe FaseGalaga
# cuida de tudo que é interno a ela (nave, inimigos, tiros, colisões).
# A classe Jogo só decide QUANDO ela começa/termina e como o resultado
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

class Explosao:
    """Círculo que cresce e esmaece por DURACAO segundos."""
    DURACAO = 0.4

    def __init__(self, x, y):
        self.x, self.y, self.tempo = x, y, 0.0

    def atualizar(self, dt):
        self.tempo += dt

    @property
    def ativa(self):
        return self.tempo < self.DURACAO

    def desenhar(self, tela):
        p = min(1.0, self.tempo/self.DURACAO)   # progresso de 0 a 1
        raio = int(8 + 28*p)
        cor = (255, int(220 - 160*p), 40)
        pygame.draw.circle(tela, cor, (int(self.x), int(self.y)),
                           raio, max(1, int(5*(1-p))))

def parametros_galaga(nivel):
    """[MELHORIA 3] [V4.2] Parâmetros de dificuldade da Galaga para o nível do jogo.

    nivel = 0 no nível 1 (dificuldade MODERADA) ... 9 no nível 10. A curva liga
    mecânicas novas pelo caminho, em vez de só acelerar tudo:
      níveis 1-2: formação balançando, mergulhos e tiros (base) + FÚRIA suave;
      nível 2+  : mergulhos em ESQUADRÃO (2 pássaros saem juntos, escalonados);
      nível 3+  : mergulhos que PERSEGUEM a nave e chefes de fileira que atiram
                  em LEQUE (3 tiros; 5 tiros a partir do nível 6);
      nível 5+  : esquadrões de 3 e a formação ganha a 5ª linha;
      nível 10  : 5 mergulhando juntos, tiros rápidos e FÚRIA ligada com 40% dos
                  inimigos vivos.
    FÚRIA: quando restam poucos inimigos, os sobreviventes enlouquecem:
    mergulham e atiram bem mais depressa (com um anel vermelho em volta).
    Depois da formação vem o CHEFÃO (veja ChefeGalaga).
    """
    n = max(0, min(NIVEL_MAXIMO - 1, nivel))
    return {
        'linhas': (3, 3, 4, 4, 4, 5, 5, 5, 5, 5)[n],
        'max_mergulhos': 2 + (n + 1)//3,                # mergulhando ao mesmo tempo
        'intervalo_mergulho': max(0.9, 1.8 - 0.10*n),   # s entre mergulhos (base)
        'duracao_mergulho': max(1.6, 2.6 - 0.12*n),     # s por mergulho (menos = mais rápido)
        'multiplicador_tiro': max(0.6, 1 - 0.045*n),    # encurta o intervalo (0,7 a 1,6 s) entre tiros
        'velocidade_tiro': min(400, VELOCIDADE_TIRO_INIMIGO + 13*n),
        'max_tiros': 5 + (2*n)//3,                      # tiros inimigos na tela
        'esquadrao': min(3, 1 + (n + 2)//3),            # 1, 2, 2, 2, 3...
        'persegue': 0.0 if n < 2 else min(0.8, 0.12*(n - 1)),
        'leque': 0 if n < 2 else (3 if n < 5 else 5),   # tiros do leque dos chefes de fileira
        'furia': min(0.4, 0.2 + 0.025*n),               # fração restante que liga a fúria
        'balanco': min(60, 30 + 4*n),                   # amplitude do balanço (px)
        'freq_balanco': min(1.6, 0.9 + 0.08*n),
        'tempo': TEMPO_GALAGA + 3*n,                    # limite de tempo da formação (s)
    }

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
        self.persegue = 0.0         # [MELHORIA 3] quanto o mergulho acompanha a nave
        self.furioso = False        # [MELHORIA 3] fúria: desenha o anel vermelho

    def comecar_entrada(self):
        """Define uma curva que nasce num canto superior e passa pelo meio."""
        canto = random.choice((-50, LARGURA+50))
        self.p0 = (canto, -50)
        self.p1 = (random.randint(100, LARGURA-100), ALTURA*0.55)
        self.estado, self.t, self.duracao = 'ENTRADA', 0.0, 1.5

    def mergulhar(self, alvo_x, duracao, atraso=0.0, persegue=0.0, lado=None):
        """Ataque: sai de lado, faz a curva e fecha sobre a posição da nave.

        [MELHORIA 3] atraso: espera (s) antes de partir, para escalonar os
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
                # [MELHORIA 3] Perseguição: o ponto de chegada desliza na
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
            # [MELHORIA 3] Anel vermelho: este inimigo está em FÚRIA.
            pygame.draw.ellipse(tela, (255, 60, 40), self.retangulo().inflate(8, 8), 2)

class ChefeGalaga:
    """[V4.3] Chefão da Galaga, inspirado no "Boss Galaga" do jogo original (o
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

    def __init__(self, sprites, nivel):
        self.sprite, self.sprite_flash = sprites
        self.nivel = nivel
        self.hp_max = 24 + 4*nivel            # 24 PV no nível 1 ... 60 PV no nível 10
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
        self.vel_tiro = 250 + 12*nivel
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
        return max(0.9, 2.4 - 0.15*self.nivel)*(0.75 if self.fase == 2 else 1.0)

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
                k = 5 + self.nivel//3
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
            aviso = max(0.8, 1.2 - 0.04*self.nivel)
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
            self.novas_escoltas += 3 + self.nivel//4
        # Movimento horizontal: vai e vem; no RAIO, alinha com a nave e trava.
        vel = 150 + 10*self.nivel
        if self.ataque == 'RAIO' and not self.raio_travado and self.raio_estado == 'AVISO':
            alvo, vel = nave_x, 320
        elif self.ataque == 'RAIO':
            alvo = self.x                        # travado (aviso final e raio ligado)
        else:
            alvo = LARGURA/2 + 170*math.sin(self.tempo*(0.55 + 0.04*self.nivel))
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

    [MELHORIA 3] A dificuldade depende de quantas vezes a fase já apareceu
    (parâmetro nivel; veja parametros_galaga).
    [MELHORIA 2] A fase é BÔNUS: não soma pontos ao placar; concluir dá vidas extras.

    Comunicação com a classe Jogo (sem a FaseGalaga conhecer o Jogo):
      - vidas_ganhas: vidas extras a somar (só quando a fase é CONCLUÍDA);
      - sons: nomes de efeitos a tocar;
      - dano: True quando a nave foi atingida neste quadro;
      - terminou: True quando a fase acabou e o Jogo deve voltar ao Flappy.
    """
    def __init__(self, recursos, nivel=0):
        self.recursos = recursos
        self.nivel = nivel          # 0 na primeira vez; aumenta a dificuldade
        self.cfg = parametros_galaga(nivel)    # [MELHORIA 3]
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
        self.vidas_ganhas = 0       # [MELHORIA 2] vidas extras a entregar ao Jogo
        self.abates = 0             # inimigos derrubados (estatística; NÃO soma pontos)
        self.sons = []
        self.dano = False
        self.terminou = False
        self.resultado = None       # None, 'VITORIA' ou 'TEMPO'
        self.tempo_resultado = 0.0
        self.mensagem = ''
        self.proximo_mergulho = 3.5     # só mergulham após a entrada
        self.proximo_tiro_inimigo = 2.5
        self.furia = False          # [MELHORIA 3] ligada quando restam poucos inimigos
        self.tempo_msg_furia = 0.0
        self.inimigos = []
        self._criar_formacao()
        self.total_inicial = len(self.inimigos)
        # [V4.3] A fase tem dois estágios: 'FORMACAO' (a fase de sempre) e 'CHEFE'.
        self.estagio = 'FORMACAO'
        self.chefe = None
        self.escoltas = []          # pássaros convocados pelo chefão (mergulham uma vez)
        self.tempo_estagio = 0.0    # tempo decorrido no estágio do chefão
        self._cd_explosao = 0.0
        # [BÔNUS] Power-ups da Galaga: CAÇA GÊMEO, BOMBA NOVA e PROPULSOR TURBO.
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

        [MELHORIA 3] A amplitude e a velocidade do balanço crescem com o nível.
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
        """[BÔNUS] Caixa de colisão da nave (um pouco menor que o sprite: mais justa).
        Com o Caça Gêmeo ela cobre as DUAS naves: o preço do tiro duplo."""
        ret = self.retangulo_nave()
        if self.gemeo:
            ret = ret.inflate(2*DESLOC_GEMEO, 0)
        return ret.inflate(-14, -18)

    @property
    def velocidade_nave(self):
        """[BÔNUS] Velocidade horizontal da nave (o Turbo a deixa 35% mais rápida)."""
        return VELOCIDADE_NAVE*(TURBO_VEL_NAVE if self.efeitos.ativo('TURBO') else 1.0)

    def reposicionar_jogador(self):
        """Chamado pelo Jogo após perder uma vida (mas ainda restam vidas).
        [BÔNUS] Perder uma vida zera os bônus (Gêmeo, Turbo e superaquecimento)."""
        self.nave_x = LARGURA/2
        self.alvo_x = None
        self.tiros = [t for t in self.tiros if t.do_jogador]
        self.efeitos.limpar()
        self.gemeo = False
        self.esfriando = 0.0

    def atirar(self):
        """Dispara respeitando o intervalo mínimo e o limite de tiros.

        [BÔNUS] CAÇA GÊMEO: cada disparo sai em par (um de cada nave) e o limite de tiros
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
        """Remove o inimigo (explosão + som). [ALTERADO] Não devolve mais pontos.
        [BÔNUS] A cada BONUS_ABATES_POR_CAPSULA abates (com som) solta uma cápsula."""
        self.inimigos.remove(inimigo)
        self.explosoes.append(Explosao(inimigo.x, inimigo.y))
        if som:
            self.abates += 1
            self.sons.append('ponto')
            self.abates_desde_capsula += 1
            if self.abates_desde_capsula >= BONUS_ABATES_POR_CAPSULA:
                self.abates_desde_capsula = 0
                self.soltar_capsula(inimigo.x, inimigo.y)

    # ------------------------------------------------------------
    # [BÔNUS] CAÇA GÊMEO, BOMBA NOVA e PROPULSOR TURBO
    # ------------------------------------------------------------
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
        """[MELHORIA 3] O líder mergulha junto com vizinhos da mesma linha.

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
        (linha 0) atiram em LEQUE: 3 tiros abertos de uma vez. [MELHORIA 3]"""
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
        [BÔNUS] O laço original (formação ou chefão) continua em _atualizar_nucleo."""
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
            self.nave_x += direcao*self.velocidade_nave*dt     # [BÔNUS] o Turbo acelera a nave
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
            # [V4.3] Formação derrubada: a luta contra o chefão tem o seu próprio laço.
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

        # [MELHORIA 3] FÚRIA: com poucos inimigos vivos, os sobreviventes
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
            caixa = self.caixa_colisao()     # [BÔNUS] com o Caça Gêmeo cobre as duas naves
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
            # [ALTERADO] [V4.3] Formação derrubada: agora vem o CHEFÃO. A vida extra
            # [MELHORIA 2] só é dada quando o chefão é derrotado.
            self._iniciar_chefe()
        elif self.tempo >= self.tempo_limite:
            self.resultado = 'TEMPO'
            self.mensagem = 'TEMPO ESGOTADO'
            self.tiros = []

    # ------------------------------------------------------------
    # [V4.3] ESTÁGIO DO CHEFÃO
    # ------------------------------------------------------------
    def _iniciar_chefe(self):
        """A formação acabou: o Boss Galaga entra em cena."""
        self.estagio = 'CHEFE'
        self.tempo_estagio = 0.0
        self.chefe = ChefeGalaga((self.recursos.chefe_galaga, self.recursos.chefe_galaga_flash),
                                 self.nivel)
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
        e.mergulhar(self.nave_x, max(1.6, 2.6 - 0.1*self.nivel), atraso=random.random()*0.5,
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
            caixa = self.caixa_colisao()     # [BÔNUS] com o Caça Gêmeo cobre as duas naves
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
            self.vidas_ganhas += VIDAS_POR_FASE_ESPECIAL            # [MELHORIA 2]
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
        if self.aviso_bonus_t > 0:                 # [BÔNUS] dica do bônus recém-coletado
            return self.aviso_bonus
        if self.estagio == 'FORMACAO' and self.tempo < 5:
            return 'SETAS ou A/D: mover | ESPACO ou clique: atirar'
        if self.estagio == 'CHEFE' and self.tempo_estagio < 5:
            return 'Cuidado com o RAIO TRATOR: saia de baixo dele!'
        return ''

    def desenhar(self, tela):
        tela.fill((6, 6, 28))
        for x, y, velocidade, tamanho in self.estrelas:
            brilho = min(255, 100 + int(velocidade))
            pygame.draw.rect(tela, (brilho, brilho, brilho),
                             (int(x), int(y), tamanho, tamanho))
        for inimigo in self.inimigos:
            inimigo.desenhar(tela)
        for inimigo in self.escoltas:          # [V4.3] pássaros convocados
            inimigo.desenhar(tela)
        if self.chefe:                         # [V4.3] chefão, raio trator e barra de vida
            self.chefe.desenhar(tela)
        for tiro in self.tiros:
            tiro.desenhar(tela)
        for explosao in self.explosoes:
            explosao.desenhar(tela)
        # A nave pisca (aparece/some) enquanto está invulnerável.
        # [BÔNUS] Com o Caça Gêmeo são duas naves lado a lado; com o Turbo ganham chamas.
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


# ================================================================
# 4C. [NOVO] OBJETOS DA FASE DONKEY KONG
# ================================================================
# Assim como a FaseGalaga, a FaseDonkey cuida de tudo que é interno a ela
# (obstáculos, barris, bananas, cenário, cronômetro) e só se comunica com
# o Jogo por atributos: vidas_ganhas, sons, dano e terminou.
#
# Diferença importante: a Galaga usa px/segundo (× dt), enquanto a fase
# Donkey mantém a física do Flappy original em px/QUADRO (o pássaro e os
# obstáculos andam uma quantidade fixa por quadro). Só o cronômetro da
# fase usa dt (segundos reais).

class ObstaculoSelva(Obstaculo):
    """[NOVO] Par temático: cipó pendurado no teto + pilha de barris no chão.

    Herda toda a lógica (posição, colisão por máscara, desenho) de Obstaculo;
    só troca os sprites, sobrescrevendo criar_sprites().
    """
    def criar_sprites(self, recursos, especial, tema):
        return recursos.selva_cipo, recursos.selva_barris

class BarrilRolante:
    """[ALTERADO] [MELHORIA 3] Barril ARREMESSADO por Kong em arco alto.

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
        #     vy0 = -g*n      e      y_apice = y0 - g*n*(n-1)/2
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
    """[NOVO] Coletável: encostar nela soma 1 ao contador de bananas da fase.

    [ALTERADO] [MELHORIA 2] Não vale pontos: as fases especiais são bônus.
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

def parametros_donkey(nivel):
    """[V4.3] Parâmetros de dificuldade do Donkey Kong para o nível do jogo
    (nivel = 0 no nível 1 ... 9 no nível 10).

    Travessia (barris entre as pilhas):
      - a rolagem fica mais rápida e a abertura entre as pilhas, menor;
      - Kong passa a arremessar SALVAS: 1 barril nos níveis 1-2; 2 barris nos
        níveis 3-5; 2 ou 3 barris (cada vez mais 3) do nível 6 em diante;
      - quase todo intervalo tem barril (a chance sobe até 100%) e Kong ergue o
        barril mais depressa (menos quadros de preparo): o "disparo" acelera;
      - nas salvas de 2 ou 3 barris, o pássaro passa por um TÚNEL livre entre os
        barris (altura 'faixa'), que estreita de 130 para 85 px.
    Chefão (Kong furioso): barris mais rápidos, bolas de fogo (a partir do nível 2)
    e mais rebites para coletar.
    """
    n = max(0, min(NIVEL_MAXIMO - 1, nivel))
    return {
        'velocidade': VELOCIDADE_DONKEY + 0.18*n,           # 5,0 -> 6,6 px/quadro
        'abertura': ABERTURA_DONKEY - 6*n,                  # 300 -> 246 px
        'chance_barril': min(1.0, CHANCE_BARRIL + 0.1*n),   # 50% -> 100%
        'salva_min': 1 if n < 2 else 2,
        'salva_max': 1 if n < 2 else (2 if n < 5 else 3),
        'chance_tres': 0.0 if n < 5 else (0.5 if n < 7 else 0.8),
        'faixa': 130 - 5*n,                                 # túnel livre (px) entre os barris
        'antecipacao': max(8, FRAMES_ANTECIPACAO_KONG - n//2),   # quadros de preparo (14 -> 10)
        # --- chefão ---
        'rebites': 4 + n//4,                                # 4, 4, 4, 4, 5, 5, 5, 5, 6, 6
        'chefe_intervalo': max(1.4, 3.2 - 0.2*n),           # s entre ataques
        'chefe_barris': 2 if n < 3 else 3,
        'chefe_vel_barril': 5.5 + 0.2*n,                    # px/quadro
        'chefe_vel_fogo': 8.0 + 0.3*n,
    }

class BolaDeFogo:
    """[V4.3] "Chama viva" do Donkey Kong: voa para a esquerda ondulando de leve.
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
    """[V4.3] Rebite dourado: o ponto fraco da estrutura do Kong furioso (referência
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

    A fase tem dois estágios [V4.3]:
      1) TRAVESSIA: cipós + pilhas de barris (ObstaculoSelva) e Kong arremessando
         barris em arco ALTO entre as pilhas. A dificuldade vem do nível do jogo:
         salvas de 1, 2 ou 3 barris, rolagem mais rápida, abertura menor (veja
         parametros_donkey). Bananas flutuam nas passagens (só um contador).
      2) CHEFÃO "KONG FURIOSO": sem pilhas, em céu aberto. Kong, maior, ataca com
         salvas de barris (com um túnel livre), bolas de fogo avisadas por uma seta
         e fica mais rápido a cada rebite coletado. Para vencer, colete todos os
         REBITES dourados que passam voando (a estrutura desaba e Kong cai).
    Vencer o chefão dá +1 vida [MELHORIA 2]; a fase não soma pontos ao placar.

    Comunicação com a classe Jogo (a fase não conhece o Jogo):
      - vidas_ganhas: vidas extras a somar (só ao derrotar o chefão);
      - sons: nomes de efeitos a tocar;
      - dano: True quando o pássaro foi atingido neste quadro;
      - terminou: True quando a fase acabou e o Jogo deve voltar ao Flappy.
    """
    X_KONG = LARGURA - 80          # centro horizontal do Kong
    # Centro do barril quando Kong o segura sobre a cabeça (altura das mãos):
    # topo do sprite do Kong (Y_CHAO + 8 - 170) + metade da altura do barril (20).
    Y_MAO_KONG = Y_CHAO + 8 - 170 + 20
    # No chefão o Kong é 35% maior: mesma conta com o sprite ampliado.
    Y_MAO_CHEFE = Y_CHAO + 8 - int(170*1.35) + 27
    X_MAO_CHEFE = 500.0            # x de onde os barris saem no chefão

    def __init__(self, recursos, nivel=0):
        self.recursos = recursos
        self.nivel = nivel          # 0 no nível 1 do jogo ... 9 no nível 10
        self.cfg = parametros_donkey(nivel)
        self.tempo = 0.0
        self.velocidade = self.cfg['velocidade']
        self.chance_barril = self.cfg['chance_barril']
        self.obstaculos, self.barris, self.bananas = [], [], []
        self.bananas_coletadas = 0
        self.rolagem = 0.0          # quanto o cenário já andou (px)
        self.kong_lancando = 0.0    # tempo restante da pose "arremessou"
        self.carregando = False     # Kong segura um barril (preparo do arremesso)
        self.decidido = False       # já sorteou se haverá barril neste intervalo
        self.vidas_ganhas = 0       # [MELHORIA 2] vidas extras a entregar ao Jogo
        self.sons = []
        self.dano = False
        self.terminou = False
        self.resultado = None       # None, 'VITORIA' ou 'TEMPO'
        self.tempo_resultado = 0.0
        self.mensagem = ''
        # [V4.3] Estágio do chefão.
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
        # [BÔNUS] Power-ups do Donkey: BANANA-RANG e PULO DE MOLA.
        self.explosoes = []                 # o Donkey não tinha explosões; o Banana-rang as usa
        self.capsulas = []                  # CapsulaBonus a caminho (no máximo uma)
        self.efeitos = EfeitosAtivos()      # MOLA (temporizado)
        self.cargas = 0                     # cargas do Banana-rang
        self.bumerangues = []               # bumerangues em voo (no máximo um)
        self.marco_bananas = 0              # quantas cápsulas as bananas já geraram
        self.fisica_original = None         # (gravidade, impulso) guardados enquanto a Mola durar
        self.aviso_bonus, self.aviso_bonus_t = '', 0.0     # dica de 4 s ao coletar um bônus

    def reposicionar(self):
        """Chamado pelo Jogo após perder uma vida (mas ainda restam vidas):
        limpa a pista para o jogador recomeçar sem colisões imediatas."""
        self.obstaculos, self.barris, self.bananas = [], [], []
        self.fogos, self.avisos_fogo, self.rebites = [], [], []
        self.carregando = False     # cancela um arremesso que estava em preparo
        self.decidido = False
        self.ataque = None
        self.preparo = 0.0
        # [BÔNUS] Perder uma vida zera os bônus (o pássaro novo já vem com a física normal).
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

    # ------------------------------------------------------------
    # [BÔNUS] BANANA-RANG e PULO DE MOLA
    # ------------------------------------------------------------
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
        desenhar_hud_bonus(tela, linhas)

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
        if self.aviso_bonus_t > 0:                 # [BÔNUS] dica do bônus recém-coletado
            return self.aviso_bonus
        if self.estagio == 'TRAVESSIA' and self.tempo < 5:
            return 'ESPACO ou clique: bater asas | desvie dos barris!'
        if self.estagio == 'CHEFE' and self.tempo_chefe < 5:
            return 'Pegue os REBITES dourados! Cuidado com barris e chamas.'
        return ''

    # ------------------------------------------------------------
    # TRAVESSIA: barris arremessados em arco alto, em salvas de 1 a 3
    # ------------------------------------------------------------
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

        k = 1: como antes, no centro da passagem seguinte (± DESVIO_APICE_BARRIL).
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
        """[JUSTIÇA] [FUSÃO] Topo da próxima passagem, sem exigir uma subida impossível
        em relação à passagem anterior (helpers do main__3_)."""
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
                              topo=self._sortear_topo(anterior, passaro))   # [JUSTIÇA]
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
        # ergue o barril. [V4.3] O preparo fica mais curto nos níveis altos.
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
            self._iniciar_chefe()

    # ------------------------------------------------------------
    # CHEFÃO: Kong furioso (rebites, salvas de barris e bolas de fogo)
    # ------------------------------------------------------------
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
        if self.nivel >= 1:
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
            quantas = 1 + (1 if self.nivel >= 3 else 0) + (1 if self.nivel >= 7 else 0)
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
            self.vidas_ganhas += VIDAS_POR_FASE_ESPECIAL              # [MELHORIA 2]
            self.mensagem = f'KONG DERROTADO!\n{texto_vidas_extras()}'
            self.barris, self.fogos, self.avisos_fogo, self.rebites = [], [], [], []
            self.dano = False                 # a vitória cancela uma colisão do mesmo quadro
        elif self.tempo_chefe >= TEMPO_CHEFE_DONKEY:
            self.resultado = 'TEMPO'
            self.mensagem = 'O KONG ESCAPOU!'
            self.barris, self.fogos, self.avisos_fogo, self.rebites = [], [], [], []

    # ------------------------------------------------------------
    # Laço da fase
    # ------------------------------------------------------------
    def atualizar(self, dt, passaro):
        """Um quadro da fase. O pássaro já foi atualizado pelo Jogo."""
        self.kong_lancando = max(0.0, self.kong_lancando - dt)
        self.tremor = max(0.0, self.tremor - dt)
        self._atualizar_bonus(dt, passaro)      # [BÔNUS] timers, Mola, cápsulas e bumerangues
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

    # ------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------
    def desenhar(self, tela, passaro):
        """Desenha, de trás para frente: céu, palmeiras, Kong, obstáculos,
        barris, bananas/rebites, chamas, chão e, por último, o pássaro."""
        r = self.recursos
        tela.blit(r.fundo_selva, (0, 0))
        # Parallax: camadas distantes andam mais devagar que as próximas.
        for camada, fator in ((r.palmeiras_longe, 0.15), (r.palmeiras_perto, 0.35)):
            x = -int(self.rolagem*fator) % LARGURA
            tela.blit(camada, (x - LARGURA, 0))
            tela.blit(camada, (x, 0))
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
        self._desenhar_bonus(tela, passaro)      # [BÔNUS]
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

# ================================================================
# 5. CLASSE JOGO — ESTADOS, EVENTOS E LOOP PRINCIPAL
# ================================================================
# MENU: tela inicial; JOGO: simulação ativa; GAMEOVER: encerramento.
# GALAGA: fase especial em que o jogo vira um "Galaga".
# [NOVO] ALERTA: aviso de 5 s (banner + contagem regressiva) que antecede
#        toda fase especial; a cena do Flappy fica congelada e sem dano.
# [NOVO] DONKEY: fase especial temática, com barris, cipós e bananas.
# [MELHORIA 4] CADASTRO: tela onde o jogador digita o nome antes de cada partida.
# [V4.2] VITORIA: tela de "Honra Máxima", exibida ao concluir o nível 10.
# A separação por estados evita que a mesma tecla execute ações
# incompatíveis em diferentes momentos.
class Jogo:
    """Coordena janela, recursos, física, entrada e desenho das telas."""
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        escala = min(info.current_w*FATOR_TELA/LARGURA,
                     info.current_h*FATOR_TELA/ALTURA, 1.0)
        self.tamanho = (max(1,int(LARGURA*escala)),max(1,int(ALTURA*escala)))
        self.janela = pygame.display.set_mode(self.tamanho,pygame.RESIZABLE)
        pygame.display.set_caption('Flappy Bird — Sprint 04 ampliada')
        self.tela = pygame.Surface((LARGURA,ALTURA))
        self.relogio = pygame.time.Clock()
        self.recursos = Recursos()
        pygame.display.set_icon(self.recursos.passaros['dia'][0])
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_grande = pygame.font.Font(None, 52)
        # [NOVO] Fontes maiores para o banner do alerta e a contagem regressiva.
        self.fonte_banner = pygame.font.Font(None, 88)
        self.fonte_contagem = pygame.font.Font(None, 200)
        # [MELHORIA 4] Fontes da tabela do ranking.
        self.fonte_tabela = pygame.font.Font(None, 22)
        self.fonte_titulo_tabela = pygame.font.Font(None, 28)
        self.som_ativo = True
        # [ALTERADO] [MELHORIA 4] Em vez de um único recorde, carrega o ranking
        # completo e o nome do último jogador (sugestão no cadastro).
        self.ranking, self.jogador = ler_ranking()
        self.atualizar_recorde()
        self.reiniciar()

    def tocar(self, nome, volume=0.5):
        efeito = self.recursos.sons.get(nome)
        if self.som_ativo and efeito is not None:
            efeito.set_volume(volume)
            efeito.play()

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
        # [MELHORIA 4] Cadastro e ranking. O nome do jogador (self.jogador) NÃO é
        # apagado aqui: ele vale também para a próxima partida.
        self.nome_digitado = ''              # texto do campo de cadastro
        self.erro_nome_ate = 0.0             # até quando mostrar o aviso "digite um nome"
        self.posicao_final = None            # posição desta partida no ranking
        self.fim_iniciado = 0.0
        self.ultimo_arcade = 0.0
        self.contador_arcade = 0
        # [V4.2] Ciclos (níveis): cada nível tem duas fases especiais (nos múltiplos
        # de 35 pontos) e, 20 pontos depois delas, a fase dos pássaros (veja
        # definir_nivel). self.especial passa a significar "fase dos pássaros ativa".
        self.nivel = 1
        self.pendentes = []                 # fases especiais que ainda faltam neste ciclo
        self.proximo_especial = PONTOS_ENTRE_ESPECIAIS   # próxima pontuação-gatilho
        self.pontos_para_passaros = None    # pontuação que libera a fase dos pássaros
        self.fim_passaros_em = None         # pontuação em que a fase dos pássaros acaba
        self.definir_nivel(1)
        # [NOVO] Estado do alerta de 5 s que antecede a fase.
        self.variante_alerta = None                    # 'GALAGA' ou 'DONKEY'
        self.alerta_restante = 0.0                     # s que faltam para a fase começar
        self.alerta_decorrido = 0.0                    # s desde o início (anima o banner)
        self.alerta_ultimo_numero = 0                  # último número "bipado" na contagem
        # Controle de cada variante de fase.
        self.galaga = None                     # objeto FaseGalaga (ou None)
        self.donkey = None                     # objeto FaseDonkey (ou None)
        # [V4.2] Banner temporário do modo clássico (subida de nível, fase dos pássaros).
        self.banner = ('', '', (255, 255, 255))
        self.banner_tempo = 0.0
        # [V4.2] Tela de Honra Máxima: partículas dos fogos de artifício.
        self.fogos = []
        self.proximo_fogo = 0.0
        # [FUSÃO] Partida em que algum atalho de teste foi usado: não entra no ranking.
        self.modo_teste_usado = False
        self.tocar('inicio')

    def iniciar(self):
        self.estado = 'JOGO'
        self.tempo_ativo = 0.0
        self.obstaculos = [self.novo_obstaculo()]      # [ALTERADO] já com a abertura do nível
        if self.recursos.sons['inicio']:
            self.recursos.sons['inicio'].stop()

    # -----------------------------------------------------------
    # [MELHORIA 4] CADASTRO DO JOGADOR (antes de cada partida)
    # -----------------------------------------------------------
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
            self.erro_nome_ate = time.monotonic() + 1.5   # aviso vermelho por 1,5 s
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

        [ALTERADO] [V4.2] O registro guarda também o nível alcançado e se o
        jogador zerou o jogo (zerou=True na tela de Honra Máxima).
        """
        if self.modo_teste_usado and ATALHO_INVALIDA_RANKING:
            self.posicao_final = None       # [FUSÃO] partida com atalho de teste não vale recorde
            return
        nome = self.jogador or 'Anônimo'
        self.ranking, self.posicao_final = adicionar_registro(
            self.ranking, nome, self.pontos, self.nivel, zerou)
        self.atualizar_recorde()
        salvar_ranking(self.ranking, self.jogador)

    # -----------------------------------------------------------
    # [MELHORIA 1] DIFICULDADE PROGRESSIVA (modo clássico)
    # -----------------------------------------------------------
    @property
    def params_nivel(self):
        """[V4.2] Parâmetros do nível atual (gravidade, abertura, velocidade...).
        Veja parametros_nivel() para a tabela dos 10 níveis."""
        return parametros_nivel(self.nivel)

    def gravidade_atual(self):
        """Gravidade do nível atual."""
        return self.params_nivel['gravidade']

    def abertura_atual(self):
        """Abertura entre os canos do nível atual."""
        return self.params_nivel['abertura']

    def novo_passaro_classico(self):
        """Pássaro do modo clássico, já com a gravidade do nível atual."""
        passaro = Passaro(self.recursos)
        passaro.aplicar_dificuldade(self.gravidade_atual())
        return passaro

    def novo_obstaculo(self):
        """Par de canos (ou de pássaros, na fase dos pássaros) nascendo na borda
        direita, com a abertura e a velocidade do nível. [V4.2] Na fase dos
        pássaros dos níveis altos a passagem também sobe e desce."""
        p = self.params_nivel
        oscilacao = p['oscilacao_passaros'] if self.especial else 0.0
        # [JUSTIÇA] [FUSÃO] A altura da passagem nunca fica tão distante da anterior que a
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

    # -----------------------------------------------------------
    # [V4.2] CICLOS (NÍVEIS): especiais por pontuação, fase dos pássaros e vitória
    # -----------------------------------------------------------
    def ordem_especiais(self, nivel):
        """As duas fases especiais do ciclo, na ordem em que aparecem: os níveis
        ímpares começam pelo Donkey Kong; os pares, pela Galaga."""
        ordem = list(ORDEM_FASES_ESPECIAIS)
        return ordem if nivel % 2 == 1 else ordem[::-1]

    def definir_nivel(self, nivel):
        """Começa o ciclo de um nível: zera o progresso do ciclo e recalcula os
        gatilhos. A pontuação NÃO é alterada. A dificuldade do modo clássico vem
        de self.nivel (parametros_nivel), então ela muda junto."""
        self.nivel = max(1, min(NIVEL_MAXIMO, int(nivel)))
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

    # -----------------------------------------------------------
    # [NOVO] FASES ESPECIAIS: gatilho -> alerta de 5 s -> fase -> volta
    # -----------------------------------------------------------
    def verificar_gatilhos(self):
        """[ALTERADO] [V4.2] Decide, a cada quadro do modo clássico, o próximo passo do ciclo.

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
        depois que a fase termina. [ALTERADO] [V4.2] A dificuldade da fase vem do
        NÍVEL do jogo (self.nivel - 1 = 0 a 9), e a fase dos pássaros também
        passa por aqui (variante 'PASSAROS').
        """
        if variante == 'PASSAROS':
            self.iniciar_fase_passaros()
            return
        self.obstaculos = []
        # Zera a trava de dano do Flappy para não ignorar um dano da fase nova.
        self.ultimo_dano = -TEMPO_INVULNERAVEL_MS
        if variante == 'DONKEY':
            self.estado = 'DONKEY'
            self.donkey = FaseDonkey(self.recursos, self.nivel - 1)
            self.passaro = self.novo_passaro_donkey()
        else:
            self.estado = 'GALAGA'
            self.galaga = FaseGalaga(self.recursos, self.nivel - 1)

    def iniciar_fase_passaros(self):
        """[V4.2] Começa a fase dos pássaros: o Flappy volta com PÁSSAROS no lugar
        dos canos e os pontos contam normalmente. Ela dura 'pontos_passaros'
        pontos; nos níveis altos os pássaros sobem e descem. Enquanto ela durar,
        as fases especiais não são acionadas."""
        self.especial = True
        faltam = self.params_nivel['pontos_passaros']
        self.fim_passaros_em = self.pontos + faltam
        self.estado = 'JOGO'
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        self.ultimo_dano = pygame.time.get_ticks()
        self.mostrar_banner('FASE DOS PÁSSAROS!', f'passe por {faltam} pássaros: vale pontos',
                            (255, 225, 90))

    def novo_passaro_donkey(self):
        """Pássaro "noturno" no ponto de partida, combinando com a selva escura."""
        passaro = Passaro(self.recursos)
        passaro.familia = 'noite'
        return passaro

    def encerrar_fase_especial(self):
        """Volta ao Flappy Bird, preservando pontos, vidas e tempo.

        [ALTERADO] [V4.2] Também avança o ciclo: se ainda há fase especial
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
        self.ultimo_dano = pygame.time.get_ticks()
        if self.pendentes:
            self.proximo_especial = proximo_multiplo(self.pontos)
        else:
            self.pontos_para_passaros = self.pontos + PONTOS_ANTES_PASSAROS

    def concluir_ciclo(self):
        """[V4.2] Fim da fase dos pássaros = fim do ciclo: sobe de nível, ou, se
        era o nível 10, vence o jogo (tela de HONRA MÁXIMA)."""
        self.especial = False
        if self.nivel >= NIVEL_MAXIMO:
            self.vitoria_final()
            return
        self.definir_nivel(self.nivel + 1)
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        self.ultimo_dano = pygame.time.get_ticks()
        self.mostrar_banner(f'NÍVEL {self.nivel}!', 'mais gravidade, velocidade e canos fechados')

    def ir_para_nivel(self, nivel):
        """[V4.4] ATALHO DE TESTE (teclas 1 a 9 e 0): muda NA HORA para o nível.

        Cancela o alerta ou a fase em andamento, recomeça o ciclo do nível
        (fases pendentes e gatilhos) e aplica ao modo clássico a gravidade, a
        abertura e a velocidade daquele nível. Os pontos não mudam."""
        self.galaga = None
        self.donkey = None
        self.estado = 'JOGO'
        self.definir_nivel(nivel)
        self.passaro = self.novo_passaro_classico()
        self.obstaculos = [self.novo_obstaculo()]
        self.ultimo_dano = pygame.time.get_ticks()
        self.mostrar_banner(f'NÍVEL {self.nivel}!', '(atalho de teste)')

    def pular_para_chefe(self):
        """[V4.4] ATALHO DE TESTE (tecla B): pula a 1ª parte da Galaga ou do Donkey."""
        fase = self.galaga if self.estado == 'GALAGA' else self.donkey
        if fase:
            fase.pular_para_chefe()

    def vitoria_final(self):
        """[V4.2] Nível 10 concluído: grava a pontuação (marcada como "zerou") e
        mostra a tela de HONRA MÁXIMA."""
        self.estado = 'VITORIA'
        self.especial = False
        self.fim_iniciado = time.monotonic()
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

        [ALTERADO] [MELHORIA 4] Antes pedia o nome só se houvesse novo recorde;
        agora o nome vem do cadastro (feito antes da partida) e TODA partida com
        pontos entra no ranking.
        """
        self.estado = 'GAMEOVER'
        self.fim_iniciado = time.monotonic()
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
        elif self.estado == 'GALAGA':
            # Na Galaga, a nave volta ao centro; a formação continua.
            self.galaga.reposicionar_jogador()
        elif self.estado == 'DONKEY':
            # [NOVO] Na fase Donkey, o pássaro recomeça e a pista é limpa;
            # o cronômetro da fase continua de onde estava.
            self.passaro = self.novo_passaro_donkey()
            self.donkey.reposicionar()
        else:
            # Reinicia o pássaro e obstáculos, preservando pontos/tempo.
            # [ALTERADO] [MELHORIA 1] Já com a gravidade e a abertura do nível.
            self.passaro = self.novo_passaro_classico()
            self.obstaculos = [self.novo_obstaculo()]

    def tema_por_tempo(self):
        """Escolhe cenário e fase pelo tempo ativo, sem contar pausas."""
        # [ALTERADO] [V4.2] O tempo só escolhe o CENÁRIO (um tema novo a cada
        # TEMPO_TEMA s). Quem decide a fase dos pássaros é o ciclo por pontos.
        indice = int(self.tempo_ativo // TEMPO_TEMA)
        self.tema = TEMAS[indice % len(TEMAS)]
        self.passaro.familia = ('dia' if self.tema in TEMAS_DIA else
                                'tarde' if self.tema in TEMAS_TARDE else 'noite')

    def aplicar_efeitos_fase(self, fase, estado_fase, agora_ms):
        """[ALTERADO] [MELHORIA 2] Aplica no Jogo o que a fase produziu neste
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
        """[NOVO] Um quadro da fase Galaga: lê teclas, atualiza e aplica efeitos."""
        g = self.galaga
        # get_pressed() informa as teclas que estão seguradas AGORA,
        # ideal para movimento contínuo (os eventos KEYDOWN disparam uma vez).
        teclas = pygame.key.get_pressed()
        esquerda = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        direita = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]
        g.atualizar(dt, esquerda, direita, teclas[pygame.K_SPACE])
        self.aplicar_efeitos_fase(g, 'GALAGA', agora_ms)

    def atualizar_donkey(self, dt, agora_ms):
        """[NOVO] Um quadro da fase Donkey Kong: física do pássaro + fase."""
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
        # [ALTERADO] A pausa vale para todos os estados ativos (JOGO, ALERTA,
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
        if self.estado == 'VITORIA':          # [V4.2] fogos de artifício da tela final
            self.atualizar_vitoria(dt)
            return
        if self.estado != 'JOGO':
            return
        self.tempo_ativo += dt
        self.tema_por_tempo()
        # [ALTERADO] [V4.2] A cada quadro o pássaro recebe a gravidade (e o impulso)
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
        # [ALTERADO] [V4.2] O banner some depois de 2,5 s; em seguida o ciclo decide
        # se chegou a hora de uma fase especial, da fase dos pássaros ou do próximo nível.
        self.banner_tempo = max(0.0, self.banner_tempo - dt)
        self.verificar_gatilhos()

    def texto(self, mensagem, x, y, cor=(255,255,255), grande=False, centro=False):
        """Renderiza texto; centro=True centraliza horizontalmente em x."""
        fonte = self.fonte_grande if grande else self.fonte
        img = fonte.render(str(mensagem),True,cor)
        self.tela.blit(img, (x-img.get_width()//2 if centro else x,y))

    def texto_destaque(self, mensagem, x, y, cor, fonte, escala=1.0, fundo=False):
        """[NOVO] Texto com sombra, centralizado em (x, y) (y = CENTRO do texto,
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
        """[NOVO] Faixa de listras amarelas e pretas (sinalização de perigo).
        'deslocamento' faz as listras correrem para o lado."""
        pygame.draw.rect(self.tela, (20, 20, 20), (0, y, LARGURA, altura))
        passo = 44
        inicio = -passo + int(deslocamento) % passo
        for x in range(inicio, LARGURA + passo, passo):
            pygame.draw.polygon(self.tela, (255, 205, 30),
                                [(x, y), (x + 22, y), (x + 22 - altura, y + altura),
                                 (x - altura, y + altura)])

    def desenhar_alerta(self):
        """[NOVO] Camada do estado ALERTA, desenhada sobre a cena congelada:
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
        """[NOVO] Placar do Flappy (pontos, vidas e medalha), reaproveitado
        pelos estados JOGO, ALERTA, GALAGA e DONKEY.

        [ALTERADO] [MELHORIA 2] As vidas podem passar de 6 (fase especial
        concluída = +1 vida): até MAX_ICONES_VIDA aparecem como ícones; acima
        disso, um ícone com o contador "xN".
        [MELHORIA 1] com_nivel=True mostra o nível de dificuldade do modo clássico.
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
            # [ALTERADO] [V4.2] Nível do ciclo (1 a 10) e o que falta para a próxima fase.
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
        """[ALTERADO] Mensagem grande no meio da tela durante uma fase especial.
        Um '\n' separa linhas: a 1ª é dourada e as demais (ex.: "+1 VIDA") verdes."""
        for i, linha in enumerate(mensagem.split('\n')):
            cor = (255,225,90) if i == 0 else (130,255,140)
            self.texto_destaque(linha, LARGURA//2, 400 + 58*i, cor, self.fonte_grande)

    def desenhar_vitoria(self):
        """[NOVO] [V4.2] Tela de HONRA MÁXIMA: fundo escuro com raios dourados
        girando, troféu desenhado com formas, fogos de artifício, a mensagem de
        parabéns e a tabela do ranking (a linha do jogador fica destacada)."""
        t = time.monotonic() - self.fim_iniciado
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
        """[NOVO] [MELHORIA 4] Tela de identificação, mostrada antes de cada partida."""
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
        cursor = '_' if int(time.monotonic()*2) % 2 == 0 else ' '
        texto = self.nome_digitado + cursor
        img = self.fonte_grande.render(texto,True,(30,30,40))
        if img.get_width() > campo.width-28:    # nome muito largo (ex.: WWWW...): fonte menor
            img = self.fonte.render(texto,True,(30,30,40))
        self.tela.blit(img,img.get_rect(midleft=(campo.x+14,campo.centery)))
        if time.monotonic() < self.erro_nome_ate:
            self.texto('Digite pelo menos um caractere!',LARGURA//2,470,
                       (255,90,90),centro=True)
        else:
            self.texto(f'Até {MAX_NOME} caracteres. Fica salvo no ranking.',
                       LARGURA//2,470,(200,200,200),centro=True)
        self.texto('ENTER: começar    DEL: limpar    ESC: voltar',LARGURA//2,520,
                   (255,225,90),centro=True)

    def desenhar_ranking(self):
        """[NOVO] [MELHORIA 4] Tabela Top 10 (posição, jogador e pontos).

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
        colunas = (x0+22, x0+75, x0+largura-130, x0+largura-24)   # [V4.2] coluna do nível
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
                # [V4.2] Nível alcançado ("ZEROU" para quem concluiu o nível 10).
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

    def desenhar(self):
        """Desenha o estado atual e apresenta o quadro na janela."""
        # Todas as posições abaixo usam a superfície lógica de 575 x 860.
        # Só ao final redimensionamos a imagem para a janela do usuário.
        fundo = self.recursos.fundos[self.tema if self.estado!='MENU' else 'bg']
        self.tela.blit(pygame.transform.scale(fundo,(LARGURA,ALTURA)),(0,0))
        if self.estado == 'MENU':
            self.chao.desenhar(self.tela)
            logo = self.recursos.logo
            self.tela.blit(logo,logo.get_rect(center=(LARGURA//2,300)))
            oscilacao = int(12*__import__('math').sin(time.monotonic()*3))
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
            self.desenhar_placar(com_nivel=True)   # [V4.2] mostra nível e progresso do ciclo
            if self.especial:
                # Fase dos pássaros (do ciclo): vale pontos normalmente, diferente
                # das fases especiais-bônus (Galaga e Donkey Kong).
                self.texto('FASE DOS PÁSSAROS!',LARGURA//2,95,(255,220,90),centro=True)
            if self.banner_tempo > 0:
                # [V4.2] Banner de 2,5 s (subida de nível / início da fase dos pássaros), pulsando.
                titulo, subtitulo, cor = self.banner
                pulso = 1.0 + 0.06*math.sin(self.banner_tempo*12)
                fonte = self.fonte_banner if len(titulo) <= 11 else self.fonte_grande
                self.texto_destaque(titulo,LARGURA//2,165,cor,fonte,pulso)
                if subtitulo:
                    self.texto_destaque(subtitulo,LARGURA//2,215,(255,255,255),self.fonte)
        elif self.estado == 'ALERTA':
            # [NOVO] A cena do Flappy fica congelada (mesmo desenho do JOGO,
            # sem o texto da fase por tempo) e o aviso é desenhado por cima.
            for obstaculo in self.obstaculos:
                obstaculo.desenhar(self.tela)
            self.chao.desenhar(self.tela)
            self.passaro.desenhar(self.tela)
            self.desenhar_placar(com_nivel=True)
            self.desenhar_alerta()
        elif self.estado == 'DONKEY':
            # [NOVO] A própria FaseDonkey desenha cenário, Kong, obstáculos,
            # barris, bananas, chão e pássaro. Aqui entram placar e textos.
            d = self.donkey
            d.desenhar(self.tela, self.passaro)
            self.desenhar_placar(com_medalha=False)
            if d.mensagem:
                self.desenhar_mensagem_fase(d.mensagem)
            # [ALTERADO] [V4.3] O texto de status e a dica vêm da própria fase (mudam no chefão).
            self.texto_destaque(d.texto_status, LARGURA//2, ALTURA-30, (255,255,255),
                                self.fonte, fundo=True)
            if d.dica:
                self.texto_destaque(d.dica, LARGURA//2, ALTURA-68, (220,220,220),
                                    self.fonte, fundo=True)
        elif self.estado == 'GALAGA':
            # [NOVO] A própria FaseGalaga desenha o cenário espacial (fundo,
            # inimigos, tiros, nave). Aqui entram o placar e os textos.
            g = self.galaga
            g.desenhar(self.tela)
            # A medalha fica de fora para não cobrir a primeira coluna.
            self.desenhar_placar(com_medalha=False)
            if g.mensagem:
                self.desenhar_mensagem_fase(g.mensagem)
            # [ALTERADO] [V4.3] O texto de status e a dica vêm da própria fase (mudam no chefão).
            self.texto(g.texto_status,LARGURA//2,ALTURA-35,centro=True)
            if g.dica:
                self.texto(g.dica,LARGURA//2,ALTURA-65,(200,200,200),centro=True)
        elif self.estado == 'VITORIA':
            # [V4.2] Tela de Honra Máxima (nível 10 concluído).
            self.desenhar_vitoria()
        elif self.estado == 'CADASTRO':
            # [MELHORIA 4] Tela para digitar o nome do jogador.
            self.desenhar_cadastro()
        else:  # GAMEOVER
            # Nesta tela, os elementos são posicionados em camadas:
            # chão, identificação do recordista, logotipo, moldura e placar.
            self.chao.desenhar(self.tela)
            # [ALTERADO] [MELHORIA 4] Cabeçalho: jogador cadastrado, pontuação e a
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
            decorrido = time.monotonic()-self.fim_iniciado
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
            # [ALTERADO] [MELHORIA 4] O antigo campo "digite seu nome" saiu: o nome
            # agora é informado no CADASTRO, antes da partida. Em seu lugar, a
            # tabela com os 10 melhores recordes (e o aviso de reiniciar).
            self.desenhar_ranking()
        # [ALTERADO] A camada de pausa vale para todos os estados ativos
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
            self.texto('P: Pausa | ESC: Sair',LARGURA-220,5)
        # [ALTERADO] Rótulo da barra: agora também informa a fase Galaga.
        if self.estado == 'GALAGA':
            rotulo = 'FASE GALAGA'
        elif self.estado == 'DONKEY':
            rotulo = 'FASE DONKEY'          # [NOVO] curto para não invadir o texto de pausa
        elif self.estado == 'ALERTA':
            rotulo = 'PREPARE-SE!'          # [NOVO]
        elif self.estado == 'VITORIA':
            rotulo = 'HONRA MÁXIMA'         # [V4.2]
        elif self.estado == 'CADASTRO':
            rotulo = 'CADASTRO'             # [MELHORIA 4]
        elif self.especial:
            rotulo = 'FASE PÁSSAROS'        # [ALTERADO] veja o texto "FASE DOS PÁSSAROS!"
        else:
            rotulo = 'Tema: '+self.tema
        self.texto(rotulo,165,5,(255,225,90))
        if self.modo_teste_usado:
            self.texto('[TESTE]',LARGURA//2,34,(255,110,110),centro=True)   # [FUSÃO] partida de teste
        # Renderização lógica 575x860 -> janela física sem alterar colisões.
        # A escala visual não altera a geometria lógica nem as colisões.
        ajustada = pygame.transform.scale(self.tela,self.janela.get_size())
        self.janela.blit(ajustada,(0,0))
        pygame.display.flip()

    def tratar_evento(self, evento):
        """Processa teclado, mouse, redimensionamento e saída.

        Retorna False para encerrar o loop principal do programa.
        """
        if evento.type == pygame.QUIT:
            return False
        if evento.type == pygame.VIDEORESIZE:
            self.janela = pygame.display.set_mode(
                (max(250,evento.w),max(350,evento.h)),pygame.RESIZABLE)
        # [NOVO] Na Galaga, o mouse também move a nave (posição horizontal).
        # Converte o x da janela (pixels reais) para o x lógico de 575 px.
        if (evento.type == pygame.MOUSEMOTION and self.estado == 'GALAGA'
                and self.galaga):
            self.galaga.alvo_x = evento.pos[0]*LARGURA/max(1,self.janela.get_width())
        if evento.type == pygame.KEYDOWN:
            # [MELHORIA 4] A digitação do nome vem ANTES de qualquer atalho
            # (S, P, G, K, T...), senão as letras do nome acionariam comandos.
            if self.estado == 'CADASTRO':
                return self.tratar_tecla_cadastro(evento)
            if evento.key == pygame.K_ESCAPE:
                return False
            if evento.key == pygame.K_s:
                self.som_ativo = not self.som_ativo
                if pygame.mixer.get_init():
                    if self.som_ativo: pygame.mixer.unpause()
                    else: pygame.mixer.pause()
            # [ALTERADO] A pausa vale em todos os estados ativos (inclui ALERTA e DONKEY).
            if evento.key == pygame.K_p and self.estado in ESTADOS_ATIVOS:
                self.pausado = not self.pausado
            # [ALTERADO] [V4.4] Atalhos de teste/cheat (só com MODO_TESTE = True). Este
            # trecho só é alcançado FORA do cadastro: lá, tratar_tecla_cadastro()
            # consome a tecla antes, por isso dá para digitar números no nome sem
            # mudar a dificuldade. Os atalhos de fase passam pelo ALERTA de 5 s, como
            # no jogo real, e NÃO alteram o cronograma de pontuação.
            if MODO_TESTE and self.estado in ESTADOS_ATIVOS and not self.pausado:
                self.tratar_atalho_teste(evento.key)
            # [BÔNUS] X lança o Banana-rang. Esta linha só é alcançada FORA do cadastro (o
            # return lá em cima trata a digitação do nome), então digitar "x" no nome é seguro.
            if (evento.key == pygame.K_x and self.estado == 'DONKEY' and self.donkey
                    and not self.pausado):
                self.donkey.lancar_bumerangue(self.passaro)
            # [FUSÃO] Este comando aparecia DUAS vezes no main__4_ (o espaço era tratado em
            # dobro: batia asas duas vezes e, no GAME OVER, pulava direto o menu).
            if evento.key == pygame.K_SPACE:
                self.acao_principal()
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (1,3):
            # Clique na barra superior não é comando de pulo.
            y_logico = evento.pos[1]*ALTURA/max(1,self.janela.get_height())
            if y_logico > 30 and self.estado != 'CADASTRO':
                self.acao_principal()
        return True

    def tratar_atalho_teste(self, tecla):
        """[V4.4] [FUSÃO] Atalhos de teste (só com MODO_TESTE = True, fora do cadastro):
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
        # [ALTERADO] [MELHORIA 4] Do menu vai para o CADASTRO; a partida só
        # começa depois que o jogador confirma o nome (ENTER).
        if self.estado == 'MENU': self.iniciar_cadastro()
        elif self.estado == 'JOGO' and not self.pausado:
            self.passaro.pular()
            self.tocar('pulo')
        # Na Galaga, o mesmo comando vira "atirar".
        elif self.estado == 'GALAGA' and not self.pausado:
            self.galaga.atirar()
        # [NOVO] Na fase Donkey, volta a ser "bater asas" (física do Flappy).
        # No ALERTA nenhum comando de jogo age: a cena está congelada.
        elif self.estado == 'DONKEY' and not self.pausado and not self.donkey.resultado:
            self.passaro.pular()
            self.tocar('pulo')
        # [ALTERADO] Ignora espaço/clique no primeiro segundo do GAME OVER: quem
        # morre apertando sem parar não "pula" a tabela do ranking sem ver.
        # [V4.2] A tela de HONRA MÁXIMA também reinicia (esperando 2,5 s, para a
        # comemoração e o ranking aparecerem).
        elif (self.estado in ('GAMEOVER', 'VITORIA')
              and time.monotonic() - self.fim_iniciado > (2.5 if self.estado == 'VITORIA' else 1.0)):
            self.reiniciar()

    def executar(self):
        """Loop principal: eventos, atualização, áudio e renderização.

        tick(FPS) controla a taxa de quadros e devolve o tempo decorrido.
        """
        rodando = True
        while rodando:
            dt = min(self.relogio.tick(FPS)/1000,0.1)
            for evento in pygame.event.get():
                if not self.tratar_evento(evento):
                    rodando = False
                    break
            if not rodando: break
            self.atualizar(dt,pygame.time.get_ticks())
            if self.estado == 'GAMEOVER' and self.contador_arcade < 3:
                agora = time.monotonic()
                if agora-self.fim_iniciado >= 3.5 and (self.ultimo_arcade == 0 or
                                                         agora-self.ultimo_arcade >= 2):
                    self.tocar('arcade')
                    self.ultimo_arcade = agora
                    self.contador_arcade += 1
            self.desenhar()
        pygame.quit()

# Este bloco só é executado quando o arquivo é iniciado diretamente.
# Ao importar o módulo em outro programa, a partida não começa sozinha.
if __name__ == '__main__':
    Jogo().executar()
