#!/usr/bin/env python3

# Componentes Basico
# PD/SDC - PUCPR
# Prof. Luiz Lima Jr.

from pika import BlockingConnection
from sys import argv
from enum import Enum

if len(argv) < 2:
    print(f"USO: {argv[0]} <id> [<v1> <v2> ...]")
    exit(1)

""" Informações globais"""
idx = argv[1]
Nx = argv[2:]
mesnagem_acumulado = []

Estado = Enum("Estado", "INICIADOR OCIOSO AQUARDANDO_ID OK  ")

estado = Estado.OCIOSO

print("meu id =", idx)
print("meus vizinhos =", Nx)

conexao = BlockingConnection()
canal = conexao.channel()

canal.queue_declare(queue=idx, durable=True, auto_delete=True)

# envia mensagem para destinos
def envia(msg, dests):
    for d in dests:
        canal.basic_publish(exchange="",
                            routing_key=d,
                            body=f"{idx}:{msg}")

def recebendo(msg, origem):
    global estado
    if estado == Estado.OCIOSO:
        print(f"{msg} recebida de {origem}")
        estado = Estado.OK
        Nxo = Nx[:]
        Nxo.remove(origem)
        envia(msg, Nxo)


def espontaneamente(msg):
    global estado
    global idx
    global mesagem_acumulado
    print("iniciador:", msg)
    estado = Estado.INICIADOR
    if estado == Estado.INICIADOR:
        estado = Estado.AQUARDANDO_ID
        cont  = 0
        mesagem_acumulado = [idx]
        envia(msg, Nx)
        if len(Nx) == 0:
            estado = Estado.OK
            print(f"Progama finalizado todos os id:: {mesagem_acumulado}")
    
    
def callback(canal, metodo,  props, msg):
    m = msg.decode().split(":")
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
