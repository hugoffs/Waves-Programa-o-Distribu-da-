# Coleta de IDs em Sistema Distribuído (Echo / Onda de Propagação)

Especificação em pseudocódigo de um algoritmo distribuído em que um nó **iniciador** dispara uma onda de mensagens pela rede e, ao final, coleta os **IDs de todos os nós**. A implementação está em [`Waves.py`](Waves.py), usando RabbitMQ (via `pika`) para a troca de mensagens entre os nós.

> Notação: `N(x)` é o conjunto de vizinhos do nó `x`, `id` é o identificador do nó e `origem` é o vizinho de quem a mensagem foi recebida.

---
### Pré-requisitos

- Python 3
- Biblioteca [`pika`](https://pypi.org/project/pika/): `pip install pika`
- Um servidor **RabbitMQ**

### Uso

```text
python3 Waves.py <id> [<vizinho1> <vizinho2> ...]
```

Cada nó é um processo separado, identificado por `<id>`, e cria uma fila no RabbitMQ com esse nome. Os vizinhos informados precisam ser **simétricos** (se `a` lista `b`, então `b` deve listar `a`), pois o algoritmo assume enlaces bidirecionais.

### Exemplo (5 nós)

Abra um terminal para cada nó e inicie **todos** antes do starter — se a fila de um nó ainda não existir, o RabbitMQ descarta as mensagens enviadas a ele.

```bash
python3 Waves.py a b d
python3 Waves.py b c d a
python3 Waves.py c e b d
python3 Waves.py d a b e c
python3 Waves.py e c d

python3 starter.py go a
```

Topologia resultante:

```mermaid
graph LR
    a --- b
    a --- d
    b --- c
    b --- d
    c --- d
    c --- e
    d --- e
```

### Disparando o iniciador

O nó se torna iniciador ao receber, na sua fila, uma mensagem sem prefixo de origem (ex.: `go`) ou com o prefixo `STARTER:` (ex.: `STARTER:go`). O script `starter.py` do professor **não faz parte deste repositório**; sem ele, envie a mensagem diretamente com `pika`:

```bash
python3 -c "import pika; c=pika.BlockingConnection(); c.channel().basic_publish(exchange='', routing_key='a', body='go'); c.close()"
```

Saída esperada no nó `a` (a ordem dos IDs pode variar):

```text
Aplicativo Terminado. IDs coletados: ['a', 'd', 'b', 'c', 'e']
Terminando
```

Cada nó encerra sozinho (`Terminando`) ao chegar no estado `OK`. Para rodar de novo, reinicie todos os nós.

### Formato das mensagens trocadas

Toda mensagem entre nós é enviada como `<id_origem>:<conteúdo>`:

| Corpo na fila | Significado |
|---------------|-------------|
| `go` ou `STARTER:go` | Dispara o nó como iniciador |
| `b:R` | `<R>` vindo do nó `b` |
| `c:I:c,e` | `<I:[c, e]>` vindo do nó `c` |


## Sumário

- [Rodar o código](#rodar-o-código)
- [Visão geral](#visão-geral)
- [Modelo](#modelo)
- [Mensagens](#mensagens)
- [Variáveis](#variáveis)
- [Algoritmo](#algoritmo)
  - [Estado INICIADOR](#estado-iniciador)
  - [Estado OCIOSO](#estado-ocioso)
  - [Estado AGUARDANDO_ID](#estado-aguardando_id)
- [Funcionamento passo a passo](#funcionamento-passo-a-passo)

---

## Visão geral

1. O iniciador envia `<R>` para todos os vizinhos.
2. Cada nó que recebe `<R>` pela primeira vez guarda a `origem` como `entrada` e repassa `<R>` aos demais vizinhos.
3. Quando um nó já recebeu uma mensagem de todos os seus vizinhos, ele envia de volta (para a `entrada`) uma mensagem `<I:info_acumulada>` com os IDs que reuniu.
4. Quando o iniciador recebe tudo, ele imprime os IDs coletados e termina.

---

## Modelo

```text
Estados    = { INICIADOR, OCIOSO, AGUARDANDO_ID, OK }
SINI       = { INICIADOR, OCIOSO }      // estados iniciais
SFIM       = { OK }                     // estado final
Restrições = R ∪ { TR, CN, BL, UI }
```

| Símbolo | Significado |
|---------|-------------|
| `SINI`  | Conjunto de estados iniciais possíveis de um nó |
| `SFIM`  | Conjunto de estados finais (terminação) |
| `R`     | Restrições básicas do modelo |
| `TR`    | Total Reliability — não há falhas de comunicação/nós |
| `CN`    | Connectivity — a rede é conexa |
| `BL`    | Bidirectional Links — os enlaces são bidirecionais |
| `UI`    | Unique Initiator — existe um único iniciador |

---

## Mensagens

| Mensagem | Descrição |
|----------|-----------|
| `<R>` | Mensagem de requisição/propagação da onda |
| `<I:dados>` | Mensagem de resposta carregando IDs (`dados`) coletados |

---

## Variáveis

| Variável | Descrição |
|----------|-----------|
| `estado` | Estado atual do nó |
| `iniciador` | `True` se o nó é o iniciador, `False` caso contrário |
| `entrada` | Vizinho de quem o nó recebeu `<R>` pela primeira vez |
| `contador` | Quantidade de mensagens recebidas até o momento |
| `info_acumulada` | Lista de IDs coletados (começa com o `id` do próprio nó) |

---

## Algoritmo

### Estado INICIADOR

```text
INICIADOR
  Espontaneamente
    iniciador = True
    estado = AGUARDANDO_ID
    contador = 0
    info_acumulada = [id]
    envia <R> a N(x)

    se contador == |N(x)|:     // sem vizinhos: termina na hora
      estado = OK
      imprime("Aplicativo Terminado. IDs coletados: ", info_acumulada)
    fimse
```

### Estado OCIOSO

```text
OCIOSO
  Recebendo <R> de origem
    iniciador = False
    estado = AGUARDANDO_ID
    entrada = origem
    contador = 1
    info_acumulada = [id]

    // Repassa a mensagem da origem para todos os vizinhos EXCETO a entrada
    vizinhos_restantes = N(x) - {origem}
    se vizinhos_restantes != { }:
      envia <R> a N(x) - { origem }
    fimse
```

### Estado AGUARDANDO_ID

```text
AGUARDANDO_ID
  Recebendo <R> ou <I:dados> de origem
    contador = contador + 1

    se mensagem for do tipo <I:dados>:
      adiciona dados recebidos a info_acumulada
    fimse

    se contador == |N(x)|:
      estado = OK
      se iniciador == True:
        imprime("Aplicativo Terminado. IDs coletados: ", info_acumulada)
      senao:
        envia <I:info_acumulada> a entrada
      fimse
    fimse
```

---

## Funcionamento passo a passo

```mermaid
sequenceDiagram
    participant A as A (iniciador)
    participant B
    participant C

    Note over A: AGUARDANDO_ID
    A->>B: #lt;R#gt;
    Note over B: OCIOSO → AGUARDANDO_ID<br/>entrada = A
    B->>C: #lt;R#gt;
    Note over C: OCIOSO, sem outros vizinhos<br/>entrada = B → OK
    C-->>B: #lt;I:[C]#gt;
    Note over B: acumula [B, C] → OK
    B-->>A: #lt;I:[B, C]#gt;
    Note over A: acumula [A, B, C] → OK<br/>imprime IDs coletados
```

Exemplo simplificado com uma rede em linha `A — B — C`:

1. **A** (iniciador) vai para `AGUARDANDO_ID` e envia `<R>` aos vizinhos.
2. **B** (`OCIOSO`) recebe `<R>`, define `entrada = A` e repassa `<R>` a **C**.
3. **C** não tem outros vizinhos além de B, então envia `<I:[C]>` de volta.
4. **B** acumula `[B, C]` e, ao receber de todos os vizinhos, envia `<I:[B, C]>` para **A**.
5. **A** junta tudo, vai para `OK` e imprime os IDs coletados.
