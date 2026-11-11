# Balanceamento e QA

A **Fase 14** (no fim deste documento) recalibrou a economia, resolveu as quatro decisões da Fase 7 e refez a passagem de qualidade com as artes novas.

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


---

# Fase 14 — economia, decisões e QA final

## 1. Economia (~3x a renda)

A loja agora tem 85 skins e 31 cenários: **53.395 moedas** ao todo (31.645 em skins, 21.750 em cenários). Meta: completar os quatro mapas com 3 estrelas paga cerca de **1/3 da loja**; o resto vem do Modo Livre.

| Regra (`config/economy.py`) | Fase 7 | Fase 14 |
|---|---|---|
| Chance de moeda na passagem | 0,6 | 0,9 |
| Moeda na Galaga | a cada 3 s | a cada 2 s |
| Moedas por banana (Donkey) | 1 | 2 |
| Bônus por estrela nova | 10 fixo | `20 + 2 × casa` (22 na casa 1, 70 na casa 25) |
| Bônus de sequência (Modo Livre) | — | +10 a cada 10 pontos seguidos sem cair ("+10 SEQUÊNCIA!") |

| Medição | Fase 7 | Fase 14 |
|---|---|---|
| Modo Livre, jogador bom (robô experiente) | ~10 moedas/min | **~26 moedas/min** |
| Modo Livre, jogador médio | — | ~16 moedas/min |
| Bônus de estrelas, 4 mapas com 3 estrelas | 3.000 | **13.800** |
| Mapas completos (estrelas + moedas coletadas) | ~3.700 (7% da loja) | **~15.500 a 17.000 (29–32% da loja)** |

| Item | Preço | Modo Livre (jogador bom) | Pelos mapas |
|---|---|---|---|
| Fantasia simples | 120 | ~5 min | as 2 primeiras casas com 3 estrelas |
| Time | 200 | ~8 min | ~3 casas |
| Fantasia detalhada | 350–500 | 13–19 min | — |
| Cenário novo | 600 / 900 / 1.300 | 23 / 34 / 49 min | — |
| Radical | 1.000–2.500 | 38–95 min | — |
| Loja inteira | 53.395 | ~23 h além dos mapas | — |

Leitura: recompensa logo no começo, metas médias a cada sessão e a coleção completa como objetivo de longo prazo. Testes: `tests/test_balanceamento.py` confere a faixa de 20 a 40% e que as duas primeiras casas já compram uma fantasia simples.

## 2. As quatro decisões da Fase 7

| # | Decisão | O que foi feito | Resultado (robô experiente, 32 tentativas) |
|---|---|---|---|
| 1 | Chefões 15 e 20 do Flappy mais fáceis que as vizinhas | O chefão é **um degrau acima**: usa a abertura de 3 casas à frente, pássaros oscilam 1,5x (até 36 px) e a meta cresce +2 a cada chefão (`config/levels.py`) | 15: 69% → **47%** (vizinhas 28–56%) · 20: 31% → **9%** (vizinhas 9–22%) |
| 2 | Casa 25 do Flappy em 0% | Teto da abertura aliviado: 175 → **182 px** (`config/difficulty_profiles.py`) | 25: 0% → **3%**; continua o desafio final |
| 3 | Chefões da Galaga e Donkey Kong | **Mantidos.** O robô da Galaga morre demais nos mergulhos (só a forma da curva vale) e o Donkey não tem robô. Os chefões da Galaga soltam bônus nos marcos de 66% e 33% da vida | Para o seu teste: veja abaixo |
| 4 | Ritmo da economia | Seção 1 | ~2,7x no Modo Livre, ~4x nos mapas |

**Para o seu teste de jogo (decisão 3):** se o Boss Galaga das casas 5 e 10 parecer impossível sem bônus, diminua `chefe_hp` ou aumente `chefe_intervalo` em `GALAGA` (`config/difficulty_profiles.py`). Se as salvas de 3 barris do Donkey (casa 14 em diante) não derem tempo de reação, adie o degrau `14: 3` de `salva_max` ou baixe `chance_tres` em `DONKEY`; para o Kong Furioso, aumente `chefe_intervalo` ou adie o degrau de `chefe_barris`. Depois rode `python -m pytest tests/test_difficulty_curve.py`.

