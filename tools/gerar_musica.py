"""Gera as músicas de fundo (chiptune) em assets/audio, só com a biblioteca padrão.

    python tools/gerar_musica.py

Cada trilha é uma sequência de compassos com acordes, melodia e bateria,
sintetizada como nos consoles de 8 bits: onda quadrada (melodia), onda
triangular (baixo) e ruído (bateria). O fim de cada trilha emenda no começo
sem estalo, para tocar em loop.

Para mudar uma música, edite as tabelas MENU ou JOGO e rode o script de novo.
"""
import array
import math
import random
import wave
from pathlib import Path

TAXA = 22050                      # amostras por segundo (mono, 16 bits)
DESTINO = Path(__file__).resolve().parents[1] / 'assets' / 'audio'


def freq(nota):
    """Nota MIDI (60 = Dó central) -> frequência em Hz."""
    return 440.0 * 2 ** ((nota - 69) / 12)


# Notas por nome: 'C5' = 72.
NOMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def n(nome):
    acidente = 1 if '#' in nome else 0
    return 12 * (int(nome[-1]) + 1) + NOMES[nome[0]] + acidente


def envelope(i, total, ataque, liberacao):
    """Ataque e liberação lineares: evita estalos no começo e no fim da nota."""
    if i < ataque:
        return i / ataque
    if i > total - liberacao:
        return max(0.0, (total - i) / liberacao)
    return 1.0


def tocar_nota(buffer, inicio, duracao, nota, onda, volume, duty=0.25, decaimento=0.0):
    total = int(duracao * TAXA)
    f = freq(nota)
    fase_passo = f / TAXA
    fase = 0.0
    ataque, liberacao = int(0.004 * TAXA), int(min(0.04, duracao * 0.35) * TAXA)
    for i in range(total):
        indice = inicio + i
        if indice >= len(buffer):
            break
        if onda == 'quadrada':
            valor = 1.0 if (fase % 1.0) < duty else -1.0
        else:                                   # triangular
            x = fase % 1.0
            valor = 4 * x - 1 if x < 0.5 else 3 - 4 * x
        queda = math.exp(-decaimento * i / TAXA) if decaimento else 1.0
        buffer[indice] += valor * volume * envelope(i, total, ataque, liberacao) * queda
        fase += fase_passo


def tocar_bumbo(buffer, inicio, volume):
    total = int(0.12 * TAXA)
    fase = 0.0
    for i in range(total):
        if inicio + i >= len(buffer):
            break
        f = 120 * math.exp(-i / (0.03 * TAXA)) + 45
        fase += f / TAXA
        buffer[inicio + i] += math.sin(2 * math.pi * fase) * volume * (1 - i / total)


def tocar_ruido(buffer, inicio, duracao, volume, aleatorio):
    total = int(duracao * TAXA)
    anterior = 0.0
    for i in range(total):
        if inicio + i >= len(buffer):
            break
        bruto = aleatorio.uniform(-1, 1)
        anterior = anterior * 0.35 + bruto * 0.65       # ruído um pouco mais "macio"
        ataque = min(1.0, i / (0.002 * TAXA))                   # 2 ms: sem estalo
        buffer[inicio + i] += anterior * volume * ataque * (1 - i / total) ** 2


def renderizar(trilha):
    bpm, compassos = trilha['bpm'], trilha['compassos']
    colcheia = 60 / bpm / 2
    amostras_colcheia = colcheia * TAXA
    total = round(len(compassos) * 8 * amostras_colcheia)
    melodia = [0.0] * total
    resto = [0.0] * total
    aleatorio = random.Random(trilha['semente'])
    for c, (acorde, notas) in enumerate(compassos):
        base = c * 8
        for passo, nota in enumerate(notas):
            if nota is None:
                continue
            inicio = round((base + passo) * amostras_colcheia)
            tocar_nota(melodia, inicio, colcheia * 0.92, n(nota), 'quadrada',
                       trilha['vol_melodia'], duty=0.25, decaimento=trilha['decaimento'])
        raiz = n(acorde)
        for passo in range(8):
            inicio = round((base + passo) * amostras_colcheia)
            nota_baixo = raiz + (12 if passo % 2 else 0)
            tocar_nota(resto, inicio, colcheia * 0.9, nota_baixo, 'triangular', trilha['vol_baixo'])
            if passo in (0, 4):
                tocar_bumbo(resto, inicio, trilha['vol_bumbo'])
            if passo in (2, 6):
                tocar_ruido(resto, inicio, 0.10, trilha['vol_caixa'], aleatorio)
            tocar_ruido(resto, inicio, 0.025, trilha['vol_chimbal'], aleatorio)
    # Filtro passa-baixa de um polo na melodia: tira a aspereza da onda quadrada.
    suave, y = [], 0.0
    for x in melodia:
        y += 0.35 * (x - y)
        suave.append(y)
    mix = [a + b for a, b in zip(suave, resto)]
    rampa = int(0.004 * TAXA)                                   # emenda do loop: começa em zero
    for i in range(rampa):
        mix[i] *= i / rampa
    pico = max(1e-9, max(abs(v) for v in mix))
    escala = 0.7 / pico
    return array.array('h', (int(max(-1.0, min(1.0, v * escala)) * 32767) for v in mix))


