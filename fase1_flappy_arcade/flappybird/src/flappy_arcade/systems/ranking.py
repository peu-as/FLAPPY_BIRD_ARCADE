"""Ranking Top 10 persistente (ranking.json), com escrita atômica.

O antigo recorde.json é lido uma única vez, só para importar o recorde.
"""
import json
import os
import time

from ..config.constants import MAX_NOME, MAX_REGISTROS, NIVEL_MAXIMO
from ..core.paths import ARQUIVO_RANKING, ARQUIVO_RECORDE


def ler_recorde():
    """Lê o recorde do formato ANTIGO (recorde.json).
    Hoje só serve para importar o recorde anterior para o ranking novo.

    O bloco with fecha o arquivo automaticamente, inclusive em erros.
    """
    try:
        with ARQUIVO_RECORDE.open(encoding='utf-8') as arq:
            dados = json.load(arq)
        pontos = dados.get('pontos', 0)
        nome = dados.get('nome', 'Anônimo')
        return (pontos if type(pontos) is int and pontos >= 0 else 0,
                nome if isinstance(nome, str) else 'Anônimo')
    except (OSError, ValueError, TypeError):
        return 0, 'Anônimo'

# Jogadores e ranking (Top 10)
# O arquivo data/ranking.json guarda o último jogador e uma lista de
# registros. Cada partida com pontuação maior que 0 vira UM registro:
# {"nome": "Ana", "pontos": 120, "data": "2026-10-28 15:42"}
# A lista é mantida ordenada: mais pontos primeiro; em caso de empate,
# quem chegou primeiro fica na frente.

def limpar_nome(texto):
    """Remove espaços das pontas e repetidos e limita o tamanho a MAX_NOME.

    Devolve '' se não sobrar nenhum caractere visível.
    """
    return ' '.join(str(texto).split())[:MAX_NOME].strip()

def _registro_valido(registro):
    """True se o item lido do JSON tem nome (texto) e pontos (inteiro > 0)."""
    return (isinstance(registro, dict)
            and isinstance(registro.get('nome'), str)
            and bool(limpar_nome(registro['nome']))
            and type(registro.get('pontos')) is int
            and registro['pontos'] > 0)

def ordenar_ranking(registros):
    """Ordena do melhor para o pior; a data desempata (o mais antigo vence)."""
    return sorted(registros, key=lambda r: (-r['pontos'], r.get('data', '')))

def ler_ranking():
    """Lê o ranking do JSON. Devolve (registros ordenados, último jogador).

    Se o arquivo não existir (ou estiver corrompido), começa vazio, mas
    aproveita o recorde do formato antigo (recorde.json), quando houver.
    Registros inválidos são ignorados em vez de derrubar o jogo.
    """
    registros, ultimo = [], ''
    try:
        with ARQUIVO_RANKING.open(encoding='utf-8') as arq:
            dados = json.load(arq)
        for r in dados.get('registros', []):
            if _registro_valido(r):
                nivel = r.get('nivel', 0)
                registros.append({'nome': limpar_nome(r['nome']),
                                  'pontos': r['pontos'],
                                  'data': str(r.get('data', '')),
                                  # nível alcançado e se a pessoa zerou o jogo
                                  'nivel': nivel if type(nivel) is int and 0 <= nivel <= NIVEL_MAXIMO else 0,
                                  'zerou': r.get('zerou') is True})
        ultimo = dados.get('ultimo_jogador', '')
        ultimo = limpar_nome(ultimo) if isinstance(ultimo, str) else ''
    except (OSError, ValueError, TypeError, AttributeError):
        pontos, nome = ler_recorde()
        if pontos > 0:
            registros.append({'nome': nome, 'pontos': pontos, 'data': '',
                              'nivel': 0, 'zerou': False})
    return ordenar_ranking(registros)[:MAX_REGISTROS], ultimo

def salvar_ranking(registros, ultimo_jogador):
    """Grava o ranking em JSON UTF-8 e devolve True/False.

    A escrita é "atômica": grava num arquivo temporário e só então troca o
    arquivo definitivo (os.replace). Se o jogo fechar no meio, o ranking
    antigo continua íntegro.
    """
    try:
        ARQUIVO_RANKING.parent.mkdir(parents=True, exist_ok=True)
        temporario = ARQUIVO_RANKING.with_suffix('.tmp')
        with temporario.open('w', encoding='utf-8') as arq:
            # ensure_ascii=False mantém acentos; indent=2 formata o JSON.
            json.dump({'ultimo_jogador': ultimo_jogador,
                       'registros': registros[:MAX_REGISTROS]},
                      arq, ensure_ascii=False, indent=2)
        os.replace(temporario, ARQUIVO_RANKING)
        return True
    except OSError as erro:
        print(f'Aviso: não foi possível gravar o ranking: {erro}')
        return False

def adicionar_registro(registros, nome, pontos, nivel=1, zerou=False):
    """Insere uma partida no ranking.

    Cada registro também guarda o NÍVEL alcançado e se o
    jogador ZEROU o jogo (concluiu o nível 10).

    Devolve (nova lista ordenada, posição da partida) com posição a partir
    de 1. Partidas com 0 pontos não entram: a posição volta None.
    """
    if pontos <= 0:
        return registros, None
    novo = {'nome': nome, 'pontos': pontos,
            'data': time.strftime('%Y-%m-%d %H:%M'),
            'nivel': nivel, 'zerou': bool(zerou)}
    ordenados = ordenar_ranking(registros + [novo])
    posicao = next(i for i, r in enumerate(ordenados, start=1) if r is novo)
    return ordenados[:MAX_REGISTROS], posicao
