"""Carregamento centralizado de imagens, sons e sprites derivados."""
import pygame

from ..config.constants import PASSAROS_ESPECIAIS, TAMANHO_INIMIGO, TAMANHO_NAVE, TEMAS
from ..core.paths import ARTES_SKINS, AUDIOS, IMAGENS
from .procedural import (
    criar_banana,
    criar_barril_rolante,
    criar_bola_fogo,
    criar_camada_palmeiras,
    criar_chefe_galaga,
    criar_cipo,
    criar_fundo_selva,
    criar_kong,
    criar_pilha_barris,
    criar_rebite,
    criar_viga,
    tingir,
)


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
    """Redimensiona mantendo a proporção: o maior lado passa a
    medir 'lado' pixels. Garante inimigos de tamanho parecido mesmo que
    os PNGs originais tenham dimensões diferentes.
    """
    escala = lado / max(sprite.get_width(), sprite.get_height())
    return pygame.transform.smoothscale(
        sprite, (max(1, int(sprite.get_width()*escala)),
                 max(1, int(sprite.get_height()*escala))))

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
        # Sprites da fase Galaga, derivados dos que já foram carregados.
        # Inimigos: os pássaros especiais reduzidos a um tamanho padrão.
        self.inimigos = {nome: ajustar_sprite(sprite, TAMANHO_INIMIGO)
                         for nome, sprite in self.especiais.items()}
        # Nave: o próprio pássaro girado 90° (anti-horário) para "apontar" para
        # cima. Se o seu sprite não olhar para a direita, ajuste o ângulo.
        self.nave = pygame.transform.rotate(
            ajustar_sprite(self.passaros['dia'][1], TAMANHO_NAVE), 90)
        # Sprites da fase Donkey Kong (gerados por código; ver seção 2B).
        # convert_alpha() acelera o blit; exige que a janela já exista.
        self.selva_cipo = criar_cipo().convert_alpha()
        self.selva_barris = criar_pilha_barris().convert_alpha()
        self.barril = criar_barril_rolante().convert_alpha()
        self.banana = criar_banana().convert_alpha()
        # Três poses: parado, 'lanca' (barril erguido: preparo do
        # arremesso) e 'arremessou' (braços erguidos, mãos vazias: barril solto).
        self.kong = {'parado': criar_kong(False).convert_alpha(),
                     'lanca': criar_kong(True).convert_alpha(),
                     'arremessou': criar_kong(True, False).convert_alpha()}
        # Chefões: Kong maior (e uma versão avermelhada, "furioso"), Boss
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
        self._artes_skins = {}
        self._cenarios = None

    @property
    def cenarios(self):
        """Fundos dos cenários comprados (montados sob demanda, no máximo 3 na memória)."""
        if self._cenarios is None:
            from .scenery import GerenciadorCenarios
            self._cenarios = GerenciadorCenarios(self)
        return self._cenarios

    def arte_skin(self, nome):
        """Arte importada de assets/skins (carregada só quando alguém usa)."""
        if nome not in self._artes_skins:
            self._artes_skins[nome] = pygame.image.load(str(ARTES_SKINS / f'{nome}.png')).convert_alpha()
        return self._artes_skins[nome]
