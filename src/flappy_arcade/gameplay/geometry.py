"""Funções geométricas puras usadas pelas fases."""

def bezier(p0, p1, p2, t):
    """Ponto de uma curva de Bézier quadrática, com t de 0 a 1.

    B(t) = (1-t)²·P0 + 2(1-t)t·P1 + t²·P2
    P0 é o início, P2 é o fim e P1 (ponto de controle) "puxa" a curva.
    É assim que os inimigos fazem trajetórias curvas de entrada e mergulho.
    """
    u = 1 - t
    return (u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
            u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1])

def colide_circulo(cx, cy, raio, caixa):
    """Colisão círculo x retângulo: acha o ponto do retângulo mais próximo
    do centro do círculo e compara a distância com o raio."""
    px = max(caixa.left, min(cx, caixa.right))
    py = max(caixa.top, min(cy, caixa.bottom))
    return (cx - px)**2 + (cy - py)**2 < raio**2
