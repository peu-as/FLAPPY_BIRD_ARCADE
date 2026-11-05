"""Barramento de eventos: módulos conversam sem se conhecerem.

Exemplo:
    bus.subscribe('settings_changed', audio.on_settings_changed)
    bus.emit('settings_changed', key='music', value=False)

Tópicos previstos: settings_changed, coin_collected, level_complete,
skin_equipped, progress_reset.
"""
from collections import defaultdict


class EventBus:
    def __init__(self):
        self._ouvintes = defaultdict(list)

    def subscribe(self, topico, funcao):
        """Registra a função; devolve outra função que cancela o registro."""
        self._ouvintes[topico].append(funcao)

        def cancelar():
            if funcao in self._ouvintes[topico]:
                self._ouvintes[topico].remove(funcao)
        return cancelar

    def emit(self, topico, **dados):
        # cópia: um ouvinte pode se descadastrar durante o próprio aviso
        for funcao in list(self._ouvintes[topico]):
            funcao(**dados)
