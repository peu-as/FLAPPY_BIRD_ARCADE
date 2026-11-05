"""Grava o comportamento do jogo ORIGINAL (golden master).

Uso (raramente necessário; o resultado já está em legacy_traces.json):

    git show baseline-fusao:src/main.py > legacy_main.py
    python tests/golden/record_legacy.py legacy_main.py

O jogo original lê o relógio direto do sistema; aqui ele é substituído por
um relógio falso para que cada execução seja idêntica.
"""
import importlib.util
import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).parent))

import pygame  # noqa: E402

from scenarios import CENARIOS, rodar  # noqa: E402

SAIDA = Path(__file__).parent / 'legacy_traces.json'


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


def main(caminho):
    m = carregar_legado(caminho)
    resultados = {}
    for nome in CENARIOS:
        pasta = Path(tempfile.mkdtemp())
        m.ARQUIVO_RANKING = pasta / 'ranking.json'
        m.ARQUIVO_RECORDE = pasta / 'recorde.json'

        def criar(clock):
            time.monotonic = clock.now
            time.strftime = lambda formato, *args: '2026-01-01 00:00'  # data do ranking
            pygame.time.get_ticks = clock.ticks
            return m.Jogo()

        resultados[nome] = rodar(nome, criar, jingle_do_loop)
        r = resultados[nome]
        print(f'{nome:14s} quadros={r["frames"]:5d} estado={r["estado_final_nome"]:9s} hash={r["final"]}')
    SAIDA.write_text(json.dumps(resultados, indent=1), encoding='utf-8')
    print('gravado em', SAIDA)


if __name__ == '__main__':
    main(sys.argv[1])
