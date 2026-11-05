"""Loja de skins: comprar com moedas e equipar (seção "skins" do save)."""
from ..config.skins import POR_ID, SKIN_PADRAO

OK, JA_POSSUI, SEM_MOEDAS, DESCONHECIDA = 'ok', 'ja_possui', 'sem_moedas', 'desconhecida'


class Loja:
    def __init__(self, save, carteira, bus=None):
        self._save = save
        self.carteira = carteira
        self._bus = bus

    @property
    def _dados(self):
        dados = self._save.section('skins')
        compradas = [s for s in dados.get('owned', []) if s in POR_ID]
        if SKIN_PADRAO not in compradas:
            compradas.insert(0, SKIN_PADRAO)
        dados['owned'] = compradas
        return dados

    def possui(self, skin_id):
        return skin_id in self._dados['owned']

    @property
    def equipada(self):
        escolhida = self._dados.get('equipped')
        return escolhida if self.possui(escolhida) else SKIN_PADRAO

    def comprar(self, skin_id):
        if skin_id not in POR_ID:
            return DESCONHECIDA
        if self.possui(skin_id):
            return JA_POSSUI
        if not self.carteira.gastar(POR_ID[skin_id].preco):
            return SEM_MOEDAS
        self._dados['owned'].append(skin_id)
        self._save.save()
        return OK

    def equipar(self, skin_id):
        if not self.possui(skin_id):
            return False
        self._dados['equipped'] = skin_id
        self._save.save()
        if self._bus:
            self._bus.emit('skin_equipped', skin=skin_id)
        return True
