"""Grava o comportamento do jogo ORIGINAL (golden master) neste computador.

Uso, na raiz do projeto, com o ambiente virtual ativo:

    python tests/golden/record_legacy.py

O original é lido direto do git (tag baseline-fusao). Também aceita o caminho
de um main.py antigo:  python tests/golden/record_legacy.py caminho/main.py

Por que gravar em cada computador: seno/cosseno e o desenho das fontes variam
minimamente entre sistemas operacionais. Comparar o original e a versão nova
na MESMA máquina isola o que importa: a mudança de código.

O jogo original lê o relógio do sistema; aqui ele é trocado por um relógio
falso, para que cada execução seja idêntica.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).parent))

import pygame  # noqa: E402

from scenarios import CENARIOS, rodar  # noqa: E402
from snapshot import assinatura_plataforma  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = Path(__file__).parent / 'legacy_traces.json'
TAG = 'baseline-fusao'


def preparar_original(caminho_arg, pasta):
    """Monta pasta/src/main.py + pasta/assets (o original procura os assets em ../assets)."""
    (pasta / 'src').mkdir(parents=True)
    destino = pasta / 'src' / 'main.py'
    if caminho_arg:
        shutil.copyfile(caminho_arg, destino)
    else:
        try:
            conteudo = subprocess.run(['git', 'show', f'{TAG}:src/main.py'], cwd=RAIZ,
                                      capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as erro:
            sys.exit(f'Não consegui ler o original da tag {TAG} no git: {erro}')
        destino.write_bytes(conteudo)
    shutil.copytree(RAIZ / 'assets', pasta / 'assets')
    return destino


def carregar_legado(caminho):
    spec = importlib.util.spec_from_file_location('legacy_main', caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def jingle_do_loop(jogo):
    """Cópia exata do trecho de Jogo.executar() que roda após atualizar()."""
    if jogo.estado == 'GAMEOVER' and jogo.contador_arcade < 3:
        agora = time.monotonic()
        if agora - jogo.fim_iniciado >= 3.5 and (jogo.ultimo_arcade == 0 or
                                                 agora - jogo.ultimo_arcade >= 2):
            jogo.tocar('arcade')
            jogo.ultimo_arcade = agora
            jogo.contador_arcade += 1


def main(caminho_arg=None):
    pasta = Path(tempfile.mkdtemp(prefix='flappy-original-'))
    try:
        m = carregar_legado(preparar_original(caminho_arg, pasta))
        resultados = {}
        for nome in CENARIOS:
            dados = Path(tempfile.mkdtemp())
            m.ARQUIVO_RANKING = dados / 'ranking.json'
            m.ARQUIVO_RECORDE = dados / 'recorde.json'

            def criar(clock):
                time.monotonic = clock.now
                time.strftime = lambda formato, *args: '2026-01-01 00:00'  # data do ranking
                pygame.time.get_ticks = clock.ticks
                return m.Jogo()

            resultados[nome] = r = rodar(nome, criar, jingle_do_loop)
            print(f'{nome:14s} quadros={r["frames"]:5d} estado={r["estado_final_nome"]:9s}')
        resultados['_plataforma'] = assinatura_plataforma()
        SAIDA.write_text(json.dumps(resultados, indent=1), encoding='utf-8')
        print('Referência gravada em', SAIDA)
        print('Plataforma:', resultados['_plataforma'])
    finally:
        pygame.quit()
        shutil.rmtree(pasta, ignore_errors=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
