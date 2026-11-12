# Roteiro da apresentação — 17/11/2026

Arquivo: `PPEM Python – Pedro-Ruan-Guilherme – Projeto 2 – 26.2 – Apresentação.pptx` (16 slides; cada slide tem as falas nas **anotações do orador**).

**Tempo total:** cerca de 17 minutos de slides e demonstração, mais as perguntas. Se o tempo for curto (10 a 12 min), pulem os slides 12 (robôs) e 14 (limitações) e encurtem a demonstração para os passos 1, 3 e 5.

## Quem fala o quê

| Slides | Quem | Assunto | Tempo |
|---|---|---|---|
| 1–4 | Pedro | Abertura, números, metas, modos de jogo | 5 min |
| 5–9 | Ruan | Estilingue, Combina 3, arquitetura, física | 9 min |
| 10–12 | Guilherme | Colisão e regras de fim, testes, robôs | 4 min |
| 13 | Pedro joga, Guilherme narra | Demonstração ao vivo | 4 min |
| 14–16 | Guilherme e Pedro | Limitações, créditos, encerramento | 2 min |

## Antes de começar (no computador da sala)

- [ ] Jogo aberto no **menu principal** (`python src/main.py` ou `FlappyBird.exe`), em janela, ao lado do PowerPoint.
- [ ] Modo Apresentação **desligado** no começo (sem o selo vermelho no topo do menu).
- [ ] Som do computador ligado e num volume baixo.
- [ ] PowerPoint aberto no slide 1, no modo de apresentação.
- [ ] **Plano B:** um vídeo curto (1 a 2 min) da demonstração gravado antes, para o caso de o computador da sala não rodar o jogo.

## Demonstração (slide 13)

1. **Menu principal (20 s):** mostrar os oito modos, a loja e os Equipamentos.
2. **Clássico (1 min):**
   - digitar um nome e jogar alguns canos;
   - bater de propósito para mostrar a vida a menos;
   - deixar acabar e mostrar o GAME OVER com medalha e ranking.
3. **Ctrl + Shift + A no menu (10 s):** aparece "MODO APRESENTAÇÃO: TUDO LIBERADO".
4. **Estilingue, casa 10 (1 min):**
   - arrastar o pássaro para trás e mostrar que a mira acompanha;
   - soltar;
   - com a Pena Dupla ou o Ovo Nova, clicar no ar para a habilidade;
   - mirar num barril para mostrar a explosão em cadeia.
5. **Combina 3, casa 15 (1 min):**
   - fazer uma combinação de 4 para criar uma Pena-Raio e usá-la;
   - jogar até o Rei-Inseto atacar (o painel avisa "ATACA NA PRÓXIMA!").
6. **Voltar ao menu e Ctrl + Shift + A de novo (10 s):** aparece "DE VOLTA AO SEU JOGO". Tudo volta como era, sem nada liberado.

Se algo travar, não insistam: voltem ao PowerPoint e sigam (ou passem o vídeo do plano B).

## Perguntas prováveis

**Por que a física do pássaro é por quadro e não por segundo?**
Porque é assim no jogo das aulas, e uma das metas era manter o Clássico idêntico. Gravidade e impulso são somados a cada quadro, calibrados a 30 quadros/s. As fases novas (Galaga e Estilingue) usam tempo real, em segundos.

**Como passar a gravidade para unidades por segundo?**
Multiplica pela taxa de quadros ao quadrado: 1,1 px/quadro² × 30² = 990 px/s².

**Por que o pulo calculado (29,1 px) é maior que o do jogo (25,2 px)?**
O jogo soma os deslocamentos quadro a quadro, e o primeiro quadro já aplica uma gravidade inteira. É o erro de discretização da integração de Euler.

**Para que serve a compensação do impulso?**
A altura do pulo é v²/2g. Se só a gravidade subisse com o nível, o pulo encolheria 38% e o jogo ficaria injusto. O impulso cresce junto (expoente 0,35), e o pulo perde só 15%.

**Como funciona a colisão?**
Em duas etapas. Primeiro, um teste rápido de retângulos. Se eles se cruzam, o jogo compara os pixels das máscaras dos sprites, para não colidir nos cantos transparentes.

**O que é o golden master?**
Gravamos partidas do jogo original. A cada mudança, o teste repete essas partidas com as mesmas entradas e compara cada quadro. Se a física ou a pontuação do Clássico mudar, o teste falha.

**Por que usar o pymunk no Estilingue?**
Pilhas de blocos caindo, rolando e batendo umas nas outras precisam de colisão entre corpos rígidos, atrito e impulso. Escrever isso do zero seria um projeto inteiro. O pymunk dá o impulso de cada batida, e o dano vem dele: 0,028 × impulso, acima de 260.

**O que vocês fizeram e o que a IA fez?**
Respondam com honestidade, como está nos créditos:
- as artes das skins e dos cenários foram geradas pelo ChatGPT;
- o Claude foi usado como assistente de programação, testes e documentação;
- o grupo definiu o que construir em cada fase, testou o jogo, decidiu os ajustes de dificuldade e revisou o resultado.

Antes da apresentação, cada integrante deve saber explicar com as próprias palavras pelo menos a física (slides 8 e 9), a colisão (slide 10) e a arquitetura (slide 7).
