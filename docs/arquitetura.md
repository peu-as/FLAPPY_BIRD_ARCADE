# Arquitetura — Flappy Arcade

Como rodar: `python src/main.py` (menu principal) · `--livre` ou `--classico` abrem direto · `--casa estilingue 5` abre uma casa de qualquer mapa · testes: `python -m pytest` · antes do commit: `python tools/verificar_jogo.py` · atalhos de teste: `$env:FLAPPY_DEBUG=1; python src/main.py` · **Modo Apresentação: Ctrl + Shift + A no menu principal**

## Pastas

```
src/
  main.py                    ponto de entrada (também o do PyInstaller)
  flappy_arcade/
    core/                    infraestrutura, sem regras de jogo
      app.py                 cria os serviços e roda o loop principal
      scene.py               Scene (base das telas) e SceneManager (pilha)
      display.py             janela redimensionável com letterbox
      event_bus.py           eventos entre módulos (ex.: settings_changed)
      clock.py               relógio do jogo (substituível nos testes)
      paths.py               onde ficam assets e dados do jogador
    config/
      constants.py           física, dificuldade, fases (valores originais)
      difficulty_profiles.py curva de 25 níveis: Rampa/Degraus por parâmetro
      levels.py              mapas de 25 casas + jornada Arcade (capítulos e etapas)
      economy.py             regras das moedas (onde aparecem, quanto valem, bônus)
      skins.py               catálogo de skins: categorias, raridade, preço, cores, efeitos
      tutorial.py            textos das dicas de tutorial dos modos novos
      estilingue.py          modo Estilingue: materiais, pássaros, física e as 25 casas
      combina3.py            modo Combina 3: objetivos, chefões e as 25 casas (tabuleiros em texto), estrelas
      scenarios.py           catálogo de cenários: preço, período (dia/tarde/noite), arquivo
      debug.py               atalhos de teste (FLAPPY_DEBUG=1)
    systems/                 serviços persistentes
      save_manager.py        save.json versionado, atômico, com backup
      apresentacao.py        Modo Apresentação (Ctrl+Shift+A): perfil com tudo liberado, só na memória
      tutorial.py            dicas de tutorial já vistas (seção "tutorial" do save)
      settings_store.py      música / SFX / efeitos visuais
      audio_manager.py       SFX e música em canais separados
      ranking.py             Top 10 (ranking.json)
      progress.py            estrelas por casa; casas liberadas em sequência
      economy.py             Carteira (saldo de moedas)
      shop.py                Loja: comprar e equipar skins
      scenarios.py           ColecaoCenarios: comprar cenários, fixo ou playlist aleatória
    gameplay/                o jogo original, reorganizado
      classic_session.py     estados, ciclo de níveis, entrada e telas
      free_mode.py           Modo Livre: sem vidas, dificuldade pelo tempo
      level_session.py       casas dos mapas: 3 vidas, estrelas; criar_sessao(mapa, casa)
      coins.py               moedas no jogo (ColetorMoedas) + mixin SessaoComMoedas
      skins.py               SkinVisual: desenha a skin no lugar do pássaro
      scenery.py             cenários comprados: montar_retrato, GerenciadorCenarios (máx. 3 na
                             memória), DiretorCenarios (fixo/aleatório) e mixin SessaoComCenarios
      flappy.py              Passaro, Obstaculo, Chao
      galaga.py              fase Galaga e Boss Galaga
      donkey.py              fase Donkey Kong e Kong Furioso
      powerups.py, effects.py, hud.py
      bonus_visuals.py       visual novo dos bônus nos modos novos (itens, efeitos e nomes)
      tutorial.py            balão "DICA" dos modos novos (uma dica por vez, cada uma só uma vez)
      estilingue/            modo Estilingue (física pymunk, fora da física original)
        mundo.py             peças, dano por impulso, explosões, habilidades (sem desenho)
        visual.py            texturas, personagens, estilingue, mira, efeitos
        sessao.py            uma casa: mira, voo, câmera, pontos, moedas, estrelas
      combina3/              modo Combina 3 (regras puras + desenho + sessão)
        tabuleiro.py         regras: trocas, combinações, especiais, cascatas, gelo/caixa/pedra (sem pygame)
        partida.py           regras de uma casa: objetivos, vida do chefão e ataques (sem pygame)
        visual.py            peças, animações de troca/queda, raios, explosões, chefões, ataques, ícones
        sessao.py            uma casa: mouse/teclado, jogadas, meta, dica, moedas, estrelas
      difficulty.py          tabelas originais (10 níveis) + justiça das passagens
      difficulty_curve.py    motor da curva de 25 níveis (lê os perfis)
      geometry.py, procedural.py, resources.py
    scenes/
      main_menu.py           menu principal: 8 modos, loja, equipamentos, Modo Apresentação (Ctrl+Shift+A),
                             configurações, sair
      pause_scene.py         pausa: continuar, configurações, recomeçar, sair
      settings_scene.py      configurações (interruptores) e resetar progresso
      map_scene.py           mapa de 25 casas com rolagem
      level_scene.py         casa: abertura -> jogo -> resultado com estrelas e moedas
      shop_scene.py          loja: abas Skins/Cenários, filtros, vitrine e grade
      equipment_scene.py     Equipamentos: cenário fixo ou playlist aleatória (até 15)
      vitrine.py             prévia combinada (skin sobre o cenário, "Ver em" Flappy/Galaga/Donkey),
                             cartões de cenário e fila de miniaturas
      game_scene.py          conduz a sessão (clássico ou livre)
    ui/
      theme.py               paleta (tirada dos sprites), medidas, animação, fontes
      widgets.py             texto com contorno, painel, estrela, botões, interruptores
tests/
  golden/                    gravação do jogo original e cenários
  test_golden_master.py      regra de ouro: clássico idêntico ao original
  test_difficulty_curve.py   curva: nível 1 = original, monotonia, passagens justas
  test_free_mode.py          regras e HUD do Modo Livre
  test_levels.py             regras das casas e do progresso
  test_menus.py              telas de modo, mapa e casa (fluxo completo)
  test_arcade.py             jornada Arcade: tabela, sessões por casa, mapa
  test_economy.py            carteira, loja, skins, moedas; moedas/skin não mudam a física
  test_polish.py             pausa, configurações, reset, menu, música, transições
  test_assets.py             artes importadas: todas presentes, carregam, cabem no jogo
  test_catalogs.py           categorias e preços, cenários, save v2, coleção de cenários
  test_shop_equipment.py     loja com abas e filtros, compras de cenário, prévias, Equipamentos
  test_balanceamento.py      chefões do Flappy um degrau acima, economia da Fase 14
  test_estilingue.py         Estilingue: casas estáveis, materiais, barris, habilidades, sessão
  test_apresentacao.py       Modo Apresentação: tudo liberado e o save real intacto
  test_sons.py               efeitos dos modos novos: arquivos, gerador reproduzível, sessões
  test_tutorial.py           dicas: uma por vez, só uma vez, guardadas no save, nas casas de verdade
  test_combina3.py           Combina 3: cada regra com tabuleiro montado à mão, objetivos, chefões, ataques, sessão
  test_bonus_visuals.py      bônus novos: nomes, itens, mesma física, clássico com cápsulas
  test_scenery.py            cenários nas fases (Flappy, Galaga, Donkey): memória, trocas, transição,
                             contraste nos 31 cenários, física idêntica
tools/
  gerar_musica.py            compõe e gera as músicas de fundo (assets/audio/musica_*.wav)
  gerar_sons.py              sintetiza os efeitos dos modos novos (assets/audio/sfx_*.wav)
  playtest.py                robô com limites humanos joga as casas (veja docs/balanceamento.md)
  importar_artes.py          folhas de arte (artes/) -> assets/skins e assets/cenarios, com relatório
  verificar_jogo.py          verificação final antes do commit (todas as telas + testes)
  playtest_estilingue.py     robô do Estilingue: casa possível? e, com --humano, a dificuldade
  playtest_combina3.py       robô do Combina 3: pontos por partida e, com --casas, vitórias e estrelas por casa
  previa_artes.py            prévia para conferir tudo que foi importado (--previa X.png)
assets/
  imgs/, audio/              artes e sons do jogo original
  skins/                     67 skins importadas (35 fantasias + 32 times), pixel art 2x
  personagens/wilson/        poses da skin lendária (tools/importar_personagem.py)
  icone/                     ícone do .exe e da janela, feitos da capa (tools/gerar_icone.py)
  cenarios/                  20 faixas de horizonte com 575 px de largura
artes/                       folhas originais (fora de assets/, não vão no executável)
  test_*.py                  save, configurações, áudio, cenas, janela, App
```