### Curva final do Flappy

| Casas | Vitória (robô experiente) | Leitura |
|---|---|---|
| 1–9 | 81–100% | aprendizado |
| 10–13 | 41–75% | desafio começa (chefão 10: 66%) |
| 14–19 | 22–47% | exige domínio (chefão 15: 47%) |
| 20–25 | 0–12% | desafio final (chefões 20 e 25: 9% e 3%) |

## 3. Qualidade

| Item | Resultado |
|---|---|
| Suíte de testes | 456 testes, golden master do clássico incluído |
| Desempenho, partidas (orçamento 33,3 ms) | Modo Livre + Galaga + bônus + cenários: média 5,6 ms; pior quadro isolado entre 26 e 36 ms conforme a medição, e 99% dos quadros abaixo de 13 ms. Donkey: média 3,7 ms, pior 20 ms |
| Desempenho, menus (orçamento 16,7 ms) | Menu 1,9 ms, mapa 2,4 ms, Equipamentos 4,0 ms; loja: média 5,6 ms, 99% dos quadros abaixo de 17 ms. Pico único de 30–50 ms ao trocar a vista de um cenário pela primeira vez (montagem da prévia) |
| Executável (PyInstaller) | Gera e abre (menu e Modo Livre); 67 skins e 20 cenários dentro; as folhas de `artes/` ficam de fora (~29 MB) |
| Correções desta fase | `tools/playtest.py` não trava mais se um processo morrer (avisa e para); miniaturas da loja montadas uma por quadro |

## 4. Antes de cada commit

```
python tools/verificar_jogo.py
```

Abre todas as telas sem janela, confere as artes e roda os testes; termina com **PRONTO PARA O COMMIT** ou com a lista do que corrigir.


---

# Fase 15 — modo Estilingue

## Como a dificuldade foi medida

`tools/playtest_estilingue.py` tem dois robôs:

- **Perfeito** (padrão): busca exaustiva de ângulo, força e momento da habilidade. Responde "esta casa dá para vencer?". As 25 casas dão.
- **Humano** (`--humano N`): escolhe a melhor jogada, mas a executa com erro de mira de uma pessoa (±2,5° no ângulo, ±5% na força, ±0,15 s no clique da habilidade). Mede a dificuldade de verdade.

## Calibração dos materiais

Medida com o pássaro comum batendo de frente num bloco de 40×80 (`tests/test_estilingue.py` confere):

| Material | Vida | Quebra com |
|---|---|---|
| Gelo | 12 | um toque médio (~500 px/s) |
| Madeira | 48 | um bom acerto (~700 px/s); a Semente-Foguete faz 2,2x de dano |
| Pedra | 380 | ~3 batidas fortes, ou explosões |
| Barril | 18 | qualquer batida; explode (raio 140 px) e pode explodir outros |
| Inseto / chefão | 32 / 240 | uma batida firme / vários golpes |

## Curva (robô humano, 8 tentativas por casa)

| Casas | Vitórias | Estrelas médias | Leitura |
|---|---|---|---|
| 1–6 | 87–100% | 1,6–2,9 | aprender a mirar, gelo, Pena Dupla, barris (chefão 5: 87%) |
| 7–13 | 75–100% | 1,2–1,9 | muros, Semente-Foguete, Ovo Nova (chefão 10: 87%) |
| 14–20 | 75–100% | 1,5–2,3 | fortalezas de pedra (chefão 15: 100% / 2,0; chefão 20: 75%) |
| 21–25 | 50–100% | 1,2–2,2 | castelo final (24 e 25: 50%) |

Ajustes feitos a partir das medições: a casa 2 trocou uma estrutura de madeira por gelo (estava em 40%); nas casas finais o Ovo Nova passou a vir mais tarde na fila (sozinho, abrindo a casa, resolvia tudo); a casa 11 ganhou um pássaro (37% → 87%); as casas 19 e 20 perderam um (fáceis demais).

