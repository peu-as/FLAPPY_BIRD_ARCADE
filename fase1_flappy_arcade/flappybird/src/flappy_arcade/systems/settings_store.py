"""Configurações do jogador (música, efeitos sonoros, efeitos visuais).

Fica dentro do save (seção "settings"). Toda mudança é gravada na hora e
avisada pelo EventBus com o tópico 'settings_changed', para que áudio e
efeitos reajam sem precisar conhecer a tela de configurações.
"""

MUSICA = 'music'
SFX = 'sfx'
EFEITOS_VISUAIS = 'visual_fx'
CHAVES = (MUSICA, SFX, EFEITOS_VISUAIS)


class SettingsStore:
    def __init__(self, save, bus):
        self._save = save
        self._bus = bus

    @property
    def _dados(self):
        return self._save.section('settings')

    def get(self, chave):
        return bool(self._dados[chave])

    def set(self, chave, valor):
        self.set_many({chave: valor})

    def set_many(self, valores):
        """Altera várias chaves com uma única gravação em disco."""
        mudou = {}
        for chave, valor in valores.items():
            if chave not in CHAVES:
                raise KeyError(f'configuração desconhecida: {chave}')
            if self._dados[chave] != bool(valor):
                self._dados[chave] = bool(valor)
                mudou[chave] = bool(valor)
        if mudou:
            self._save.save()
            for chave, valor in mudou.items():
                self._bus.emit('settings_changed', key=chave, value=valor)

    def toggle(self, chave):
        self.set(chave, not self.get(chave))

    @property
    def music_enabled(self):
        return self.get(MUSICA)

    @property
    def sfx_enabled(self):
        return self.get(SFX)

    @property
    def visual_fx_enabled(self):
        return self.get(EFEITOS_VISUAIS)