## Regras da casa

1. **Dependências só descem:** `scenes` → `gameplay` / `systems` → `config`. A jogabilidade não importa nada de `scenes` nem de `core.app`.
2. **Serviços chegam por injeção:** cenas recebem um `AppContext` (janela, recursos, save, settings, áudio, bus, relógio, pilha de cenas). Nada de variáveis globais.
3. **Tempo só pelo relógio injetado:** nada de `time.monotonic()` ou `pygame.time.get_ticks()` direto na jogabilidade.
4. **Cores só pelo tema:** `Palette.<NOME>`, nunca RGB solto em telas novas.
5. **Dificuldade só pelo provedor:** as fases leem `cfg` e a sessão pede `self.dificuldade.flappy/galaga/donkey(nivel)`. Nada de contas com o número do nível espalhadas pelo código.
6. **O clássico não muda sem o golden master acusar.** Depois de mudar algo de propósito no clássico, ou quando a regra do retrato (`tests/golden/snapshot.py`) mudar, regrave a referência com `python tests/golden/record_legacy.py` e explique no commit.

## Loop (mesma ordem do jogo original)

```
tick(fps da cena do topo) → eventos → update(dt) → draw(tela lógica 575x860) → janela (letterbox)
```

A física é por quadro e calibrada a 30 FPS, por isso a `GameScene` roda a 30 FPS. Telas de menu podem rodar a 60 FPS para animações mais suaves.

