"""Gera os efeitos sonoros dos modos novos (Estilingue e Combina 3) em assets/audio.

    python tools/gerar_sons.py

Síntese de 8 bits só com a biblioteca padrão, como tools/gerar_musica.py:
ondas quadrada, triangular e senoidal, varreduras de frequência e ruído
filtrado. O sorteador tem semente fixa, então rodar de novo gera os mesmos
arquivos. Para mudar um som, edite a função dele e rode o script.

Arquivos (prefixo sfx_): veja SONS no fim deste arquivo. O jogo os carrega em
gameplay/resources.py (Recursos.sons) com o nome sem o prefixo.
"""
import array
import math
import random
import wave
from pathlib import Path

TAXA = 22050                      # amostras por segundo (mono, 16 bits)
DESTINO = Path(__file__).resolve().parents[1] / 'assets' / 'audio'
sorteio = random.Random(18)


# ---------------------------------------------------------------- blocos de síntese
def vazio(segundos):
    return [0.0] * int(segundos * TAXA)


def somar(base, outro, inicio=0.0, volume=1.0):
    i0 = int(inicio * TAXA)
    if len(base) < i0 + len(outro):
        base.extend([0.0] * (i0 + len(outro) - len(base)))
    for i, v in enumerate(outro):
        base[i0 + i] += v * volume
    return base


def tom(segundos, f_inicio, f_fim=None, onda='seno', decaimento=6.0, duty=0.5, vibrato=0.0):
    """Uma nota que vai de f_inicio a f_fim (varredura exponencial), com queda de volume."""
    f_fim = f_fim or f_inicio
    total = int(segundos * TAXA)
    fase, saida = 0.0, []
    for i in range(total):
        t = i / total
        f = f_inicio * (f_fim / f_inicio) ** t
        if vibrato:
            f *= 1 + 0.03 * math.sin(2 * math.pi * vibrato * i / TAXA)
        fase += f / TAXA
        x = fase % 1.0
        if onda == 'quadrada':
            v = 1.0 if x < duty else -1.0
        elif onda == 'triangular':
            v = 4 * x - 1 if x < 0.5 else 3 - 4 * x
        else:
            v = math.sin(2 * math.pi * x)
        ataque = min(1.0, i / (0.003 * TAXA))
        saida.append(v * ataque * math.exp(-decaimento * i / TAXA))
    return saida


def ruido(segundos, corte=0.3, decaimento=8.0):
    """Ruído branco passado por um filtro passa-baixa simples (corte de 0 a 1: abafado a brilhante)."""
    total = int(segundos * TAXA)
    saida, anterior = [], 0.0
    for i in range(total):
        anterior += corte * (sorteio.uniform(-1, 1) - anterior)
        ataque = min(1.0, i / (0.002 * TAXA))
        saida.append(anterior * ataque * math.exp(-decaimento * i / TAXA))
    return saida


def salvar(nome, amostras, volume=0.8):
    pico = max(1e-6, max(abs(v) for v in amostras))
    fim = int(0.006 * TAXA)                                   # some sem estalo
    dados = array.array('h')
    for i, v in enumerate(amostras):
        suave = min(1.0, (len(amostras) - i) / fim)
        dados.append(int(v / pico * volume * suave * 32767))
    with wave.open(str(DESTINO / f'sfx_{nome}.wav'), 'wb') as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(TAXA)
        arquivo.writeframes(dados.tobytes())


# ---------------------------------------------------------------- Estilingue
def lancar():
    """Elástico soltando: twang que sobe + sopro."""
    s = tom(0.22, 140, 420, 'quadrada', decaimento=9, duty=0.3)
    return somar(s, ruido(0.25, corte=0.5, decaimento=12), 0.02, 0.5)


def habilidade():
    """Brilho rápido subindo (Pena Dupla, Semente-Foguete, Ovo Nova)."""
    s = vazio(0.05)
    for k, f in enumerate((660, 880, 1320)):
        somar(s, tom(0.09, f, onda='quadrada', decaimento=18, duty=0.25), k * 0.045, 0.6)
    return s