**Para o seu teste de jogo:** o robô mira com uma precisão constante; uma pessoa erra mais no começo e acerta mais depois de algumas tentativas na mesma casa. Se alguma casa parecer injusta, mude a fila de pássaros (`passaros`) ou o material de um módulo em `CASAS_ESTILINGUE` e rode `python tools/playtest_estilingue.py --casas N` e `--humano 8 --casas N`.

## Desempenho

A física é leve: 0,02–0,09 ms por quadro nas casas mais cheias. O executável (com a pymunk dentro) tem ~30 MB e abre as casas do Estilingue.

---

# Fase 16 — modo Combina 3 (o jogo)

Nesta fase as 25 casas pedem só **pontos em 20 jogadas** (tabela provisória para o jogo já ser jogável). A Fase 17 troca a tabela por objetivos variados (coletar peças, quebrar gelo e caixas, chefões com vida) e liga o botão do menu.

## Como foi medido

`tools/playtest_combina3.py` joga partidas inteiras só com as regras (sem tela), com três jogadores:

- **Aleatório:** escolhe qualquer troca válida (quem só segue a dica).
- **Médio:** na metade das jogadas escolhe a troca que mais pontua; na outra metade, qualquer uma.
- **Bom:** escolhe a melhor troca 9 em cada 10 vezes.

Pontos em 30 jogadas, 6 tipos de peça, 200 partidas por jogador:

| Jogador | 10% piores | Mediana | 10% melhores | Por jogada |
|---|---|---|---|---|
| Aleatório | 3.380 | 4.920 | 7.320 | 175 |
| Médio | 6.320 | 9.270 | 14.310 | 329 |
| Bom | 9.620 | 13.170 | 18.890 | 463 |

Decisão tirada daqui: **6 tipos de peça em todas as casas**. Com 5 tipos as cascatas mais que dobram os pontos e o resultado vira sorte; a dificuldade sobe pela meta (e, na Fase 17, pelos obstáculos), não pelo número de tipos.

## Metas

`meta = 20 jogadas x (150 + 7 por casa)`, arredondada para a centena; as casas 5, 10, 15, 20 e 25 pedem 15% a mais. Vai de 3.000 (casa 1) a 7.300 (casa 25). Estrelas: 3 sobrando 6 jogadas ou mais, 2 sobrando 3 ou mais, 1 se bater a meta no fim.

## Curva (120 partidas por casa)

| Casas | Meta | Médio: vitórias / estrelas | Bom: vitórias / estrelas |
|---|---|---|---|
| 1–4 | 3.000–3.400 | 95–98% / 2,7–2,9 | 100% / 2,9–3,0 |
| 5 (chefe) | 4.100 | 88% / 2,6 | 96% / 2,8 |
| 6–9 | 3.700–4.100 | 89–94% / 2,5–2,7 | 98–99% / 2,8–2,9 |
| 10 (chefe) | 4.900 | 77% / 2,3 | 93% / 2,6 |
| 11–14 | 4.400–4.800 | 75–86% / 2,2–2,4 | 95–96% / 2,7–2,8 |
| 15 (chefe) | 5.700 | 60% / 2,2 | 89% / 2,5 |
| 16–19 | 5.100–5.500 | 63–73% / 2,1–2,4 | 88–95% / 2,5–2,7 |
| 20 (chefe) | 6.500 | 40% / 2,0 | 79% / 2,3 |
| 21–24 | 5.800–6.200 | 46–59% / 2,0–2,3 | 85–87% / 2,3–2,5 |
| 25 (chefe) | 7.300 | 36% / 2,0 | 65% / 2,5 |

Leitura: quem joga com atenção passa quase sempre até a casa 14 e sente o aperto nos chefões 20 e 25; quem só troca o que aparece empaca por volta da casa 15. É a mesma forma de curva dos outros mapas.

