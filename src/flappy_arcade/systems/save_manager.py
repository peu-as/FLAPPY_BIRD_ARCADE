"""Save do jogador: um único JSON versionado, à prova de falhas.

Formato (versão 2):
    {
      "version": 2,
      "settings":  {"music": true, "sfx": true, "visual_fx": true},
      "wallet":    {"coins": 0},
      "skins":     {"owned": ["classico"], "equipped": "classico"},
      "scenarios": {"owned": ["bg"], "mode": "fixo", "fixed": "bg", "playlist": ["bg"]},
      "progress":  {},          # por mapa: casas liberadas e estrelas
      "records":   {"free_best_streak": 0},  # Modo Livre: maior sequência sem cair
      "tutorial":  {"vistas": []}            # dicas dos modos novos já vistas (Fase 18)
    }

Versão 2 (Fase 9): cenários compráveis. Quem vem da versão 1 mantém tudo
(moedas, skins, estrelas) e começa só com o cenário básico.

Garantias:
  * escrita atômica: grava num .tmp e troca de uma vez (os.replace), então
    uma queda de energia nunca deixa o save pela metade;
  * cópia de segurança (.bak) do último save bom;
  * arquivo corrompido é isolado (save.corrupt-<data>.json), nunca apagado;
  * campos ausentes ou com tipo errado voltam ao padrão, sem perder o resto;
  * versões antigas são migradas por funções registradas em MIGRACOES;
  * se a pasta não for gravável, o jogo continua com o progresso em memória.
"""
import copy
import json
import os
import shutil
import time
from pathlib import Path

VERSAO_ATUAL = 2

PADRAO = {
    'version': VERSAO_ATUAL,
    'settings': {'music': True, 'sfx': True, 'visual_fx': True},
    'wallet': {'coins': 0},
    'skins': {'owned': ['classico'], 'equipped': 'classico'},
    'scenarios': {'owned': ['bg'], 'mode': 'fixo', 'fixed': 'bg', 'playlist': ['bg']},
    'progress': {},
    'records': {'free_best_streak': 0},
    'tutorial': {'vistas': []},                # dicas dos modos novos já vistas
}

# MIGRACOES[n] recebe um save da versão n e devolve um da versão n + 1.
# Ao mudar o formato: aumente VERSAO_ATUAL e registre a função aqui.
MIGRACOES = {
    0: lambda dados: {**dados, 'version': 1},
    1: lambda dados: {**dados, 'scenarios': copy.deepcopy(PADRAO['scenarios'])},
}


def _completar(dados, padrao):
    """Preenche chaves ausentes e corrige tipos, preservando chaves extras."""
    resultado = dict(dados)
    for chave, valor_padrao in padrao.items():
        atual = resultado.get(chave)
        if isinstance(valor_padrao, dict):
            resultado[chave] = (_completar(atual, valor_padrao)
                                if isinstance(atual, dict) else copy.deepcopy(valor_padrao))
        elif type(atual) is not type(valor_padrao):
            resultado[chave] = copy.deepcopy(valor_padrao)
    return resultado


class SaveManager:
    def __init__(self, caminho, migracoes=None):
        self.caminho = Path(caminho)
        self.backup = self.caminho.with_name(self.caminho.name + '.bak')
        self.migracoes = MIGRACOES if migracoes is None else migracoes
        self.data = copy.deepcopy(PADRAO)
        self.gravavel = True

    # ------------------------------------------------------------ leitura
    def load(self):
        """Carrega o save (ou o backup, ou o padrão) e devolve os dados."""
        for arquivo in (self.caminho, self.backup):
            dados = self._ler(arquivo)
            if dados is not None:
                self.data = dados
                return self.data
        self.data = copy.deepcopy(PADRAO)
        return self.data

    def _ler(self, arquivo):
        if not arquivo.exists():
            return None
        try:
            bruto = json.loads(arquivo.read_text(encoding='utf-8'))
            if not isinstance(bruto, dict):
                raise ValueError('save não é um objeto JSON')
            return self._migrar(bruto)
        except (OSError, ValueError, KeyError, TypeError) as erro:
            print(f'Aviso: save ilegível ({arquivo.name}): {erro}')
            self._isolar(arquivo)
            return None

    def _migrar(self, dados):
        versao = dados.get('version', 0)
        if not isinstance(versao, int) or versao < 0:
            raise ValueError(f'versão inválida: {versao!r}')
        while versao < VERSAO_ATUAL:
            dados = self.migracoes[versao](dados)
            versao += 1
            dados['version'] = versao
        # um save de versão MAIS NOVA é mantido como está (só completado)
        return _completar(dados, {**PADRAO, 'version': dados['version']})

    def _isolar(self, arquivo):
        base = f'{self.caminho.stem}.corrupt-{time.strftime("%Y%m%d-%H%M%S")}'
        destino, n = arquivo.with_name(f'{base}.json'), 2
        while destino.exists():                              # dois no mesmo segundo: não sobrescreve
            destino, n = arquivo.with_name(f'{base}-{n}.json'), n + 1
        try:
            os.replace(arquivo, destino)
        except OSError:
            pass

    # ------------------------------------------------------------ escrita
    def save(self):
        """Grava atomicamente. Devolve False (sem travar o jogo) se falhar."""
        if not self.gravavel:
            return False
        tmp = self.caminho.with_name(self.caminho.name + '.tmp')
        try:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp, 'w', encoding='utf-8') as arquivo:
                json.dump(self.data, arquivo, ensure_ascii=False, indent=2)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            if self.caminho.exists():
                shutil.copy2(self.caminho, self.backup)
            os.replace(tmp, self.caminho)
            return True
        except OSError as erro:
            print(f'Aviso: não foi possível salvar o progresso: {erro}')
            self.gravavel = False
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    def section(self, nome):
        """Acesso direto a uma seção ('settings', 'wallet', 'skins', 'progress')."""
        return self.data[nome]

    def reset_progress(self):
        """Zera moedas, skins, cenários e mapas; mantém as configurações."""
        configuracoes = self.data['settings']
        self.data = copy.deepcopy(PADRAO)
        self.data['settings'] = configuracoes
        return self.save()
