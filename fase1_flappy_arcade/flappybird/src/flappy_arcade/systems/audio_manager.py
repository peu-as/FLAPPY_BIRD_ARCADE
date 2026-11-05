"""Áudio do jogo: efeitos sonoros e música em canais separados.

* Efeitos (SFX): objetos pygame.mixer.Sound, tocados por nome.
* Música: pygame.mixer.music (streaming, em laço), uma faixa por vez.

Respeita as configurações em tempo real: desligar a música para a faixa,
religar retoma a mesma faixa; desligar os SFX corta os que estão tocando.
Sem placa de som (mixer indisponível), tudo vira operação vazia.
"""
import pygame

from .settings_store import MUSICA, SFX


class AudioManager:
    def __init__(self, settings, sons, bus):
        self.settings = settings
        self.sons = sons
        self.disponivel = pygame.mixer.get_init() is not None
        self._faixa = None          # (caminho, volume) da música pedida
        bus.subscribe('settings_changed', self._ao_mudar_configuracao)

    @property
    def sfx_enabled(self):
        return self.settings.sfx_enabled

    @property
    def music_enabled(self):
        return self.settings.music_enabled

    # ------------------------------------------------------------ efeitos
    def play_sfx(self, nome, volume=0.5):
        if not (self.disponivel and self.sfx_enabled):
            return
        efeito = self.sons.get(nome)
        if efeito is not None:
            efeito.set_volume(volume)
            efeito.play()

    # ------------------------------------------------------------ música
    def play_music(self, caminho, volume=0.6, fade_ms=600):
        """Toca uma faixa em laço (lembrada mesmo com a música desligada)."""
        if self._faixa and self._faixa[0] == caminho:
            return
        self._faixa = (caminho, volume)
        self._iniciar_faixa(fade_ms)

    def stop_music(self, fade_ms=400):
        self._faixa = None
        self._parar_faixa(fade_ms)

    def _iniciar_faixa(self, fade_ms):
        if not (self.disponivel and self._faixa and self.music_enabled):
            return
        caminho, volume = self._faixa
        try:
            pygame.mixer.music.load(str(caminho))
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1, fade_ms=fade_ms)
        except pygame.error as erro:
            print(f'Aviso: música {caminho} indisponível: {erro}')

    def _parar_faixa(self, fade_ms):
        if self.disponivel:
            pygame.mixer.music.fadeout(fade_ms)

    # ------------------------------------------------------------ configurações
    def toggle_mute(self):
        """Tecla S: com algum som ligado, silencia tudo; senão, liga tudo."""
        ligar = not (self.music_enabled or self.sfx_enabled)
        self.settings.set_many({MUSICA: ligar, SFX: ligar})

    def _ao_mudar_configuracao(self, key, value):
        if key == MUSICA:
            if value:
                self._iniciar_faixa(fade_ms=400)
            else:
                self._parar_faixa(fade_ms=250)
        elif key == SFX and not value and self.disponivel:
            pygame.mixer.stop()     # corta só os SFX; a música é outro canal
