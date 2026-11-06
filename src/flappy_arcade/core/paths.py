"""Caminhos de recursos (somente leitura) e de dados do jogador (graváveis).

Em desenvolvimento, tudo fica na raiz do projeto (assets/ e data/).
Empacotado pelo PyInstaller, os recursos vêm da pasta temporária do executável
e os dados vão para a pasta de dados do usuário de cada sistema operacional.
A variável de ambiente FLAPPY_DATA_DIR força outra pasta de dados (testes).
"""
import os
import sys
from pathlib import Path

# Nome mantido igual ao das versões anteriores: preserva rankings já salvos.
NOME_APP = 'FlappyBird'


def _raiz_recursos():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    # este arquivo: <raiz>/src/flappy_arcade/core/paths.py
    return Path(__file__).resolve().parents[3]


def _pasta_dados_do_usuario():
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA')
        return (Path(base) if base else Path.home() / 'AppData' / 'Local') / NOME_APP
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / NOME_APP
    base = os.environ.get('XDG_DATA_HOME')
    return (Path(base) if base else Path.home() / '.local' / 'share') / NOME_APP


def _raiz_dados():
    forcada = os.environ.get('FLAPPY_DATA_DIR')
    if forcada:
        return Path(forcada)
    if getattr(sys, 'frozen', False):
        return _pasta_dados_do_usuario()
    return RAIZ_RECURSOS


RAIZ_RECURSOS = _raiz_recursos()
RAIZ_DADOS = _raiz_dados()

IMAGENS = RAIZ_RECURSOS / 'assets' / 'imgs'
AUDIOS = RAIZ_RECURSOS / 'assets' / 'audio'
ARTES_SKINS = RAIZ_RECURSOS / 'assets' / 'skins'          # tools/importar_artes.py
ARTES_CENARIOS = RAIZ_RECURSOS / 'assets' / 'cenarios'

PASTA_DADOS = RAIZ_DADOS / 'data'
ARQUIVO_RECORDE = PASTA_DADOS / 'recorde.json'   # formato antigo, só leitura
ARQUIVO_RANKING = PASTA_DADOS / 'ranking.json'
ARQUIVO_SAVE = PASTA_DADOS / 'save.json'         # moedas, skins, mapas, configurações

# Músicas de fundo (geradas por tools/gerar_musica.py)
MUSICA_MENU = AUDIOS / 'musica_menu.wav'
MUSICA_JOGO = AUDIOS / 'musica_jogo.wav'
