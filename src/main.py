# ============================================================
# PROJETO: FLAPPY BIRD
# DISCIPLINA: Programação para Engenharia Mecânica
# SPRINT 02: Física, salto e animação do pássaro
# ============================================================

# pathlib permite montar caminhos sem depender da pasta do terminal.
from pathlib import Path

# Biblioteca utilizada para janelas, eventos, imagens e desenho 2D.
import pygame


# ------------------------------------------------------------
# 1. CONFIGURAÇÕES DO JOGO
# ------------------------------------------------------------

# Resolução lógica de referência (independente do monitor).
LARGURA = 575
ALTURA = 860

# Limite de quadros por segundo.
FPS = 30

# Ocupa, no máximo, 85% das dimensões informadas pelo monitor.
FATOR_TELA = 0.85

# Parâmetros de movimento por quadro, em pixels lógicos.
GRAVIDADE = 1.1         # Incremento de velocidade a cada quadro.
IMPULSO = -8           # Velocidade vertical aplicada ao saltar.

# Coordenada vertical do topo do solo lógico.
ALTURA_SOLO = 760

# Número de quadros entre mudanças de sprite.
QUADROS_ANIMACAO = 5

# Localiza a raiz do projeto a partir deste arquivo (src/main.py).
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_IMAGENS = RAIZ_PROJETO / "assets" / "imgs"


# ------------------------------------------------------------
# 2. CLASSE RESPONSÁVEL PELO PÁSSARO
# ------------------------------------------------------------

class Passaro:
    """Armazena o estado e implementa o movimento do pássaro."""

    def __init__(self, imagens):
        # Lista de sprites que representam o bater de asas.
        self.imagens = imagens

        # Define posição inicial, usando números reais (float).
        self.x = 150.0
        self.y = 300.0

        # Começa em repouso vertical.
        self.velocidade_y = 0.0

        # Controla qual imagem será desenhada.
        self.indice_imagem = 0
        self.contador_animacao = 0

        # Obtém dimensões do sprite para tratar os limites.
        self.largura = imagens[0].get_width()
        self.altura = imagens[0].get_height()

    def pular(self):
        # No Pygame, velocidade negativa significa subir.
        self.velocidade_y = IMPULSO

    def atualizar(self):
        # Atualiza primeiro a velocidade e depois a posição.
        # Esse procedimento é um Euler semiexplícito simplificado.
        self.velocidade_y += GRAVIDADE
        self.y += self.velocidade_y

        # Impede que o pássaro ultrapasse o topo do cenário.
        if self.y < 0:
            self.y = 0
            self.velocidade_y = 0

        # Impede que a parte inferior atravesse o solo lógico.
        limite_inferior = ALTURA_SOLO - self.altura
        if self.y > limite_inferior:
            self.y = limite_inferior
            self.velocidade_y = 0

        # Conta os quadros para alternar os sprites.
        self.contador_animacao += 1
        if self.contador_animacao >= QUADROS_ANIMACAO:
            self.contador_animacao = 0
            self.indice_imagem = (
                self.indice_imagem + 1
            ) % len(self.imagens)

    def desenhar(self, superficie):
        # Escolhe a imagem correspondente ao quadro da animação.
        imagem = self.imagens[self.indice_imagem]

        # O desenho usa coordenadas inteiras em pixels lógicos.
        superficie.blit(imagem, (int(self.x), int(self.y)))


# ------------------------------------------------------------
# 3. CARREGAMENTO DAS IMAGENS
# ------------------------------------------------------------

def carregar_imagens():
    """Carrega os três sprites e preserva a transparência PNG."""

    imagens = []

    # Percorre os nomes dos três arquivos enviados.
    for numero in (1, 2, 3):
        caminho = PASTA_IMAGENS / f"bird{numero}.png"

        # Informa claramente quando falta algum arquivo.
        if not caminho.is_file():
            raise FileNotFoundError(
                f"Sprite não encontrado: {caminho}\n"
                "Copie bird1.png, bird2.png e bird3.png "
                "para assets/imgs/."
            )

        # convert_alpha() preserva transparência e otimiza desenho.
        imagem = pygame.image.load(str(caminho)).convert_alpha()
        imagens.append(imagem)

    return imagens


# ------------------------------------------------------------
# 4. FUNÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():
    # Inicializa os módulos do Pygame.
    pygame.init()

    # Consulta a resolução informada pelo monitor.
    info = pygame.display.Info()
    largura_monitor = info.current_w
    altura_monitor = info.current_h

    # Calcula o fator de escala sem ultrapassar o tamanho lógico.
    escala_largura = largura_monitor * FATOR_TELA / LARGURA
    escala_altura = altura_monitor * FATOR_TELA / ALTURA
    escala = min(escala_largura, escala_altura, 1.0)

    # Obtém as dimensões físicas da janela (em pixels inteiros).
    largura_janela = int(LARGURA * escala)
    altura_janela = int(ALTURA * escala)

    # Cria a janela física adaptada ao monitor.
    tela = pygame.display.set_mode((largura_janela, altura_janela))
    pygame.display.set_caption("Flappy Bird — Sprint 02")

    # Cria uma superfície com resolução lógica FIXA.
    cenario = pygame.Surface((LARGURA, ALTURA))

    # As imagens são carregadas após a criação da janela.
    imagens = carregar_imagens()
    passaro = Passaro(imagens)

    # Cria o relógio e a variável de controle do loop.
    relogio = pygame.time.Clock()
    executando = True

    # --------------------------------------------------------
    # 5. LOOP PRINCIPAL DO JOGO
    # --------------------------------------------------------

    while executando:
        # 5.1. Processamento dos eventos do sistema e do teclado.
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False

            # Um evento KEYDOWN de Espaço produz um salto.
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    passaro.pular()

        # 5.2. Atualização da física e da animação.
        passaro.atualizar()

        # 5.3. Desenho em coordenadas lógicas.
        cenario.fill((135, 206, 235))  # Fundo azul-claro.

        # Representa o solo com um retângulo verde.
        pygame.draw.rect(
            cenario,
            (70, 160, 80),
            (0, ALTURA_SOLO, LARGURA, ALTURA - ALTURA_SOLO),
        )

        # Desenha o pássaro sobre o cenário lógico.
        passaro.desenhar(cenario)

        # 5.4. Escalonamento apenas da imagem final.
        imagem_final = pygame.transform.scale(
            cenario, (largura_janela, altura_janela)
        )
        tela.blit(imagem_final, (0, 0))
        pygame.display.flip()

        # Mantém o limite de até 30 quadros por segundo.
        relogio.tick(FPS)

    # Encerra o Pygame depois que o loop termina.
    pygame.quit()


# ------------------------------------------------------------
# 6. PONTO DE ENTRADA DO PROGRAMA
# ------------------------------------------------------------

if __name__ == "__main__":
    main()
 