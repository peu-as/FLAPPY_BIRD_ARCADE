# Créditos e bibliografia

**Flappy Arcade** — Projeto 2 de Programação para Engenharia Mecânica (PPEM), UFS/DMEC, 2026.2.

## Equipe e orientação

- **Desenvolvimento:** Pedro, Ruan e Guilherme.
- **Professor e autor do projeto didático de base:** Wilson Luciano (DMEC/UFS).

## Código

- **Base didática:** o Flappy Bird das aulas da disciplina (repositório [wilson-luciano/flappybird](https://github.com/wilson-luciano/flappybird), licença MIT, © 2026 Wilson Luciano), incluindo a física original do pássaro, dos canos e das fases.
- **Extensões do grupo:** organização em módulos, mapas, jornada Arcade, Modo Livre, loja e economia, save versionado, cenários, modos Estilingue e Combina 3, sons e músicas gerados por código, testes automáticos e ferramentas de verificação. Distribuídas sob a mesma licença MIT (veja [`LICENSE`](LICENSE)).

## Ferramentas de inteligência artificial

| Ferramenta | Uso |
|---|---|
| **ChatGPT** (OpenAI) | Geração das artes das skins (fantasias e times) e dos cenários novos (folhas em `artes/`, importadas para `assets/skins` e `assets/cenarios` por `tools/importar_artes.py`), da folha do personagem lendário Wilson Luciano (`artes/wilson_luciano.png`, importada por `tools/importar_personagem.py`) e da capa (`artes/capa.png`, que vira o ícone por `tools/gerar_icone.py`). |
| **Claude** (Anthropic) | Assistente de programação: apoio na implementação, nos testes automáticos, na calibração da dificuldade e na documentação. As decisões de projeto, os testes de jogo e a revisão foram feitos pelo grupo. |

## Recursos gráficos e sonoros

| Recurso | Origem |
|---|---|
| Sprites do pássaro, canos, chão, fundos, números e logotipo (`assets/imgs`) | Repositório do curso. Baseados no jogo *Flappy Bird* (Dong Nguyen / .GEARS Studios, 2013); marca e personagem pertencem aos seus titulares. |
| Pássaros especiais da pasta `assets/imgs` (Blue, Bubble, Chuck, Doge, Fishy, Kirby e outros) | Repositório do curso (variações feitas por fãs). Aparecem como pássaros-obstáculo e inimigos da Galaga, como no jogo original das aulas. Alguns lembram personagens de terceiros (Kirby, da Nintendo/HAL Laboratory; Chuck, de *Angry Birds*, da Rovio); não foram usados em conteúdo novo (skins, modos novos). |
| Sons `wing`, `point`, `hit`, `die` e músicas `chiptune_begin`, `game_over` e `game_over_arcade` (`assets/audio`) | Repositório do curso. |
| Skin lendária Wilson Luciano (`assets/personagens/wilson`) | Gerada com o ChatGPT (OpenAI). Homenagem do grupo ao Prof. Wilson Luciano, professor da disciplina. Uso acadêmico, sem fins comerciais. |
| Ícone do jogo (`assets/icone`) | Recortes da capa gerada com o ChatGPT (OpenAI). |
| Skins de fantasias e de times (`assets/skins`) e cenários novos (`assets/cenarios`) | Gerados com o ChatGPT (OpenAI). As skins de times usam cores e símbolos inspirados em clubes de futebol; nomes, escudos e marcas pertencem aos clubes. Uso acadêmico, sem fins comerciais. |
| Kong, barris, cipós, bananas, chefão da Galaga, itens dos bônus, peças do Combina 3, casulos | Desenhados por código no próprio projeto (`gameplay/procedural.py`, `gameplay/bonus_visuals.py`, `gameplay/combina3/visual.py`). |
| Músicas de fundo `musica_menu` e `musica_jogo` | Compostas e sintetizadas por código no projeto (`tools/gerar_musica.py`). |
| Efeitos sonoros dos modos novos (`sfx_*.wav`) | Sintetizados por código no projeto (`tools/gerar_sons.py`). |
| Fonte dos textos | Fonte padrão do pygame (`freesansbold.ttf`, GNU FreeFont; GPL com exceção para fontes). |

## Jogos que inspiraram as mecânicas

Nenhum material desses jogos foi copiado: só as ideias de jogabilidade, recriadas com regras e artes próprias. Nomes e marcas pertencem aos seus titulares.

- *Flappy Bird* — Dong Nguyen / .GEARS Studios, 2013.
- *Galaga* — Namco, 1981.
- *Donkey Kong* — Nintendo, 1981.
- *Angry Birds* — Rovio Entertainment, 2009 (inspiração do modo Estilingue).
- *Candy Crush Saga* — King, 2012 (inspiração do modo Combina 3).

## Bibliotecas e ferramentas

| Software | Uso | Licença |
|---|---|---|
| Python 3.12 | linguagem | PSF License |
| pygame 2.6.1 | janela, desenho, sons, eventos | LGPL 2.1 |
| pymunk 7.3.1 (motor Munk2D, derivado do Chipmunk2D) | física 2D do Estilingue | MIT |
| pytest | testes automáticos | MIT |
| PyInstaller | executável para Windows | GPL 2 com exceção para o executável gerado |
| Pillow | importação das artes (só em `requirements-dev.txt`) | MIT-CMU (HPND) |
| Git e GitHub | versionamento | GPL 2 (Git) |

## Bibliografia

- LUCIANO, Wilson. *Flappy Bird com Python e Pygame*: aulas 00 a 05 e sprints do Projeto 2. Programação para Engenharia Mecânica, DMEC/UFS, 2026. Disponível em: https://github.com/wilson-luciano/flappybird.
- PYGAME COMMUNITY. *Pygame documentation*. Disponível em: https://www.pygame.org/docs/. Acesso em: nov. 2026.
- BLOMQVIST, Victor. *Pymunk documentation*. Disponível em: https://www.pymunk.org/. Acesso em: nov. 2026.
- PYTHON SOFTWARE FOUNDATION. *The Python Tutorial* e *The Python Standard Library* (versão 3.12). Disponível em: https://docs.python.org/3.12/. Acesso em: nov. 2026.
- PYTEST-DEV. *pytest documentation*. Disponível em: https://docs.pytest.org/. Acesso em: nov. 2026.
- PYINSTALLER DEVELOPMENT TEAM. *PyInstaller Manual*. Disponível em: https://pyinstaller.org/. Acesso em: nov. 2026.
- NYSTROM, Robert. *Game Programming Patterns*. Genever Benning, 2014. Disponível em: https://gameprogrammingpatterns.com/. (Padrões *Game Loop*, *State* e *Update Method*, usados no loop e na pilha de cenas.)
- FIEDLER, Glenn. *Fix Your Timestep!* Gaffer On Games, 2004. Disponível em: https://gafferongames.com/post/fix_your_timestep/. (Passo de tempo fixo na física.)
- HALLIDAY, David; RESNICK, Robert; WALKER, Jearl. *Fundamentos de Física*, v. 1: Mecânica. 10. ed. Rio de Janeiro: LTC, 2016. (Movimento com aceleração constante e lançamento oblíquo: queda do pássaro e trajetória do Estilingue.)
- GITHUB. *Choose a License: MIT License*. Disponível em: https://choosealicense.com/licenses/mit/. Acesso em: nov. 2026.