**Para o seu teste de jogo:** uma pessoa tende a jogar melhor que o "médio" quando aprende a montar Pena-Raio e Ovo Nova de propósito. Se as casas finais parecerem fáceis ou injustas, mude `PONTOS_POR_JOGADA_A_MAIS` ou `EXTRA_CHEFE` em `config/combina3.py` e rode `python tools/playtest_combina3.py --casas` (uns 5 minutos com as 40 partidas padrão; `--partidas 120` para mais precisão).

## Moedas

1 por peça especial criada, 1 a cada 2 jogadas que sobram e 4 pela vitória, mais o bônus de estrelas que todo mapa dá. A conta fina da economia dos dois modos novos fica para a Fase 18.

---

# Fase 17 — mapa do Combina 3 (objetivos e chefões)

As metas de pontos da Fase 16 deram lugar a 25 casas com objetivos variados: 4 de pontos, 6 de coletar, 7 de gelo/caixas (algumas com os dois) e 5 chefões. A curva foi medida com `python tools/playtest_combina3.py --casas --partidas 40`, com o robô mirando no objetivo da casa (e não só nos pontos).

## Chefões

Medido: o jogador médio tira cerca de **8,7 de vida por jogada** (o bom, ~10,8), já contando os ataques que tampam casas. A vida de cada chefão foi posta perto de "jogadas × 8,7", subindo devagar:

| Casa | Chefão | Vida | Ataca a cada | Ataque |
|---|---|---|---|---|
| 5 | Rei-Inseto | 160 | 4 jogadas | 2 casulos |
| 10 | Kong | 165 | 4 jogadas | 2 barris |
| 15 | Rei-Inseto | 180 | 3 jogadas | 3 casulos |
| 20 | Kong | 190 | 3 jogadas | 2 barris |
| 25 | os dois | 235 | 3 jogadas | 2 casulos + 1 barril |

Bravo (metade da vida): uma casa a mais por ataque.

## Curva (40 partidas por casa)

| Casas | Médio: vitórias / estrelas | Bom: vitórias / estrelas | Leitura |
|---|---|---|---|
| 1–4 | 85–100% / 2,6–2,9 | 92–100% / 2,9–3,0 | aprender: pontos, coletar, gelo |
| 5 (chefe) | 82% / 1,8 | 92% / 2,5 | primeiro chefão |
| 6–9 | 70–100% / 2,0–2,9 | 77–97% / 2,3–2,9 | caixas, pedras, gelo grosso |
| 10 (chefe) | 72% / 1,7 | 92% / 2,2 | Kong e os barris |
| 11–14 | 60–87% / 2,1–2,8 | 85–95% / 2,5–2,9 | misturas |
| 15 (chefe) | 60% / 1,7 | 90% / 2,1 | |
| 16–19 | 50–80% / 2,1–2,6 | 72–95% / 2,4–2,7 | |
| 20 (chefe) | 55% / 1,4 | 85% / 2,0 | |
| 21–24 | 47–60% / 2,0–2,6 | 77–95% / 2,2–2,7 | reta final |
| 25 (chefe) | 35% / 1,4 | 57% / 1,8 | os dois chefões |

Ajustes feitos a partir das medições: chefões com vida bem menor (a primeira tabela tinha 230–520: 0–20% de vitória); a casa 3 trocou o gelo do fundo pelo do meio (no fundo, só 33%); gelo grosso afinado nas casas 8, 14, 17, 22 e 24 (o último pedacinho de gelo num canto custa muitas jogadas); coletas um pouco menores nas casas 9, 18 e 22; casas 16 e 23 com mais caixas (estavam fáceis).

**Para o seu teste de jogo:** o robô "bom" enxerga as peças que vão cair (ele testa a jogada numa cópia do tabuleiro), então joga melhor que uma pessoa atenta; o "médio" é a melhor referência. Se uma casa de gelo parecer injusta, troque `G` por `g` no desenho do tabuleiro; se um chefão parecer forte, baixe a `vida` ou aumente `a_cada` em `CASAS_COMBINA3`.
