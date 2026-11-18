#!/usr/bin/env python3

# Componentes Basico - Algoritmo Eco (Waves)
# PD/SDC - PUCPR
# Prof. Luiz Lima Jr.
#Código base cedido pelo professor utilizado + implementação adicional da equipe.

from pika import BlockingConnection
from sys import argv
from enum import Enum

if len(argv) < 2:
    print(f"USO: {argv[0]} <id> [<v1> <v2> ...]")
    exit(1)

# Estado e variáveis globais do nó
idx = argv[1]
Nx = argv[2:]

Estado = Enum("Estado", "INICIADOR OCIOSO AGUARDANDO_ID OK")

estado = Estado.OCIOSO
iniciador = False
entrada = None
contador = 0
info_acumulada = []

print("meu id =", idx)
print("meus vizinhos =", Nx)

conexao = BlockingConnection()
canal = conexao.channel()

canal.queue_declare(queue=idx, durable=True, auto_delete=True)


# Envia mensagem para destinos prefixando o ID deste nó
def envia(msg, dests):
    for d in dests:
        canal.basic_publish(exchange="",
                            routing_key=d,
                            body=f"{idx}:{msg}")


# Trata requisições de onda (R) e respostas com IDs acumulados (I)
def recebendo(msg, origem):
    global estado, iniciador, entrada, contador, info_acumulada

    if estado == Estado.OCIOSO:
        if msg == "R":
            print(f"{msg} recebida de {origem}")
            iniciador = False
            estado = Estado.AGUARDANDO_ID
            entrada = origem
            contador = 1
            info_acumulada = [idx]
            Nxo = Nx[:]
            if origem in Nxo:
                Nxo.remove(origem)
            envia("R", Nxo)

    elif estado == Estado.AGUARDANDO_ID:
        if msg == "R" or msg.startswith("I:"):
            print(f"{msg} recebida de {origem}")
            contador += 1
            if msg.startswith("I:"):
                info_acumulada.extend(msg[2:].split(","))

    # Ao receber mensagens de todos os vizinhos, retorna o eco ou encerra
    if estado == Estado.AGUARDANDO_ID and contador == len(Nx):
        estado = Estado.OK
        if iniciador:
            print("Aplicativo Terminado. IDs coletados:", info_acumulada)
        else:
            envia(f"I:{','.join(info_acumulada)}", [entrada])
        canal.stop_consuming()


# Inicia a propagação da onda a partir do nó iniciador
def espontaneamente(msg):
    global estado, iniciador, contador, info_acumulada
    if estado != Estado.OCIOSO:
        return
    print("iniciador:", idx)
    iniciador = True
    estado = Estado.AGUARDANDO_ID
    contador = 0
    info_acumulada = [idx]
    envia("R", Nx)
    if contador == len(Nx):
        estado = Estado.OK
        print("Aplicativo Terminado. IDs coletados:", info_acumulada)
        canal.stop_consuming()


# Separa origem e carga útil sem truncar os dados de I:...
def callback(canal, metodo, props, msg):
    m = msg.decode().strip().split(":", 1)
    if len(m) < 2:
        origem = "STARTER"
        msg = m[0]
    else:
        origem = m[0]
        msg = m[1]
    if origem.upper() == "STARTER":
        espontaneamente(msg)
    else:
        recebendo(msg, origem)


canal.basic_consume(queue=idx,
                    on_message_callback=callback,
                    auto_ack=True)

try:
    print(f"{idx}: aguardando mensagens...")
    canal.start_consuming()
except KeyboardInterrupt:
    canal.stop_consuming()

conexao.close()
print("Terminando")