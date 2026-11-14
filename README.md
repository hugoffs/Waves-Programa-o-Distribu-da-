# T2 - Sistemas Distribuídos: Algoritmo do Eco (Waves)

Este repositório contém a especificação formal e a documentação do **Algoritmo do Eco** desenvolvido para a disciplina de Processamento Distribuído / Sistemas Distribuídos e Concorrentes (PD/SDC) da PUCPR, ministrada pelo Prof. Luiz Lima Jr.

---

## Especificação Formal

As definições formais dos estados, estados iniciais, finais e restrições do sistema distribuído seguem o modelo abaixo:

$$\mathcal{S} = \{\text{INICIADOR, OCIOSO, AGUARDANDO_ID, OK}\}$$
$$\mathcal{S}_{INI} = \{\text{INICIADOR, OCIOSO}\}$$
$$\mathcal{S}_{FIM} = \{\text{OK}\}$$
$$\text{Restrições} = \mathcal{R} \cup \{\text{TR, CN, BL, UI}\}$$

---

### 1. INICIADOR
**Espontaneamente**
```text
iniciador = True
estado = AGUARDANDO_ID
contador = 0
info_acumulada = [id]
envia <R> a N(x)
se contador == |N(x)|:
    estado = OK
    imprime("Aplicativo Terminado. IDs coletados: ", info_acumulada)
fimse
```

---

### 2. OCIOSO
**Recebendo `<R>` de `origem`**
```text
iniciador = False
estado = AGUARDANDO_ID
entrada = origem
contador = 1
info_acumulada = [id]

// Repassa a mensagem da origem para todos os vizinhos EXCETO a entrada
vizinhos_restantes = N(x) - {origem}
se vizinhos_restantes != \emptyset:
    envia <R> a N(x) - {origem}
fimse
```

---

### 3. AGUARDANDO_ID
**Recebendo `<R>` ou `<I:dados>` de `origem`**
```text
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

### 4. Procedimentos Auxiliares (Protótipo / Legado)

#### Procedimento `retornar()`
```text
msg = list(mgs)
msg >> "ok"
se vizinhos != None:
    vizinhos = vizinhos - origem
    mensagem = msg
fimsenão:
    estado = OK
    se origem == id:
        mensagem = mensagem + id
        print()
    senão:
        envia <mensagem> a {origem}
    fimse
fimse
```

#### Procedimento `visita()`
```text
se msg == None:
    vizinhos = N(x)
    envia <R> a N(x)
fimse
se msg == R:
    se origem_atual in vizinhos:
        vizinhos = vizinhos - {origem_atual}
        envia <R> a origem_atual
    fimse
se vizinhos == None:
    estado = OK
    envia <OK + Id> a origem
fimse
```