def salvar(nome, amostras):
    DESTINO.mkdir(parents=True, exist_ok=True)
    caminho = DESTINO / nome
    with wave.open(str(caminho), 'wb') as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(TAXA)
        arquivo.writeframes(amostras.tobytes())
    return caminho


# Cada compasso: (acorde, 8 colcheias da melodia; None = pausa)
MENU = {
    'bpm': 112, 'semente': 3, 'decaimento': 3.0,
    'vol_melodia': 0.30, 'vol_baixo': 0.30, 'vol_bumbo': 0.45, 'vol_caixa': 0.16, 'vol_chimbal': 0.05,
    'compassos': [
        ('C3', ['E5', 'G5', 'C6', 'G5', 'E5', 'G5', 'D5', 'E5']),
        ('A2', ['C5', 'E5', 'A5', 'E5', 'C5', 'E5', 'B4', 'C5']),
        ('F2', ['A4', 'C5', 'F5', 'C5', 'A4', 'C5', 'G4', 'A4']),
        ('G2', ['B4', 'D5', 'G5', 'D5', 'B4', 'D5', 'F5', 'D5']),
        ('C3', ['G5', 'E5', 'C5', 'E5', 'G5', 'C6', 'B5', 'G5']),
        ('A2', ['A5', 'E5', 'C5', 'E5', 'A5', 'C6', 'B5', 'A5']),
        ('F2', ['F5', 'C5', 'A4', 'C5', 'F5', 'A5', 'G5', 'F5']),
        ('G2', ['D5', 'G5', 'B5', 'G5', 'F5', 'D5', 'B4', None]),
    ],
}

JOGO = {
    'bpm': 144, 'semente': 9, 'decaimento': 5.0,
    'vol_melodia': 0.28, 'vol_baixo': 0.34, 'vol_bumbo': 0.55, 'vol_caixa': 0.22, 'vol_chimbal': 0.07,
    'compassos': [
        ('A2', ['A4', 'C5', 'E5', 'A5', 'G5', 'E5', 'C5', 'E5']),
        ('F2', ['F4', 'A4', 'C5', 'F5', 'E5', 'C5', 'A4', 'C5']),
        ('C3', ['G4', 'C5', 'E5', 'G5', 'E5', 'C5', 'G4', 'C5']),
        ('G2', ['G4', 'B4', 'D5', 'G5', 'F5', 'D5', 'B4', 'D5']),
        ('A2', ['E5', 'A5', 'C6', 'A5', 'E5', 'A5', 'B5', 'C6']),
        ('F2', ['C6', 'A5', 'F5', 'A5', 'C6', 'A5', 'G5', 'F5']),
        ('C3', ['E5', 'G5', 'C6', 'G5', 'E5', 'D5', 'C5', 'D5']),
        ('E2', ['E5', 'G#5', 'B5', 'G#5', 'E5', 'D5', 'B4', None]),
    ] * 2,
}


if __name__ == '__main__':
    for nome, trilha in (('musica_menu.wav', MENU), ('musica_jogo.wav', JOGO)):
        caminho = salvar(nome, renderizar(trilha))
        segundos = len(trilha['compassos']) * 8 * 60 / trilha['bpm'] / 2
        print(f'{caminho.name}: {segundos:.1f} s, {caminho.stat().st_size // 1024} KB')
