"""Cenários do jogador: comprar, escolher um fixo ou montar a playlist aleatória.

Seção "scenarios" do save. Os dados são conferidos a cada acesso: cenário que
não existe some, o básico nunca falta, o fixo precisa ser seu e a playlist
só tem cenários seus, sem repetição e com no máximo MAX_PLAYLIST.
"""
from ..config.scenarios import CENARIO_PADRAO, MAX_PLAYLIST, MODO_ALEATORIO, MODO_FIXO, MODOS, POR_ID
from .shop import DESCONHECIDA, JA_POSSUI, OK, SEM_MOEDAS

NAO_POSSUI, PLAYLIST_CHEIA, ULTIMO_DA_PLAYLIST = 'nao_possui', 'playlist_cheia', 'ultimo_da_playlist'


class ColecaoCenarios:
    def __init__(self, save, carteira, bus=None):
        self._save = save
        self.carteira = carteira
        self._bus = bus

    @property
    def _dados(self):
        dados = self._save.section('scenarios')
        comprados = list(dict.fromkeys(c for c in dados.get('owned', []) if c in POR_ID))
        if CENARIO_PADRAO not in comprados:
            comprados.insert(0, CENARIO_PADRAO)
        dados['owned'] = comprados
        if dados.get('mode') not in MODOS:
            dados['mode'] = MODO_FIXO
        if dados.get('fixed') not in comprados:
            dados['fixed'] = CENARIO_PADRAO
        lista = list(dict.fromkeys(c for c in dados.get('playlist', []) if c in comprados))
        dados['playlist'] = lista[:MAX_PLAYLIST] or [dados['fixed']]
        return dados

    # ------------------------------------------------------------ consulta
    def possui(self, cenario_id):
        return cenario_id in self._dados['owned']

    @property
    def comprados(self):
        return list(self._dados['owned'])

    @property
    def modo(self):
        return self._dados['mode']

    @property
    def fixo(self):
        return self._dados['fixed']

    @property
    def playlist(self):
        return list(self._dados['playlist'])

    def na_playlist(self, cenario_id):
        return cenario_id in self._dados['playlist']

    def ativos(self):
        """O que o diretor de cenários vai mostrar: o fixo, ou a playlist."""
        dados = self._dados
        return [dados['fixed']] if dados['mode'] == MODO_FIXO else list(dados['playlist'])

    # ------------------------------------------------------------ ações
    def comprar(self, cenario_id):
        if cenario_id not in POR_ID:
            return DESCONHECIDA
        if self.possui(cenario_id):
            return JA_POSSUI
        if not self.carteira.gastar(POR_ID[cenario_id].preco):
            return SEM_MOEDAS
        dados = self._dados
        dados['owned'].append(cenario_id)
        if len(dados['playlist']) < MAX_PLAYLIST:     # comprado já entra no sorteio
            dados['playlist'].append(cenario_id)
        self._salvar('scenario_bought', cenario=cenario_id)
        return OK

    def usar_fixo(self, cenario_id):
        """Escolhe um cenário fixo (e passa para o modo fixo)."""
        if not self.possui(cenario_id):
            return NAO_POSSUI
        dados = self._dados
        dados['fixed'], dados['mode'] = cenario_id, MODO_FIXO
        self._salvar('scenarios_changed')
        return OK

    def definir_modo(self, modo):
        if modo not in MODOS:
            return DESCONHECIDA
        self._dados['mode'] = modo
        self._salvar('scenarios_changed')
        return OK

    def alternar_na_playlist(self, cenario_id):
        """Põe ou tira da playlist. Nunca deixa a playlist vazia nem passar de 15."""
        if not self.possui(cenario_id):
            return NAO_POSSUI
        lista = self._dados['playlist']
        if cenario_id in lista:
            if len(lista) == 1:
                return ULTIMO_DA_PLAYLIST
            lista.remove(cenario_id)
        else:
            if len(lista) >= MAX_PLAYLIST:
                return PLAYLIST_CHEIA
            lista.append(cenario_id)
        self._salvar('scenarios_changed')
        return OK

    def _salvar(self, evento, **dados):
        self._save.save()
        if self._bus:
            self._bus.emit(evento, **dados)


__all__ = ['ColecaoCenarios', 'MODO_ALEATORIO', 'MODO_FIXO', 'NAO_POSSUI', 'PLAYLIST_CHEIA',
           'ULTIMO_DA_PLAYLIST']