## Dificuldade

| Provedor | Onde | Níveis | Usado por |
|---|---|---|---|
| `DificuldadeOriginal` | `gameplay/difficulty.py` | 1 a 10 | jogo clássico (idêntico ao original) |
| `CurvaDificuldade` | `gameplay/difficulty_curve.py` + `config/difficulty_profiles.py` | 1 a 25 | Modo Livre e mapas (casa N = nível N) |

Na curva, o nível 1 é sempre o nível 1 original. Galaga e Donkey terminam no nível 10 original (o teto já testado); o Flappy vai um pouco além (gravidade 1,70, abertura 182 px, velocidade 6,2). Nos mapas, o chefão do Flappy é um degrau acima: abertura de 3 casas à frente e pássaros oscilando mais (`DificuldadeDaCasa`, `config/levels.py`). Para balancear, edite só `config/difficulty_profiles.py` e rode `python -m pytest tests/test_difficulty_curve.py`.

## Modo Livre

Sem cadastro, ranking ou game over. Bater conta uma queda e o pássaro volta com 1,2 s de invulnerabilidade. A dificuldade sobe um nível da curva a cada `LIVRE_SEGUNDOS_POR_NIVEL` (40 s) de jogo, sem contar pausas e alertas, até o 25. Os ciclos continuam depois do 10. Recorde: maior sequência de pontos sem cair (`records.free_best_streak` no save).

## Mapas

Cada casa é um desafio fechado com 3 vidas, na dificuldade do nível N da curva. As casas são sessões que herdam da `ClassicSession`, então a física e as fases são as do original. Chefão nas casas 5, 10, 15, 20 e 25 (no Flappy, a fase dos pássaros), ligado por `cfg['chefe']`. Estrelas: 3 sem perder vida, 2 perdendo uma, 1 perdendo duas. Tempo esgotado na Galaga ou no Donkey é derrota. A casa N + 1 abre quando a N tem estrela.

## Jornada Arcade

`JORNADA` em `config/levels.py` é uma tabela de 5 capítulos (Céus, Selva, Entardecer, Noite, Espaço) com 5 casas cada; `'*'` marca o chefão, sempre na 5ª casa. Estilos: `flappy`, `passaros`, `donkey`, `galaga`. A casa N usa o nível N da curva, seja qual for o estilo. No mapa, o cenário de fundo acompanha o capítulo, cada casa tem um selo com o ícone do estilo e placas marcam os capítulos. Para mudar a jornada, edite a tabela: os testes conferem chefões no lugar certo, estilos misturados e nada repetido três vezes seguidas.

## Economia e skins

