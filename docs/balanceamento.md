# Fase 7 — QA e balanceamento

Relatório da passagem final de qualidade e do primeiro balanceamento por dados. Todos os ajustes ficaram em arquivos de dados (`config/`), e o jogo clássico continua idêntico ao original (golden master).

## 1. Qualidade

| Item | Resultado |
|---|---|
| Aviso `libpng warning: bKGD: invalid` | Vinha só de `assets/imgs/base.png` (bloco de metadados malformado). Bloco removido; pixels idênticos, golden master passando. |
| Desempenho (pior caso de cada tela) | Nenhuma tela passa de 37% do tempo por quadro. Partidas: 11–19% de 33,3 ms. Menus, mapas e loja: 17–27% de 16,7 ms. |
| Executável (PyInstaller) | Gera e abre com assets e músicas. Teste novo: no executável, o save vai para a pasta de dados do usuário (`%LOCALAPPDATA%\FlappyBird` no Windows; equivalentes no macOS e no Linux). |
| Suíte de testes | 171 testes. |

## 2. Dificuldade

### Método

`tools/playtest.py` põe um robô para jogar as 25 casas do Flappy e da Galaga, 16 vezes cada, com limites humanos: tempo de reação, ritmo máximo de toques (o mesmo do cálculo de justiça do jogo) e imprecisão na mira. Há três habilidades: `casual`, `medio` e `experiente`.

Como ler os números: o robô experiente vence o nível 1 sempre e perde vidas de forma realista, então serve como referência de "jogador bom". Na Galaga, o robô morre muito para mergulhos e chefões, então só a **forma** da curva é confiável, não os valores. O Donkey Kong não tem robô: desviar de salvas de barris exige um planejamento que um robô simples faria mal.

### Ajustes aplicados

| Problema encontrado | Ajuste | Antes → depois (robô experiente) |
|---|---|---|
| Galaga: degrau brusco na casa 6 (4ª linha, leque e perseguição entravam juntos) | Uma novidade por casa: 4ª linha na 6, perseguição na 7, leque na 8, 5ª linha na 13, leque de 5 na 16 | casa 6: 6% → 19% (casual: 38% → 44%) |
| Flappy: casas 21–25 quase impossíveis para um jogador bom (meta subia até 33 canos) | Meta cresce mais devagar: `8 + 0,75 × casa` (9 → 26) | casas 21–24: 0–12% → 6–12% |
| Flappy: chefões mais fáceis que as casas vizinhas (pássaros são alvos menores) | Chefão pede 8 pássaros a mais que a meta da casa | casa 10: 88% → 75% (vizinhas: 81%) |

### Curva atual do Flappy (robô experiente)

| Casas | Vitória | Leitura |
|---|---|---|
| 1–8 | 94–100% | aprendizado: o erro custa uma vida, raramente a casa |
| 9–12 | 50–81% | desafio começa |
| 13–19 | 12–31% | exige domínio |
| 20–25 | 0–31% | desafio final |

## 3. Economia

| | Moedas |
|---|---|
| Modo Livre (robô experiente) | ~10 por minuto |
| Casa vencida | ~7 coletadas + até 30 de bônus (10 por estrela nova) |
| 100 casas com 3 estrelas | ~3.700 no total |

| Skin | Preço | Minutos de Modo Livre | Casas novas com 3 estrelas |
|---|---|---|---|
| Comum mais barata | 50 | 5 | 1,3 |
| Rara mais barata | 250 | 25 | 6,7 |
| Radical mais barata | 1.000 | 98 | 27 |
| Arco-íris (mais cara) | 2.500 | 245 | 67 |
| Todas as comuns + raras | 2.975 | — | dá para comprar só com os mapas |
| Todas as radicais | 6.300 | ~10 h | — |

Leitura: recompensa cedo (uma comum a cada 1–3 casas), raras como meta de médio prazo, radicais como troféu. Não alterei preços.

## 4. Decisões para você

1. **Chefões 15 e 20 do Flappy** ainda são mais fáceis que as vizinhas (69% e 31%, contra 31% e 12%). Opções:
   (a) manter como "respiro" entre casas duras;
   (b) os pássaros do chefão oscilarem mais;
   (c) fase mais longa (40 a 60 pássaros, vira maratona).
2. **Casa 25 do Flappy:** 0% para o robô experiente. Manter como desafio final, ou aliviar o teto da curva (por exemplo, abertura 175 → 185 px em `config/difficulty_profiles.py`)?
3. **Chefões da Galaga e Donkey Kong inteiro:** dependem do seu teste de jogo. Observe se o Boss Galaga das casas 5 e 10 é vencível sem power-up e se as salvas de 3 barris (a partir da casa 14) dão tempo de reação.
4. **Economia:** o Modo Livre rende ~10 moedas/min. Se as radicais parecerem distantes demais, há duas opções: bônus por sequência longa sem cair, ou mais moedas por passagem (`CHANCE_MOEDA_NA_PASSAGEM` em `config/economy.py`).

## 5. Como repetir

```
python tools/playtest.py --habilidade experiente
python tools/playtest.py --habilidade casual --mapas galaga --tentativas 30
```

Depois de mexer em `config/difficulty_profiles.py` ou em `config/levels.py`, a taxa de vitória deve cair de forma gradual, sem degraus entre casas vizinhas.
