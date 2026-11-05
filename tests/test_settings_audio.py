import pytest

from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore


class SomFalso:
    def __init__(self):
        self.tocou, self.volume = 0, None

    def set_volume(self, v):
        self.volume = v

    def play(self):
        self.tocou += 1


@pytest.fixture
def montagem(tmp_path, pygame_pronto):
    bus = EventBus()
    save = SaveManager(tmp_path / 'save.json')
    save.load()
    settings = SettingsStore(save, bus)
    som = SomFalso()
    audio = AudioManager(settings, {'pulo': som}, bus)
    audio.disponivel = True
    return save, settings, audio, som, bus


def test_mudanca_e_gravada_e_avisada(montagem, tmp_path):
    save, settings, _, _, bus = montagem
    avisos = []
    bus.subscribe('settings_changed', lambda key, value: avisos.append((key, value)))
    settings.toggle('visual_fx')
    assert avisos == [('visual_fx', False)]
    assert SaveManager(tmp_path / 'save.json').load()['settings']['visual_fx'] is False


def test_valor_igual_nao_grava_nem_avisa(montagem):
    _, settings, _, _, bus = montagem
    avisos = []
    bus.subscribe('settings_changed', lambda **d: avisos.append(d))
    settings.set('music', True)
    assert avisos == []


def test_chave_desconhecida_e_erro(montagem):
    with pytest.raises(KeyError):
        montagem[1].set('volume_secreto', True)


def test_sfx_respeita_configuracao(montagem):
    _, settings, audio, som, _ = montagem
    audio.play_sfx('pulo', 0.3)
    assert (som.tocou, som.volume) == (1, 0.3)
    settings.set('sfx', False)
    audio.play_sfx('pulo')
    assert som.tocou == 1
    audio.play_sfx('nao_existe')            # som ausente não quebra


def test_tecla_s_silencia_e_religa_tudo(montagem):
    _, settings, audio, _, _ = montagem
    audio.toggle_mute()
    assert not settings.music_enabled and not settings.sfx_enabled
    audio.toggle_mute()
    assert settings.music_enabled and settings.sfx_enabled
    settings.set('music', False)            # só a música desligada: S silencia o resto
    audio.toggle_mute()
    assert not settings.music_enabled and not settings.sfx_enabled


def test_sem_placa_de_som_nada_quebra(montagem):
    _, _, audio, som, _ = montagem
    audio.disponivel = False
    audio.play_sfx('pulo')
    audio.play_music('qualquer.ogg')
    audio.stop_music()
    assert som.tocou == 0


def test_bus_cancelar_inscricao():
    bus = EventBus()
    recebidos = []
    cancelar = bus.subscribe('x', lambda **d: recebidos.append(d))
    bus.emit('x', a=1)
    cancelar()
    bus.emit('x', a=2)
    assert recebidos == [{'a': 1}]
