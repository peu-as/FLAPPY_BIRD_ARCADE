"""Fotografia determinística do estado de uma sessão de jogo.

Percorre recursivamente os atributos da sessão (pássaro, canos, fases,
inimigos, barris...) e produz uma estrutura só com valores simples. O hash
dessa estrutura, quadro a quadro, prova que duas versões do código se
comportam de forma idêntica.

Atributos de infraestrutura (janela, fontes, áudio, relógio) são ignorados:
eles mudaram de lugar na nova arquitetura, mas não fazem parte da física.
"""
import hashlib
import types

import pygame

IGNORADOS = {
    # infraestrutura que mudou de lugar na nova arquitetura
    'recursos', 'janela', 'tela', 'relogio', 'tamanho', 'clock', 'audio',
    'som_ativo', 'bus', 'settings',
    'fonte', 'fonte_grande', 'fonte_banner', 'fonte_contagem',
    'fonte_tabela', 'fonte_titulo_tabela',
}
TIPOS_OPACOS = (pygame.Surface, pygame.mask.Mask, pygame.font.Font,
                types.FunctionType, types.MethodType, types.ModuleType,
                types.BuiltinFunctionType)


def _som_ou_none(obj):
    try:
        return isinstance(obj, pygame.mixer.Sound)
    except Exception:
        return False


def fotografar(obj, _pilha=None):
    """Converte obj em tuplas/listas/escalares comparáveis."""
    if _pilha is None:
        _pilha = set()
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, pygame.Rect):
        return ('Rect', obj.x, obj.y, obj.w, obj.h)
    if isinstance(obj, TIPOS_OPACOS) or _som_ou_none(obj):
        return '<opaco>'
    ident = id(obj)
    if ident in _pilha:
        return '<ciclo>'
    _pilha.add(ident)
    try:
        if isinstance(obj, (list, tuple)):
            return [fotografar(x, _pilha) for x in obj]
        if isinstance(obj, (set, frozenset)):
            return sorted(repr(fotografar(x, _pilha)) for x in obj)
        if isinstance(obj, dict):
            return [(repr(k), fotografar(v, _pilha))
                    for k, v in sorted(obj.items(), key=lambda kv: repr(kv[0]))
                    if k not in IGNORADOS]
        if hasattr(obj, '__dict__'):
            campos = sorted((k, v) for k, v in vars(obj).items()
                            if k not in IGNORADOS and not k.startswith('__'))
            return (type(obj).__name__, [(k, fotografar(v, _pilha)) for k, v in campos])
        return repr(obj)
    finally:
        _pilha.discard(ident)


def assinatura_plataforma():
    """O que precisa ser igual para os hashes serem comparáveis.

    Seno/cosseno vêm da biblioteca matemática do sistema operacional e o texto
    é desenhado pela biblioteca de fontes do pygame: ambos variam (pouquíssimo)
    entre Windows, macOS e Linux. Por isso a gravação vale para uma plataforma.
    """
    import sys
    return {'sistema': sys.platform, 'pygame': pygame.version.ver,
            'sdl': '.'.join(map(str, pygame.version.SDL)),
            'sdl_ttf': '.'.join(map(str, pygame.font.get_sdl_ttf_version()))}


def hash_estado(sessao):
    # [1]: só os campos; o nome da classe da sessão mudou (Jogo -> ClassicSession)
    return hashlib.md5(repr(fotografar(sessao)[1]).encode()).hexdigest()


def hash_pixels(superficie):
    return hashlib.md5(pygame.image.tobytes(superficie, 'RGB')).hexdigest()