- **Moedas** só no Modo Livre, nos mapas e na jornada (o clássico é o original). Flappy: no centro da passagem (por onde o jogador já passa). Galaga: caem soltas, opcionais. Donkey: cada banana vale moedas. O `ColetorMoedas` usa o próprio `random.Random`: nunca o `random` do jogo, senão mudaria a sequência dos canos (há um teste que pega isso).
- **Quanto rende** (Fase 14): 0,9 de chance de moeda por passagem, uma moeda a cada 2 s na Galaga, 2 por banana, +10 a cada 10 pontos seguidos sem cair no Modo Livre e `20 + 2 × casa` por estrela nova. Os números e a lógica estão em `docs/balanceamento.md`.
- **Depósito** na carteira ao fim da partida ou ao sair dela, pela diferença ainda não depositada (seguro se `on_exit` rodar mais de uma vez). Bônus por estrela (`bonus_por_estrela(casa)`) só por estrela nova.
- **Skins** só mudam o desenho: `Passaro.skin` é usado em `Passaro.desenhar`; colisão e máscara continuam no sprite original. Teste: a mesma partida com e sem moedas/skin tem física idêntica por 1.500 quadros.
- **Skins** em três categorias: Clássicas (18, as da Fase 5), Fantasias (35 artes + a lendária) e Times (32 artes). As artes (`tipo='arte'`) são carregadas só quando usadas (`Recursos.arte_skin`).
- **Skin lendária** (Fase 22, raridade `LENDARIA`, 5000 moedas, a mais cara do jogo): `tipo='personagem'`, poses em `assets/personagens/wilson/` (`Recursos.poses_personagem`). `gameplay/lendaria.py` escolhe a pose pela velocidade do pássaro (pulo, planar, mergulho, no chão; na vitrine as poses se revezam) e desenha o efeito `lendario`: aura dourada aditiva, rastro de silhuetas, faíscas com gravidade, explosão e onda a cada bater de asas e um reflexo que atravessa o personagem. Como toda skin, só aparência: `tests/test_lendaria.py` confere quadro a quadro que posição, velocidade e retângulo de colisão são idênticos com e sem ela, e que o `random` do jogo não é tocado. O retrato aparece nos cartões da loja e no Estilingue.
- **Preços das skins**: comuns 50–200, raras 250–500, radicais 1000+ (`FAIXAS_PRECO`). Times 200; fantasias simples 120; detalhadas 350–500; radicais com efeito: Dinossauro 1200 (poeira), Fada 1500 (brilhos), Futurista 1800 (neon), Unicórnio 2000 (rastro arco-íris).
- **Cenários** (`config/scenarios.py`): 31 no total. Só o `bg` é de graça. Os 10 outros fundos originais custam 150–400 (noite e entardecer mais caros); os 20 novos custam 600, 900 ou 1300. Cada um tem um período, que decide a cor dos canos e dos pássaros quando ele estiver na tela. O clássico não usa este catálogo.
- **Coleção de cenários** (`ctx.scenarios`): modo `fixo` (um cenário) ou `aleatorio` (playlist de até 15). Cenário comprado entra na playlist se houver vaga. A playlist nunca fica vazia; dados estragados no save são consertados na leitura.

## Artes novas (skins e cenários)

As folhas ficam em `artes/` (`skins.png`, `times.png`, `cenarios.png`). O importador recorta cada personagem, tira o fundo (o que encosta na borda e os bolsões fechados da mesma cor), reduz para a grade de pixels do jogo (36 px de largura, 24 cores) e amplia 2x sem borrar; todos da mesma folha na mesma escala, alinhados pelo corpo. Cenários viram faixas de horizonte de 575 px; no jogo, `montar_retrato` apoia a faixa no chão e estende o céu com as cores do topo dela.

Passo a passo completo: [`docs/como_adicionar_artes.md`](como_adicionar_artes.md). Resumo: ponha a folha em `artes/`, acrescente os nomes na tabela do importador (esquerda -> direita, cima -> baixo) e rode `python tools/importar_artes.py --previa previa.png` (precisa de `pip install -r requirements-dev.txt`). O relatório avisa tamanhos fora do padrão; `tests/test_assets.py` confere que tudo carrega. Personagens de terceiros (Link, Cavaleiro, Super Herói, Herói Vermelho) ficam de fora: na tabela, a posição deles é `None`.

## Cenários nas fases

Modo Livre, mapas e jornada usam os cenários do jogador no Flappy; o clássico continua com o ciclo de fundos do original (não herda o mixin, e o golden master confere).

