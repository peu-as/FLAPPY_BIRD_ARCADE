"""Regra de ouro: o jogo na nova arquitetura se comporta EXATAMENTE como o original.

Os mesmos cenários foram gravados no main.py original (tag git baseline-fusao)
em golden/legacy_traces.json: hash do estado completo a cada 50 quadros e dos
pixels da tela a cada 10. Qualquer mudança de física, regra ou desenho quebra
este teste e aponta o primeiro quadro diferente.
"""
import json
import time
from pathlib import Path

import pytest

from scenarios import CENARIOS, rodar

GRAVACAO = json.loads((Path(__file__).parent / 'golden' / 'legacy_traces.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('nome', list(CENARIOS))
def test_identico_ao_original(nome, recursos, tmp_path, monkeypatch):
    from flappy_arcade.core.event_bus import EventBus
    from flappy_arcade.gameplay.classic_session import ClassicSession
    from flappy_arcade.systems import ranking
    from flappy_arcade.systems.audio_manager import AudioManager
    from flappy_arcade.systems.save_manager import SaveManager
    from flappy_arcade.systems.settings_store import SettingsStore

    monkeypatch.setattr(ranking, 'ARQUIVO_RANKING', tmp_path / 'ranking.json')
    monkeypatch.setattr(ranking, 'ARQUIVO_RECORDE', tmp_path / 'recorde.json')
    monkeypatch.setattr(time, 'strftime', lambda formato, *a: '2026-01-01 00:00')

    def criar(clock):
        bus = EventBus()
        settings = SettingsStore(SaveManager(tmp_path / 'save.json'), bus)
        return ClassicSession(recursos, AudioManager(settings, recursos.sons, bus), clock)

    novo = rodar(nome, criar, lambda sessao: sessao.pos_atualizar())
    antigo = GRAVACAO[nome]

    for tipo in ('estados', 'pixels'):
        diferentes = sorted((int(q) for q in antigo[tipo] if novo[tipo].get(q) != antigo[tipo][q]))
        assert not diferentes, f'{nome}: {tipo} divergem a partir do quadro {diferentes[0]}'
    assert novo['frames'] == antigo['frames']
    assert novo['estado_final_nome'] == antigo['estado_final_nome']
    assert novo['final'] == antigo['final']
