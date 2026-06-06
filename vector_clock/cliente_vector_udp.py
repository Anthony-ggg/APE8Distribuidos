#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - P2P UDP (5 POSICIONES)
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
    "PC1": ("192.168.1.10", 8001),
    "PC2": ("192.168.1.11", 8002),
    "PC3": ("192.168.1.12", 8003),
    # Las últimas dos PCs comentadas por si acaso, descomentar si se usan físicamente:
    # "PC4": ("192.168.1.13", 8004),
    # "PC5": ("192.168.1.14", 8005)
}

# Identidad por defecto si no se pasa argumento
MI_ID = "PC1"  
if '--id' in sys.argv:
    MI_ID = sys.argv[sys.argv.index('--id') + 1]

# Validar que el ID exista en nuestra configuración activa
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
        # Regla de Oro: Máximo componente a componente para las 5 posiciones
        for i in range(5):
            reloj_vector[i] = max(reloj_vector[i], vector_recibido[i])
        # Incremento posterior de la posición propia
        reloj_vector[MI_INDICE] += 1
        return list(reloj_vector)

def log_evento(tipo, descripcion, v_antes, v_despues):
    print(f"\n  {'─'*60}")
    print(f"  EVENTO: {tipo} en {MI_ID}")
    print(f"  Descripción: {descripcion}")
    print(f"  Vector ANTES:   {v_antes}")
    print(f"  Vector DESPUÉS: {v_despues}")
    print(f"  {'─'*60}", flush=True)

def escuchar_udp(sock):
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            paquete = json.loads(data.decode('utf-8'))
            v_antes = list(reloj_vector)
            v_nuevo = tick_recepcion(paquete["vector"])
            log_evento("RECEPCIÓN", f"Desde {paquete['origen']}: '{paquete['mensaje']}'", v_antes, v_nuevo)
        except:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', MI_PUERTO))
    
    print("=" * 60)
    print(f"  RELOJES DE VECTORES UDP — NODO {MI_ID}")
    print("=" * 60)
    print(f"  Escuchando en puerto: {MI_PUERTO}")
    print(f"  Vector inicial: {reloj_vector}")
    print("=" * 60)

    threading.Thread(target=escuchar_udp, args=(sock,), daemon=True).start()

    print("\n[COMANDOS]: local | enviar <PC> <mensaje> | salir\n")
    
    try:
        while True:
            cmd = input(f"{MI_ID} > ").strip().split(' ', 2)
            if not cmd or cmd[0] == '': continue
            
            comando = cmd[0].lower()
            if comando == 'salir':
                break
            elif comando == 'local':
                v_antes = list(reloj_vector)
                log_evento("LOCAL", "Evento interno", v_antes, tick_local())
            elif comando == 'enviar':
                if len(cmd) < 3:
                    print("[ERROR] Uso: enviar <PC_DESTINO> <MENSAJE>")
                    continue
                destino = cmd[1].upper()
                
                if destino not in TABLA_RED:
                    print(f"[ERROR] {destino} no está activo o está comentado.")
                    continue
                    
                v_antes = list(reloj_vector)
                v_envio = tick_envio()
                
                paquete = {"origen": MI_ID, "vector": v_envio, "mensaje": cmd[2]}
                sock.sendto(json.dumps(paquete).encode('utf-8'), TABLA_RED[destino])
                log_evento("ENVÍO", f"Mensaje enviado a {destino}", v_antes, v_envio)
    finally:
        sock.close()

if __name__ == "__main__":
    main()