- `SessaoComCenarios` (mixin, antes de `SessaoComMoedas` nas sessões novas) troca só três coisas: o fundo (`desenhar_fundo`), o rótulo do topo (`rotulo_tema`) e o `tema`/`familia`, que decidem a cor dos canos e do pássaro pelo período do cenário. O tempo, a física e os sorteios dos canos são os do original; teste: a mesma partida com o ciclo original e com 15 cenários sorteados tem física idêntica por 1.500 quadros.
- `DiretorCenarios`: no fixo, mostra um; no aleatório, troca a cada 20 s de jogo (os mesmos `TEMPO_TEMA` do original), nunca repete o anterior, dissolve em ~1 s (sem efeitos visuais, troca seca) e já monta o próximo antes da hora. Usa o próprio `random.Random`.
- `GerenciadorCenarios` (`ctx.resources.cenarios`): monta cada fundo sob demanda (~5 ms) e guarda só 3 (atual, anterior e próximo), seja qual for o tamanho da playlist.
- As cenas chamam `preparar_cenarios` em `preparar_recompensas` (`scenes/game_scene.py`), com `ctx.scenarios.ativos()`.
- **Galaga ("Decolagem")**: o horizonte do cenário fica embaixo e se dissolve no espaço original; a formação continua voando no espaço puro. No chefão, o mundo escurece mais em 1 s. **Donkey ("Selva sobre o seu mundo")**: o cenário substitui o céu, tingido de selva à noite, atrás das duas camadas de palmeiras; rola a 0,05 (palmeiras a 0,15 e 0,35), espelhado para não ter emenda.
- **Leitura garantida (exposição automática)**: cada cenário escurece só o necessário para a nave (faixa da nave) e as bananas (área de jogo do Donkey) terem contraste de pelo menos 3:1 com o fundo (`CONTRASTE_MINIMO`, o mínimo das diretrizes de acessibilidade para elementos gráficos). `tests/test_scenery.py` mede isso nos 31 cenários; cenário novo que não passar é escurecido sozinho.
- As versões das fases são montadas uma vez (~28 ms), durante o alerta de 5 s que antecede a fase, e só as da fase da vez ficam na memória. Sem cenário (clássico), `FaseGalaga.desenhar_fundo` e `FaseDonkey.desenhar_fundo` desenham exatamente o original.

## Modo Estilingue

Inspirado nos jogos de arremesso com física. Os insetos da Esquadrilha Galaga (o Rei-Inseto em miniatura) roubaram os ovos e se escondem em fortalezas; o jogador lança o próprio pássaro (a skin equipada) com o estilingue. É um mapa de 25 casas como os outros: a sessão `EstilingueSession` cumpre o mesmo contrato da `LevelScene` (atualizar, desenhar, tratar_evento, resultado, estrelas, moedas), então abertura, estrelas, moedas, pausa e progresso vêm de graça.

- **Física à parte:** usa a biblioteca **pymunk** (corpos rígidos 2D) só neste modo; a física original do Flappy/Galaga/Donkey não é tocada. Passos fixos (3 por quadro, 90 Hz), então a mesma jogada dá sempre o mesmo resultado; nada usa o `random` do jogo.
- **Dano:** cada batida gera um impulso; o que passa de `IMPULSO_MINIMO` vira dano nas duas peças. Gelo quebra com um toque médio, madeira com um bom acerto, pedra com ~3 batidas fortes ou explosões. Peça que sai do mundo conta como derrubada.
- **Elementos especiais:** blocos de gelo/madeira/pedra com rachaduras; **barris do Kong** que explodem em cadeia; três pássaros com habilidade (os nomes dos bônus): **Pena Dupla** (vira três), **Semente-Foguete** (dispara reto, 2,2x de dano em madeira), **Ovo Nova** (explode no clique ou 1,2 s depois de bater). Chefões: Rei-Inseto (5, 15), Kong (10, 20) e os dois juntos (25).
- **Estrelas:** 3 sobrando 2 pássaros, 2 sobrando 1, 1 usando todos.
- **Controles:** arrastar para trás e soltar (mouse) ou setas + ESPAÇO; no ar, clique/ESPAÇO usa a habilidade; roda do mouse ou A/D olham a fortaleza. O elástico solta o pássaro pela forquilha (a âncora), de onde a mira desenha o voo: o caminho mostrado é o caminho real (até a primeira batida).
- **Visual:** o fundo é o cenário que o jogador equipou (com paralaxe); câmera sobrevoa a fortaleza no começo e segue o pássaro.
- **Para mudar uma casa:** edite `CASAS_ESTILINGUE` em `config/estilingue.py` (módulos `torre`, `casinha`, `piramide`, `muro`, `fortaleza`, `barril`) e rode `python tools/playtest_estilingue.py --casas N` (o robô diz se dá para vencer) e `--humano 8` (a dificuldade com erro de mira humano). Os testes conferem que toda fortaleza fica de pé sozinha.

