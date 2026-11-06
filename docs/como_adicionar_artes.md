# Como adicionar novas artes

Guia para colocar skins e cenários novos no jogo. Você só mexe em **tabelas**; o importador, os testes e a loja fazem o resto.

Antes de começar (uma vez só):

```
pip install -r requirements-dev.txt
```

(instala Pillow e numpy, que só o importador usa; o jogo continua precisando apenas do pygame)

---

## 1. Preparar a folha de arte

| | Skins / times | Cenários |
|---|---|---|
| Arquivo | `artes/skins.png` ou `artes/times.png` | `artes/cenarios.png` |
| Formato | PNG, personagens em grade | PNG, paisagens em grade |
| Fundo | uma cor lisa (o ciano das folhas atuais funciona bem) | divisórias **brancas** entre as paisagens |
| Rótulos | caixa azul com o nome embaixo (ou colado embaixo, como nos times) | não precisa |
| Personagem | pássaro de perfil, olhando para a **direita**, corpo inteiro visível | paisagem **deitada** (mais larga que alta), com o horizonte embaixo |

Dicas que evitam retrabalho:

- **Fundo diferente do personagem.** O importador apaga o fundo por cor. Um personagem azul-claro num fundo azul-claro perde pedaços (o relatório avisa quando a área visível fica estranha).
- **Mesmo tamanho de personagem na folha toda.** Todos da folha usam a mesma escala; um personagem desenhado bem menor fica menor no jogo.
- **Nada de personagens de outras marcas** (heróis, mascotes, logotipos de jogos). Na tabela, a posição deles fica como `None` e eles não entram.
- **Cenário:** o que importa fica na metade de baixo (é o que aparece no jogo, apoiado no chão). O céu de cima é estendido automaticamente.

## 2. Dar os nomes

Abra `tools/importar_artes.py` e acrescente os nomes na tabela certa, **na ordem da folha** (esquerda → direita, cima → baixo):

```python
NOMES_SKINS = [ ..., 'Mago', 'Ninja', ... ]      # None = pular essa peça
NOMES_TIMES = [ ..., 'Santos', 'Flamengo', ... ]  # viram ids "time_santos", "time_flamengo"
NOMES_CENARIOS = [ ..., 'Parque', 'Praia', ... ]
```

O número de nomes tem que bater com o número de peças da folha; se não bater, o importador para e diz quantas peças achou.

Se um cenário ficar com o período errado (o importador decide dia, tarde ou noite pelo brilho), corrija em `AJUSTE_PERIODO`.

## 3. Importar e conferir

```
python tools/importar_artes.py --previa previa.png
```

- Grava `assets/skins/<id>.png` e `assets/cenarios/<id>.png`.
- Mostra um **relatório** (tamanho, cores, área visível, período de cada cenário). Qualquer linha diferente de `ok` merece uma olhada.
- `previa.png` mostra todas as skins numeradas sobre o céu do jogo, ao lado do pássaro original, e cada cenário montado como tela de jogo, com canos e chão.

## 4. Pôr à venda

**Skins** — `src/flappy_arcade/config/skins.py`:

```python
_fantasia('mago', 'Mago', RARA, 450),                       # fantasia
_fantasia('dinossauro', 'Dinossauro', RADICAL, 1200, 'poeira'),  # com efeito
_time('santos', 'Santos'),                                   # time (200)
```

Faixas de preço (o teste confere): comuns 50–200, raras 250–500, radicais 1000+. Efeitos disponíveis: `brilho`, `fantasma`, `neon`, `arco_iris`, `rastro_arco_iris`, `poeira`.

**Cenários** — `src/flappy_arcade/config/scenarios.py`:

```python
_novo('praia', 'Praia', 600, DIA),
```

Novos custam 600, 900 ou 1300; o período (`DIA`, `TARDE`, `NOITE`) decide a cor dos canos e dos pássaros.

## 5. Rodar os testes

```
python -m pytest
```

Eles conferem, sozinhos:

- toda arte do catálogo existe e toda arte de `assets/` está no catálogo;
- cada skin cabe no lugar do pássaro (e a colisão continua a do pássaro original);
- cada cenário vira um fundo de tela e tem **contraste** suficiente na Galaga e no Donkey (cenário claro demais é escurecido automaticamente, então isso quase nunca falha);
- os preços estão nas faixas certas.

Depois, rode a verificação final (seção 6) e faça o commit.

## 6. Verificação final

```
python tools/verificar_jogo.py
```

Abre todas as telas sem janela (menu, mapas, casas, Modo Livre com Galaga e Donkey, loja, Equipamentos, configurações), confere as artes e roda os testes. Termina com **PRONTO PARA O COMMIT** ou com a lista do que corrigir.

---

## Onde cada coisa fica

```
artes/                       folhas originais (não vão no executável)
tools/importar_artes.py      tabelas de nomes + importador
tools/previa_artes.py        prévia de conferência
assets/skins/, assets/cenarios/   o que o jogo carrega
config/skins.py, config/scenarios.py   catálogo, preços, efeitos, períodos
gameplay/scenery.py          como o cenário vira fundo (Flappy, Galaga, Donkey)
```
