"""Fase 18: efeitos sonoros dos modos novos (tools/gerar_sons.py)."""
import array
import importlib.util
import random
import wave
from pathlib import Path

import pygame

from flappy_arcade.config import combina3 as cfg
from flappy_arcade.core.paths import AUDIOS
from flappy_arcade.gameplay.resources import SONS_MODOS_NOVOS

FERRAMENTA = Path(__file__).resolve().parents[1] / 'tools' / 'gerar_sons.py'


def _gerador():
    spec = importlib.util.spec_from_file_location('gerar_sons', FERRAMENTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_arquivos_existem_curtos_e_nao_mudos():
    for nome in SONS_MODOS_NOVOS:
        with wave.open(str(AUDIOS / f'sfx_{nome}.wav')) as arquivo:
            assert arquivo.getnchannels() == 1 and arquivo.getframerate() == 22050
            quadros = arquivo.readframes(arquivo.getnframes())
            duracao = arquivo.getnframes() / arquivo.getframerate()
        amostras = array.array('h', quadros)
        assert 0.05 < duracao < 1.0, nome
        assert max(abs(v) for v in amostras) > 0.5 * 32767, nome         # tem som de verdade


def test_gerador_reproduz_os_mesmos_arquivos(tmp_path):
    gerador = _gerador()
    gerador.DESTINO = tmp_path
    gerador.sorteio = random.Random(18)
    gerador.main()
    assert set(gerador.SONS) == set(SONS_MODOS_NOVOS)
    for nome in SONS_MODOS_NOVOS:
        assert (tmp_path / f'sfx_{nome}.wav').read_bytes() == (AUDIOS / f'sfx_{nome}.wav').read_bytes(), nome


class AudioGravador:
    def __init__(self):
        self.tocados = []

    def play_sfx(self, nome, volume=0.5):
        self.tocados.append(nome)


def test_combina3_toca_so_sons_que_existem(recursos, monkeypatch):
    from flappy_arcade.gameplay.combina3.sessao import PRONTO, Combina3Session
    from flappy_arcade.gameplay.combina3.tabuleiro import LINHA_H, OVO
    casa = cfg.CasaCombina3(20, ((cfg.CHEFE,),), chefao=cfg.chefe('dupla', 9999, 1, casulos=1, barris=1),
                            mapa=('.......', '..g.g..', '.......', 'c.....c', '.......', '.......', '.......', '.......'))
    monkeypatch.setattr(cfg, 'casa_combina3', lambda n: casa)
    audio = AudioGravador()
    s = Combina3Session(recursos, audio, None, 1, semente=5)
    s.tab.grade[2][1].especial = LINHA_H
    s.tab.grade[2][3].especial = OVO
    for _ in range(600):
        if s.resultado or s.usadas >= 8:
            break
        if s.etapa == PRONTO:
            s.acao_principal()
        s.atualizar()
    tocados = set(audio.tocados)
    assert tocados <= set(recursos.sons), tocados - set(recursos.sons)
    assert {'estouro1', 'ataque_chefe', 'chefe_ferido'} <= tocados


def test_estilingue_toca_so_sons_que_existem(recursos):
    from flappy_arcade.gameplay.estilingue.sessao import EstilingueSession
    audio = AudioGravador()
    s = EstilingueSession(recursos, audio, None, 6)
    for i in range(900):
        if s.resultado:
            break
        if i % 20 == 0:
            s.acao_principal()
        s.atualizar()
    tocados = set(audio.tocados)
    assert tocados <= set(recursos.sons), tocados - set(recursos.sons)
    assert 'lancar' in tocados


def test_sons_carregam_no_pygame(recursos):
    if not pygame.mixer.get_init():
        return
    assert all(recursos.sons[nome] is not None for nome in SONS_MODOS_NOVOS)