## Modo Combina 3

Jogo de combinar três com as peças do nosso universo: **pena, folha, ovo, moeda, semente e fruta** (os mesmos desenhos em pixel art dos bônus). Tabuleiro de 8 linhas por 7 colunas; trocar duas peças vizinhas só vale se formar uma sequência de 3 ou mais. É um mapa de 25 casas como os outros (`Combina3Session` cumpre o contrato da `LevelScene`).

- **Regras separadas do desenho:** `tabuleiro.py` não conhece o pygame. Cada passo de uma jogada é uma `Onda` (o que some, o que nasce, quais efeitos, quantos pontos); a sessão toca uma onda por vez com animação: `trocar` → `aplicar` → `cair` → `proxima_onda`, até acabar a cascata. O robô e os testes usam `jogar(a, b)`, que resolve tudo de uma vez. Cada tabuleiro tem o próprio sorteador (`semente`); nada usa o `random` do jogo.
- **Peças especiais** (com os nomes dos bônus):

| Como fazer | Nasce | Ao ser combinada |
|---|---|---|
| 4 em linha | **Pena-Raio** (setas) | limpa a linha ou a coluna inteira |
| L ou T (5 peças) | **Ovo Nova** (anel pulsando) | explode as 8 casas em volta (3x3) |
| 5 em linha | **Arco-íris** (esfera girando) | trocada com uma peça, limpa todas daquele tipo |

- **Combos** (trocar duas especiais entre si): Pena-Raio + Pena-Raio = cruz; Ovo + Ovo = 5x5; Pena-Raio + Ovo = 3 linhas e 3 colunas; Arco-íris + especial = todas as peças daquele tipo viram a especial e disparam; Arco-íris + Arco-íris = o tabuleiro inteiro. Especial atingida por outra dispara em cadeia.
- **Pontos:** 20 por peça, 30 por camada de gelo, 40 por golpe em caixa, 60/120/200 ao criar Pena-Raio/Ovo Nova/Arco-íris e +150 por combo de especiais; cada onda seguinte da mesma jogada multiplica (x2, x3...).
- **Obstáculos:** **gelo** (camadas sob a peça; perde uma quando a peça é limpa; o grosso tem moldura dupla), **caixa** (ocupa a casa; quebra com limpeza ao lado ou efeito por cima) e **pedra** (fixa). As peças caem por trechos da coluna: param em cima de caixa e pedra, e peças novas entram no topo de cada trecho.
- **Sem jogadas?** O tabuleiro embaralha as mesmas peças até existir uma troca válida. Parado por 5 s, o jogo mostra uma dica.
- **Controles:** clicar em duas vizinhas ou arrastar (mouse); setas movem o cursor, ESPAÇO segura a peça e a seta seguinte troca.
- **Objetivos (Fase 17):** cada casa tem um ou mais, todos obrigatórios: **pontos**, **coletar** peças de um tipo, quebrar todo o **gelo**, quebrar todas as **caixas** ou derrotar o **chefão**. O painel de cima mostra cada objetivo com ícone e "feito/alvo" (fica verde com um visto quando cumprido); a casa termina assim que o último é cumprido. Troca que não combina não gasta jogada.
- **Chefões (casas 5, 10, 15, 20 e 25):** Rei-Inseto, Kong e os dois juntos, com barra de vida no painel. Cada peça limpa tira 1 de vida (gelo e caixas também) e cada efeito disparado tira 3 a mais (`dano_da_onda`: um raio, uma explosão; o combo Pena-Raio + Ovo Nova conta 6 raios, +18, e Ovo + Ovo conta uma explosão grande, +3). A cada N jogadas o chefão ataca (o painel avisa "ATACA EM N JOGADAS"): o Rei-Inseto prende peças em **casulos** (1 golpe) e o Kong arremessa **barris** (2 golpes); os projéteis voam do painel até as casas. Com metade da vida, fica **BRAVO** e atinge uma casa a mais. Nunca mais de 12 caixas no tabuleiro.
- **Regras x tela:** `partida.py` tem as regras da casa (objetivos, dano, ataques) sem pygame; a sessão anima as etapas e o robô usa `Partida.jogar`. Um teste confere que os dois caminhos dão o mesmo tabuleiro.
- **Estrelas e moedas:** estrelas pelas jogadas que sobram (3 com 30% ou mais, 2 com 12% ou mais). Moedas (Fase 18): 2 por especial criada, 1 por jogada que sobrou, 10 pela vitória e 15 a mais nas casas de chefão, além do bônus de estrelas do mapa.
- **Para mudar uma casa:** edite `CASAS_COMBINA3` em `config/combina3.py`: o tabuleiro é desenhado em texto (`.` comum, `#` pedra, `c`/`C` caixa de 1/2 golpes, `g`/`G` gelo de 1/2 camadas) e os objetivos são tuplas como `(COLETAR, 'pena', 15)`. Depois rode `python tools/playtest_combina3.py --casas N`. Para abrir direto: `python src/main.py --casa combina3 N`.
- **Fora do Arcade:** o Combina 3 está no menu (`ORDEM_MAPAS`), mas não entra na jornada Arcade.

