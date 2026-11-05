"""Garantias da curva de 25 níveis (config/difficulty_profiles.py)."""
import pytest

from flappy_arcade.config.difficulty_profiles import NIVEIS, PERFIS, Degraus
from flappy_arcade.gameplay.difficulty import (
    DificuldadeOriginal,
    desvio_maximo_passagem,
    parametros_donkey,
    parametros_galaga,
    parametros_nivel,
)
from flappy_arcade.gameplay.difficulty_curve import NIVEL_TETO_ORIGINAL, TABELA_ORIGINAL, CurvaDificuldade

MODOS = list(PERFIS)
curva = CurvaDificuldade()


def tabela(modo):
    return [getattr(curva, modo)(n) for n in range(1, NIVEIS + 1)]


@pytest.mark.parametrize('modo', MODOS)
def test_nivel_1_e_o_original(modo):
    assert getattr(curva, modo)(1) == TABELA_ORIGINAL[modo](1)


def test_provedor_original_bate_com_as_tabelas():
    original = DificuldadeOriginal()
    for n in range(1, 11):
        assert original.flappy(n) == parametros_nivel(n)
        assert original.galaga(n) == parametros_galaga(n - 1)
        assert original.donkey(n) == parametros_donkey(n - 1)


@pytest.mark.parametrize('modo', MODOS)
def test_perfil_cobre_todos_os_parametros(modo):
    """Nenhum parâmetro fica esquecido no valor do nível 1."""
    assert set(PERFIS[modo]) == set(TABELA_ORIGINAL[modo](1))


@pytest.mark.parametrize('modo', MODOS)
def test_degraus_comecam_no_valor_original(modo):
    base = TABELA_ORIGINAL[modo](1)
    for nome, spec in PERFIS[modo].items():
        if isinstance(spec, Degraus):
            assert min(spec.valores) == 1 and spec.valores[1] == base[nome], nome


@pytest.mark.parametrize('modo', ['galaga', 'donkey'])
def test_nivel_25_e_o_teto_original(modo):
    """Galaga e Donkey terminam no nível 10 do original (o teto já testado)."""
    teto = TABELA_ORIGINAL[modo](NIVEL_TETO_ORIGINAL)
    final = getattr(curva, modo)(NIVEIS)
    for nome, spec in PERFIS[modo].items():
        if getattr(spec, 'fim', None) is None:
            assert final[nome] == pytest.approx(teto[nome]), nome


@pytest.mark.parametrize('modo', MODOS)
def test_cada_parametro_anda_numa_direcao_so(modo):
    niveis = tabela(modo)
    for nome in niveis[0]:
        valores = [float(p[nome]) for p in niveis]
        sobe = all(b >= a for a, b in zip(valores, valores[1:]))
        desce = all(b <= a for a, b in zip(valores, valores[1:]))
        assert sobe or desce, f'{modo}.{nome} oscila: {valores}'


@pytest.mark.parametrize('modo', MODOS)
def test_todo_nivel_e_diferente_do_anterior(modo):
    niveis = tabela(modo)
    for n in range(1, NIVEIS):
        assert niveis[n] != niveis[n - 1], f'{modo}: nível {n + 1} igual ao {n}'


def test_niveis_fora_da_faixa_sao_limitados():
    assert curva.flappy(0) == curva.flappy(1)
    assert curva.flappy(99) == curva.flappy(NIVEIS)


def test_passagens_do_flappy_sao_sempre_justas(recursos):
    """Em todo nível, a próxima passagem é alcançável com folga.

    desvio_maximo_passagem é a mesma conta de justiça que o jogo usa para
    sortear os canos. Exigimos mais que o piso do jogo (80 px), descontando a
    oscilação dos pássaros, e uma abertura de pelo menos 3,5 alturas do pássaro.
    """
    from flappy_arcade.gameplay.flappy import Passaro
    sprite = recursos.passaros['dia'][0]
    for n in range(1, NIVEIS + 1):
        p = curva.flappy(n)
        passaro = Passaro(recursos)
        passaro.aplicar_dificuldade(p['gravidade'])
        desvio = desvio_maximo_passagem(
            p['abertura'], p['velocidade'], passaro.gravidade, passaro.impulso,
            recursos.cano_dia.get_width(), sprite.get_width(), sprite.get_height())
        assert desvio - 2 * p['oscilacao_passaros'] >= 100, f'nível {n}: folga {desvio}'
        assert p['abertura'] >= 3.5 * sprite.get_height(), f'nível {n}'
