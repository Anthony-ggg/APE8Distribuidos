#!/usr/bin/env python3
import socket
import threading
import json
import sys

# Vector estricto de 3 posiciones [PC1, PC2, PC3]
MAPA_PROCESOS = {"PC1": 0, "PC2": 1, "PC3": 2}
reloj_vector = [0, 0, 0]

# !!! CONFIGURACIÓN: Reemplaza con las IPs reales de tus 3 máquinas !!!
TABLA_RED = {
    "PC1": ("192.168.1.10", 8001),
    "PC2": ("192.168.1.11", 8002),
    "PC3": ("192.168.1.12", 8003)
}

MI_ID = "PC1"  # ID por defecto si no se pasa argumento
if '--id' in sys.argv:
    MI_ID = sys.argv[sys.argv.index('--id') + 1]

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
        for i in range(3):
            reloj_vector[i] = max(reloj_vector[i], vector_recibido[i])
        reloj_vector[MI_INDICE] += 1
        return list(reloj_vector)

def log_evento(tipo, descripcion, v_antes, v_despues):
    print(f"\n  {'─'*55}\n  EVENTO: {tipo} en {MI_ID}\n  Descripción: {descripcion}")
    print(f"  Vector ANTES:   {v_antes}\n  Vector DESPUÉS: {v_despues}\n  {'─'*55}", flush=True)

def escuchar_udp(sock):
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            paquete = json.loads(data.decode('utf-8'))
            v_antes = list(reloj_vector)
            v_nuevo = tick_recepcion(paquete["vector"])
            log_evento("RECEPCIÓN", f"Desde {paquete['origen']}: '{paquete['mensaje']}'", v_antes, v_nuevo)
        except: break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', MI_PUERTO))
    print(f"=== NODO UDP {MI_ID} LEVANTADO EN PUERTO {MI_PUERTO} ===")
    threading.Thread(target=escuchar_udp, args=(sock,), daemon=True).start()
    
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
                v_antes = list(reloj_vector)
                v_envio = tick_envio()
                paquete = {"origen": MI_ID, "vector": v_envio, "mensaje": cmd[2]}
                sock.sendto(json.dumps(paquete).encode('utf-8'), TABLA_RED[destino])
                log_evento("ENVÍO", f"Mensaje enviado a {destino}", v_antes, v_envio)
    finally: sock.close()

if __name__ == "__main__": main()