## Modo Apresentação (atalho secreto)

Para mostrar o jogo inteiro (numa aula, por exemplo) e, em seguida, como ele fica para um jogador qualquer.

- **Atalho:** **Ctrl + Shift + A** no menu principal liga; o mesmo atalho desliga. Ao ligar aparece "MODO APRESENTAÇÃO: TUDO LIBERADO" e um selo vermelho no topo do menu; ao desligar, "DE VOLTA AO SEU JOGO".
- **Ligado:** todas as casas de todos os mapas abertas (sem estrelas, para ainda mostrar a conquista; "Resetar progresso" recomeça a apresentação, não o jogo real), todas as skins e cenários, 99.999 moedas e os atalhos de teste no Clássico e no Modo Livre (G Galaga, K Donkey, F pássaros, B chefão, C bônus, T perto do gatilho, V Honra Máxima, 1 a 0 níveis).
- **O jogo de verdade fica intacto:** o save do jogador é gravado e guardado de lado; o perfil de apresentação vive só na memória (`save.gravavel = False`) e o ranking do clássico não é gravado. Desligar, ou simplesmente fechar o jogo, volta tudo como era. Só as configurações (música, efeitos) são as mesmas nos dois.
- **Código:** `systems/apresentacao.py` (`ligar`, `desligar`, `alternar`, `perfil`); `ProgressStore.liberada` e `salvar_ranking` consultam `apresentacao.ligado()`; o clássico usa os atalhos se `MODO_TESTE or apresentacao.ligado()` (a física não muda: o teste de referência continua igual).

## Sons e dicas dos modos novos (Fase 18)

- **Sons:** 15 efeitos de 8 bits sintetizados por `tools/gerar_sons.py` (só biblioteca padrão; semente fixa, então rodar de novo gera os mesmos arquivos). Estilingue: elástico ao lançar, habilidade, madeira, gelo e pedra quebrando (cada material soa diferente), explosão dos barris e do Ovo Nova, guincho do inseto. Combina 3: "pop" que sobe um tom a cada cascata (`estouro1` a `estouro4`), arpejo de peça especial nova, zap da Pena-Raio/Arco-íris, explosão do Ovo Nova, gelo, caixas, chefão ferido e o rosnado do ataque. Carregados em `Recursos.sons` (`SONS_MODOS_NOVOS`). Para mudar um som, edite a função dele no gerador e rode `python tools/gerar_sons.py`.
- **Dicas de tutorial:** um balão "DICA" aparece na primeira vez que o jogador encontra cada coisa: mirar, cada pássaro especial, barris e chefão no Estilingue; trocar, coletar, gelo, caixas, chefão, cada peça especial e o combo de duas especiais no Combina 3. Uma por vez, por até 7 s (some antes se o jogador agir depois de 2,5 s). As já vistas ficam na seção `tutorial` do save; "Resetar progresso" (e o Modo Apresentação) mostram todas de novo. Textos em `config/tutorial.py`; a sessão só pede pelo nome (`guia.pedir('c3_gelo')`), e nome errado dá erro nos testes.

## Bônus com cara nova (modos novos)

O clássico mantém as cápsulas com letra. Nos modos novos, `SessaoComBonusNovos` entrega um `EstiloBonus` à Galaga e ao Donkey da vez (`fase.estilo_bonus`), e as fases chamam o estilo só para desenhar:

| Bônus (lógica) | Nome novo | Item | Efeito na tela |
|---|---|---|---|
| GEMEO | Pena Dupla | pena azul | o ala (nave da direita) fica azulado e solta penas |
| BOMBA | Ovo Nova | ovo rachado | dois anéis, clarão suave e casca voando |
| TURBO | Semente-Foguete | semente com foguete | rastro de fogo saindo das naves |
| BUMERANGUE | Cacho Bumerangue | cacho de bananas | o cacho gira e deixa um rastro amarelo |
| MOLA | Folha-Trampolim | folha | folha sob o pássaro e anel "BOING!" a cada pulo |

