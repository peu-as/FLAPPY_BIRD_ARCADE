"""Curva de dificuldade de 25 níveis, calculada a partir dos perfis de dados.

Uso:
    curva = CurvaDificuldade()
    curva.flappy(7)   ->  {'gravidade': ..., 'abertura': ..., ...}
    curva.galaga(7), curva.donkey(7)

Mesma interface do provedor original (DificuldadeOriginal), então a sessão
não precisa saber qual dos dois está usando. Os valores são calculados uma
vez só e guardados em cache.
"""
from ..config.difficulty_profiles import NIVEIS, PERFIS, Degraus
from .difficulty import parametros_donkey, parametros_galaga, parametros_nivel

# Tabela original de cada modo, pelo nível do jogo (1 a 10).
TABELA_ORIGINAL = {
    'flappy': parametros_nivel,
    'galaga': lambda nivel: parametros_galaga(nivel - 1),
    'donkey': lambda nivel: parametros_donkey(nivel - 1),
}
NIVEL_TETO_ORIGINAL = 10


def valor_no_nivel(spec, nivel, inicial, teto_original):
    """Valor de um parâmetro num nível (1 a NIVEIS), segundo a especificação."""
    if isinstance(spec, Degraus):
        marcos = [n for n in sorted(spec.valores) if n <= nivel]
        return spec.valores[marcos[-1]]
    if nivel <= spec.desde and (nivel < spec.desde or spec.inicio is None):
        return inicial
    comeco = inicial if spec.inicio is None else spec.inicio
    fim = teto_original if spec.fim is None else spec.fim
    t = (nivel - spec.desde) / (NIVEIS - spec.desde)
    valor = comeco + (fim - comeco) * t ** spec.curva
    return round(valor) if spec.inteiro else valor


class CurvaDificuldade:
    """Provedor de dificuldade de 25 níveis (Modo Livre e, na Fase 3, os mapas)."""

    nivel_maximo = NIVEIS

    def __init__(self, perfis=PERFIS):
        self._perfis = perfis
        self._cache = {}

    def _calcular(self, modo, nivel):
        nivel = max(1, min(NIVEIS, int(nivel)))
        chave = (modo, nivel)
        if chave not in self._cache:
            base = TABELA_ORIGINAL[modo](1)
            teto = TABELA_ORIGINAL[modo](NIVEL_TETO_ORIGINAL)
            params = dict(base)
            for nome, spec in self._perfis[modo].items():
                params[nome] = valor_no_nivel(spec, nivel, base[nome], teto[nome])
            self._cache[chave] = params
        return dict(self._cache[chave])

    def flappy(self, nivel):
        return self._calcular('flappy', nivel)

    def galaga(self, nivel):
        return self._calcular('galaga', nivel)

    def donkey(self, nivel):
        return self._calcular('donkey', nivel)
