#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - P2P TCP (5 POSICIONES)
=============================================================
"""
import socket
import threading
import json
import sys

# Vector estricto de 5 posiciones [PC1, PC2, PC3, PC4, PC5]
MAPA_PROCESOS = {
    "PC1": 0, 
    "PC2": 1, 
    "PC3": 2,
    "PC4": 3, 
    "PC5": 4
}
reloj_vector = [0, 0, 0, 0, 0]

# TABLA DE RED CON LAS IPs ASIGNADAS (Secuenciales desde .10)
TABLA_RED = {
    "PC1": ("192.168.1.10", 9001),
    "PC2": ("192.168.1.11", 9002),
    "PC3": ("192.168.1.12", 9003),
    # Las últimas dos PCs comentadas por si acaso, descomentar si se usan físicamente:
    # "PC4": ("192.168.1.13", 9004),
    # "PC5": ("192.168.1.14", 9005)
}

MI_ID = "PC1"
if '--id' in sys.argv:
    MI_ID = sys.argv[sys.argv.index('--id') + 1]

if MI_ID not in TABLA_RED:
    print(f"[ERROR] El ID '{MI_ID}' está comentado o no existe en la TABLA_RED.")
    sys.exit(1)

MI_INDICE = MAPA_PROCESOS[MI_ID]
MI_PUERTO = TABLA_RED[MI_ID][1]
lock_reloj = threading.Lock()

def tick_local():
    global reloj_vector
    with lock_reloj:
        reloj_vector[MI_INDICE] += 1
        return list(reloj_vector)

def tick_envio():
    return tick_local()

def tick_recepcion(vector_recibido):
    global reloj_vector
    with lock_reloj:
        for i in range(5):
            reloj_vector[i] = max(reloj_vector[i], vector_recibido[i])
        reloj_vector[MI_INDICE] += 1
        return list(reloj_vector)

def log_evento(tipo, descripcion, v_antes, v_despues):
    print(f"\n  {'─'*60}")
    print(f"  EVENTO: {tipo} en {MI_ID}")
    print(f"  Descripción: {descripcion}")
    print(f"  Vector ANTES:   {v_antes}")
    print(f"  Vector DESPUÉS: {v_despues}")
    print(f"  {'─'*60}", flush=True)

def manejar_cliente_tcp(conn):
    try:
        data = conn.recv(1024).decode('utf-8')
        if data:
            paquete = json.loads(data)
            v_antes = list(reloj_vector)
            v_nuevo = tick_recepcion(paquete["vector"])
            log_evento("RECEPCIÓN", f"Desde {paquete['origen']} via TCP: '{paquete['mensaje']}'", v_antes, v_nuevo)
    except:
        pass
    finally:
        conn.close()

def servidor_tcp():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('', MI_PUERTO))
    servidor.listen(5)
    while True:
        try:
            conn, _ = servidor.accept()
            threading.Thread(target=manejar_cliente_tcp, args=(conn,), daemon=True).start()
        except:
            break

def enviar_tcp(destino, mensaje_texto):
    v_antes = list(reloj_vector)
    v_envio = tick_envio()
    paquete = {"origen": MI_ID, "vector": v_envio, "mensaje": mensaje_texto}
    
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect(TABLA_RED[destino])
        cliente.sendall(json.dumps(paquete).encode('utf-8'))
        cliente.close()
        log_evento("ENVÍO", f"Mensaje enviado a {destino} (TCP)", v_antes, v_envio)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a {destino}: {e}")

def main():
    print("=" * 60)
    print(f"  RELOJES DE VECTORES TCP — NODO {MI_ID}")
    print("=" * 60)
    print(f"  Escuchando en puerto: {MI_PUERTO}")
    print(f"  Vector inicial: {reloj_vector}")
    print("=" * 60)
    
    threading.Thread(target=servidor_tcp, daemon=True).start()
    
    print("\n[COMANDOS]: local | enviar <PC> <mensaje> | salir\n")
    try:
        while True:
            cmd = input(f"{MI_ID} > ").strip().split(' ', 2)
            if not cmd or cmd[0] == '': continue
            if cmd[0].lower() == 'salir': break
            elif cmd[0].lower() == 'local':
                v_antes = list(reloj_vector)
                log_evento("LOCAL", "Evento interno", v_antes, tick_local())
            elif cmd[0].lower() == 'enviar':
                if len(cmd) < 3: continue
                destino = cmd[1].upper()
                if destino not in TABLA_RED:
                    print(f"[ERROR] {destino} no está activo o está comentado.")
                    continue
                enviar_tcp(destino, cmd[2])
    except KeyboardInterrupt: 
        pass

if __name__ == "__main__": 
    main()