Os itens são pixel art desenhados por código (`DESENHOS`), do tamanho da área de coleta. Raio (`CapsulaBonus.RAIO`), durações (`TIPOS_BONUS`) e regras não mudam; os avisos e o HUD trocam os nomes na hora de mostrar (`renomear`), e a lógica guarda o texto original. As partículas usam o próprio sorteador e somem com os efeitos visuais desligados. Teste: a mesma partida na Galaga e no Donkey, com e sem o visual novo, tem física idêntica.

## Loja e Equipamentos

- **Loja** (`ShopScene(ctx, aba='skins'|'cenarios')`): abas com filtros (Clássicas, Fantasias, Times; Originais, Novos). A vitrine mostra a skin voando sobre o cenário: na aba Skins, a escolhida sobre o cenário em uso; na aba Cenários, o escolhido com a skin equipada. "Ver em" troca a prévia entre Flappy, Galaga e Donkey (as mesmas montagens do jogo). Teclas: setas, ENTER, TAB (aba), Q/E (filtro), V (vista), ESC.
- Comprar pede confirmação. Skin comprada é equipada. Cenário comprado entra na playlist e, no modo fixo, vira o fixo. Cenário que já é seu: no fixo, USAR; no aleatório, PÔR/TIRAR DA PLAYLIST.
- **Equipamentos** (menu principal e loja): FIXO ou ALEATÓRIO, cartões só dos cenários comprados (no aleatório, com caixinha e contador "N/15"), atalhos para a loja de cenários e para trocar a skin. Tudo vai para o save na hora.
- **Miniaturas**: recortes do horizonte (156x88) guardados à parte (`GerenciadorCenarios.miniatura`), sem tirar os fundos grandes da memória; montadas uma por quadro (`FilaMiniaturas`, `MINIATURAS_POR_QUADRO`) para a tela abrir sem engasgo. As prévias da vitrine guardam as 6 últimas.

## Pausa, configurações e música

- **Pausa** (`P`, `ESC` ou a janela perdendo o foco) só com a partida em andamento: no menu, no cadastro e no game over do clássico as teclas fazem o que faziam. A pausa é uma cena por cima; como só o topo é atualizado, a partida congela sozinha.
- **Configurações** abrem do menu principal e da pausa. Resetar apaga moedas, skins, cenários, estrelas e recordes do Modo Livre; mantém configurações e o ranking do clássico. O foco começa em CANCELAR.
- **Música:** `musica_menu.wav` (menus, mapas, loja) e `musica_jogo.wav` (casas e Modo Livre). O clássico não tem música, como o original. Para mudar as músicas, edite as tabelas em `tools/gerar_musica.py` e rode `python tools/gerar_musica.py`.
- **Transições:** ao trocar de tela, o último quadro se dissolve em ~0,2 s (`Motion.SCENE_FADE_MS`); sem efeitos visuais, a troca é seca.

## Cuidados com o pygame

Fontes (`ui/theme.py: Fonts`) e textos prontos (`ui/widgets.py`) ficam em cache e são esvaziados sozinhos no `pygame.quit()` (`pygame.register_quit`). Nunca guarde uma `Font` em variável global fora desse cache.

## Save (`data/save.json`)

```json
{ "version": 2,
  "settings":  {"music": true, "sfx": true, "visual_fx": true},
  "wallet":    {"coins": 0},
  "skins":     {"owned": ["classico", "azul"], "equipped": "azul"},
  "scenarios": {"owned": ["bg", "praia"], "mode": "aleatorio", "fixed": "bg", "playlist": ["bg", "praia"]},
  "progress":  {"flappy": {"estrelas": [3, 2, 0, ...]}},
  "records":   {"free_best_streak": 0},
  "tutorial":  {"vistas": ["c3_trocar", "est_mirar"]} }
```

Versão 2 (Fase 9): a migração 1 → 2 só acrescenta `scenarios` com o cenário básico; moedas, skins e estrelas ficam como estavam.

Mudou o formato? Aumente `VERSAO_ATUAL` e registre a migração em `MIGRACOES` (`save_manager.py`). Seções novas com valor padrão (como `records`) não precisam de migração: o save as completa sozinho.
