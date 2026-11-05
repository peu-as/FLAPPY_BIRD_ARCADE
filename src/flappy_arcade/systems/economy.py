"""Carteira de moedas do jogador (seção "wallet" do save).

As moedas coletadas numa partida são depositadas de uma vez quando a partida
termina ou quando o jogador sai dela; assim o save não é gravado a cada moeda.
"""


class Carteira:
    def __init__(self, save, bus=None):
        self._save = save
        self._bus = bus

    @property
    def saldo(self):
        return self._save.section('wallet')['coins']

    def _definir(self, valor):
        self._save.section('wallet')['coins'] = valor
        self._save.save()
        if self._bus:
            self._bus.emit('coins_changed', saldo=valor)

    def depositar(self, quantidade):
        if quantidade > 0:
            self._definir(self.saldo + int(quantidade))

    def pode_pagar(self, preco):
        return self.saldo >= preco

    def gastar(self, preco):
        """Debita se houver saldo. Devolve True se pagou."""
        if preco < 0 or not self.pode_pagar(preco):
            return False
        self._definir(self.saldo - preco)
        return True
