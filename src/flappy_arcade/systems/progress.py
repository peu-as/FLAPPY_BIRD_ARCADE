"""Progresso nos mapas: estrelas por casa, com casas liberadas em sequência.

Formato no save (seção "progress"):
    {"flappy": {"estrelas": [3, 2, 0, 0, ...]}}      # 25 números de 0 a 3

As casas liberadas não são gravadas: saem das estrelas (a casa N + 1 abre
quando a N tem estrela), então nunca ficam inconsistentes. No Modo Apresentação
(systems/apresentacao.py) todas abrem.
"""
from ..config.levels import CASAS, VIDAS_POR_CASA
from . import apresentacao


class ProgressStore:
    def __init__(self, save, bus=None):
        self._save = save
        self._bus = bus

    def _lista(self, mapa):
        """Lista de estrelas do mapa, criada ou consertada se preciso."""
        secao = self._save.section('progress')
        dados = secao.get(mapa)
        if not isinstance(dados, dict):
            dados = secao[mapa] = {}
        lista = dados.get('estrelas')
        if not isinstance(lista, list):
            lista = []
        lista = [min(VIDAS_POR_CASA, max(0, v)) if isinstance(v, int) and not isinstance(v, bool) else 0
                 for v in lista[:CASAS]]
        lista += [0] * (CASAS - len(lista))
        dados['estrelas'] = lista
        return lista

    def estrelas(self, mapa, casa):
        return self._lista(mapa)[casa - 1]

    def liberada(self, mapa, casa):
        return 1 <= casa <= CASAS and (casa == 1 or apresentacao.ligado() or self.estrelas(mapa, casa - 1) > 0)

    def concluida(self, mapa, casa):
        return self.estrelas(mapa, casa) > 0

    def total(self, mapa):
        return sum(self._lista(mapa))

    def maximo(self):
        return CASAS * VIDAS_POR_CASA

    def casa_atual(self, mapa):
        """Primeira casa liberada ainda sem estrela (ou a última, se tudo feito)."""
        for casa in range(1, CASAS + 1):
            if not self.concluida(mapa, casa):
                return casa
        return CASAS

    def registrar(self, mapa, casa, estrelas):
        """Guarda o resultado de uma vitória. Devolve (melhorou, casa_liberada)."""
        lista = self._lista(mapa)
        antes = lista[casa - 1]
        liberou = casa + 1 if antes == 0 and casa < CASAS else None
        melhorou = estrelas > antes
        if melhorou:
            lista[casa - 1] = estrelas
            self._save.save()
            if self._bus:
                self._bus.emit('level_complete', mapa=mapa, casa=casa, estrelas=estrelas)
        return melhorou, liberou