def madeira():
    """Tábua quebrando: estalo seco e um corpo grave."""
    s = ruido(0.16, corte=0.35, decaimento=26)
    somar(s, tom(0.18, 190, 110, 'triangular', decaimento=20), 0.0, 0.9)
    return somar(s, ruido(0.08, corte=0.6, decaimento=40), 0.05, 0.5)


def gelo():
    """Vidro/gelo partindo: pings agudos espalhados e um chiado brilhante."""
    s = ruido(0.12, corte=0.9, decaimento=30)
    for _ in range(6):
        somar(s, tom(0.18, sorteio.uniform(2200, 4200), onda='seno', decaimento=22),
              sorteio.uniform(0.0, 0.12), 0.45)
    return s


def pedra():
    """Pedra rachando: baque grave e pesado."""
    s = tom(0.3, 95, 55, 'triangular', decaimento=11)
    return somar(s, ruido(0.25, corte=0.12, decaimento=14), 0.0, 1.2)


def explosao():
    """Barril/Ovo Nova: estrondo abafado que some devagar."""
    s = ruido(0.7, corte=0.08, decaimento=5.5)
    somar(s, tom(0.5, 120, 40, 'triangular', decaimento=6), 0.0, 0.8)
    return somar(s, ruido(0.06, corte=0.8, decaimento=40), 0.0, 0.6)


def inseto():
    """Inseto derrotado: guincho que sobe."""
    return tom(0.16, 700, 1700, 'quadrada', decaimento=10, duty=0.2)


# ---------------------------------------------------------------- Combina 3
def estouro(nivel):
    """Peças combinando: 'pop' curto; cada nível de cascata soa um tom acima."""
    base = 520 * 2 ** (nivel * 3 / 12)
    s = tom(0.09, base * 1.8, base, 'seno', decaimento=24)
    return somar(s, tom(0.07, base * 2.7, base * 2, 'quadrada', decaimento=40, duty=0.25), 0.0, 0.25)


def especial():
    """Peça especial nasceu: arpejo de 4 notas."""
    s = vazio(0.05)
    for k, nota in enumerate((72, 76, 79, 84)):
        f = 440 * 2 ** ((nota - 69) / 12)
        somar(s, tom(0.12, f, onda='quadrada', decaimento=14, duty=0.25), k * 0.055, 0.55)
    return s


def raio():
    """Pena-Raio / Arco-íris disparando: zap que desce."""
    s = tom(0.26, 2400, 260, 'quadrada', decaimento=7, duty=0.4)
    return somar(s, ruido(0.2, corte=0.7, decaimento=14), 0.0, 0.3)


def ataque_chefe():
    """Chefão atacando: rosnado grave e desafinado."""
    s = tom(0.55, 92, 70, 'quadrada', decaimento=3.5, duty=0.4, vibrato=9)
    return somar(s, tom(0.55, 97, 74, 'quadrada', decaimento=3.5, duty=0.3, vibrato=7), 0.0, 0.8)


def chefe_ferido():
    """Chefão levou dano: batida curta e um gemido descendo."""
    s = ruido(0.08, corte=0.4, decaimento=30)
    return somar(s, tom(0.2, 320, 180, 'triangular', decaimento=12), 0.02, 0.9)


SONS = {
    'lancar': lancar, 'habilidade': habilidade, 'madeira': madeira, 'gelo': gelo, 'pedra': pedra,
    'explosao': explosao, 'inseto': inseto,
    'estouro1': lambda: estouro(0), 'estouro2': lambda: estouro(1),
    'estouro3': lambda: estouro(2), 'estouro4': lambda: estouro(3),
    'especial': especial, 'raio': raio, 'ataque_chefe': ataque_chefe, 'chefe_ferido': chefe_ferido,
}


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nome, gerar in SONS.items():
        amostras = gerar()
        salvar(nome, amostras)
        print(f'sfx_{nome}.wav  {len(amostras) / TAXA:.2f} s')


if __name__ == '__main__':
    main()
