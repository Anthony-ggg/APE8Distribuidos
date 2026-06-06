
#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - P2P TCP (5 POSICIONES)
=============================================================
 
CORRECCIONES APLICADAS:
  1. Validación estricta del argumento --id al iniciar (evita que todos
     arranquen como PC2 por defecto y pisen el mismo puerto).
  2. Un nodo NO puede enviarse un mensaje a sí mismo (se detecta y avisa).
  3. Manejo robusto de errores en el servidor TCP (acepta reconexiones
     sin romper el hilo principal).
  4. Timeout en la conexión de envío para no bloquear si el destino
     está caído.
  5. Confirmación visual del ID y puerto al arrancar para detectar
     configuraciones incorrectas rápidamente.
"""
 
import socket
import threading
import json
import sys
 
# ── Vector estricto de 5 posiciones [PC1, PC2, PC3, PC4, PC5] ──────────────
MAPA_PROCESOS = {
    "PC1": 0,
    "PC2": 1,
    "PC3": 2,
    "PC4": 3,
    "PC5": 4,
}
reloj_vector = [0, 0, 0, 0, 0]
 
# ── Tabla de red ─────────────────────────────────────────────────────────────
# Descomentar PC4/PC5 si se usan físicamente.
TABLA_RED = {
    "PC1": ("192.168.1.10", 9001),
    "PC2": ("192.168.1.11", 9002),
    "PC3": ("192.168.1.12", 9003),
    # "PC4": ("192.168.1.13", 9004),
    # "PC5": ("192.168.1.14", 9005),
}
 
# ── FIX 1: El --id es OBLIGATORIO; sin él el programa no arranca ─────────────
if '--id' not in sys.argv:
    print("[ERROR] Debes indicar tu identidad con: python script.py --id PC1")
    print("        Valores válidos:", list(TABLA_RED.keys()))
    sys.exit(1)
 
MI_ID = sys.argv[sys.argv.index('--id') + 1].upper()
 
if MI_ID not in TABLA_RED:
    print(f"[ERROR] El ID '{MI_ID}' no existe o está comentado en TABLA_RED.")
    print("        Valores válidos:", list(TABLA_RED.keys()))
    sys.exit(1)
 
MI_INDICE = MAPA_PROCESOS[MI_ID]
MI_IP, MI_PUERTO = TABLA_RED[MI_ID]
lock_reloj = threading.Lock()
 
 
# ── Operaciones del reloj ─────────────────────────────────────────────────────
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
 
 
# ── Log ───────────────────────────────────────────────────────────────────────
def log_evento(tipo, descripcion, v_antes, v_despues):
    print(f"\n  {'─'*60}")
    print(f"  EVENTO: {tipo} en {MI_ID}")
    print(f"  Descripción: {descripcion}")
    print(f"  Vector ANTES:   {v_antes}")
    print(f"  Vector DESPUÉS: {v_despues}")
    print(f"  {'─'*60}", flush=True)
 
 
# ── Servidor TCP ──────────────────────────────────────────────────────────────
def manejar_cliente_tcp(conn):
    try:
        # FIX 3: recibir en bucle por si el mensaje llega fragmentado
        fragmentos = []
        while True:
            parte = conn.recv(4096)
            if not parte:
                break
            fragmentos.append(parte)
        data = b"".join(fragmentos).decode('utf-8')
        if data:
            paquete = json.loads(data)
            v_antes = list(reloj_vector)
            v_nuevo = tick_recepcion(paquete["vector"])
            log_evento(
                "RECEPCIÓN",
                f"Desde {paquete['origen']} via TCP: '{paquete['mensaje']}'",
                v_antes,
                v_nuevo,
            )
    except Exception as e:
        print(f"[WARN] Error procesando mensaje entrante: {e}")
    finally:
        conn.close()
 
 
def servidor_tcp():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', MI_PUERTO))   # escucha en todas las interfaces
    srv.listen(10)
    print(f"  [TCP] Servidor escuchando en 0.0.0.0:{MI_PUERTO}")
    while True:
        try:
            conn, addr = srv.accept()
            threading.Thread(
                target=manejar_cliente_tcp, args=(conn,), daemon=True
            ).start()
        except Exception as e:
            print(f"[WARN] Error en accept: {e}")
 
 
# ── Envío TCP ─────────────────────────────────────────────────────────────────
def enviar_tcp(destino, mensaje_texto):
    # FIX 2: evitar enviarse a uno mismo
    if destino == MI_ID:
        print(f"[ERROR] No puedes enviarte un mensaje a ti mismo ({MI_ID}).")
        return
 
    v_antes = list(reloj_vector)
    v_envio = tick_envio()
    paquete = {"origen": MI_ID, "vector": v_envio, "mensaje": mensaje_texto}
 
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.settimeout(5)          # FIX 4: timeout de 5 s
        cliente.connect(TABLA_RED[destino])
        cliente.sendall(json.dumps(paquete).encode('utf-8'))
        cliente.shutdown(socket.SHUT_WR)   # señala fin de datos al receptor
        cliente.close()
        log_evento("ENVÍO", f"Mensaje enviado a {destino} (TCP)", v_antes, v_envio)
    except socket.timeout:
        print(f"[ERROR] Tiempo de espera agotado al conectar a {destino}.")
    except ConnectionRefusedError:
        print(f"[ERROR] {destino} rechazó la conexión. ¿Está corriendo el script en esa PC?")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a {destino}: {e}")
 
 
# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"  RELOJES DE VECTORES TCP — NODO {MI_ID}")
    print("=" * 60)
    print(f"  Mi IP configurada : {MI_IP}  |  Puerto: {MI_PUERTO}")
    print(f"  Mi índice en vector: {MI_INDICE}")
    print(f"  Vector inicial     : {reloj_vector}")
    print(f"  Nodos activos      : {list(TABLA_RED.keys())}")
    print("=" * 60)
 
    threading.Thread(target=servidor_tcp, daemon=True).start()
 
    print("\n[COMANDOS]: local | enviar <PC> <mensaje> | salir\n")
    try:
        while True:
            try:
                linea = input(f"{MI_ID} > ").strip()
            except EOFError:
                break
 
            if not linea:
                continue
 
            cmd = linea.split(' ', 2)
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
                    print(f"[ERROR] '{destino}' no está activo. Nodos disponibles: {list(TABLA_RED.keys())}")
                    continue
                enviar_tcp(destino, cmd[2])
 
            else:
                print(f"[ERROR] Comando desconocido: '{cmd[0]}'")
                print("        Comandos válidos: local | enviar <PC> <mensaje> | salir")
 
    except KeyboardInterrupt:
        pass
 
    print("\n[INFO] Nodo detenido.")
 
 
if __name__ == "__main__":
    main()
