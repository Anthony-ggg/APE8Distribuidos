"""
FASE 4 - Relojes Lógicos de Lamport
Servidor UDP
Universidad Nacional de Loja - Sistemas Distribuidos

Ejecutar en PC1 (192.168.1.10):
    python lamport_udp_server.py

Diferencia clave con TCP:
- UDP es sin conexión (connectionless): no hay handshake.
- Cada datagrama llega de forma independiente.
- Los paquetes pueden llegar desordenados o perderse (sin garantía).
- Esto hace MÁS interesante observar Lamport: el orden causal puede
  diferir del orden real de llegada, visible claramente en Wireshark.
"""

import socket
import json
import threading
import time
from datetime import datetime

# ─── Configuración ─────────────────────────────────────────────────────────────
HOST   = '0.0.0.0'
PORT   = 5002            # Puerto UDP (distinto al TCP para poder correr ambos)
PC_ID  = "PC1"
BUFFER = 4096
# ────────────────────────────────────────────────────────────────────────────────

lamport_clock = 0
clock_lock    = threading.Lock()
log_entries   = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}"
    print(line)
    log_entries.append(line)

def update_clock(received_clock):
    """Regla de Lamport al recibir: max(local, recibido) + 1"""
    global lamport_clock
    with clock_lock:
        lamport_clock = max(lamport_clock, received_clock) + 1
        return lamport_clock

def increment_clock():
    global lamport_clock
    with clock_lock:
        lamport_clock += 1
        return lamport_clock

def save_log():
    with open("log_lamport_udp_server.txt", "w", encoding="utf-8") as f:
        f.write(f"=== LOG SERVIDOR UDP LAMPORT - {PC_ID} ===\n")
        f.write(f"Inicio: {datetime.now()}\n\n")
        for entry in log_entries:
            f.write(entry + "\n")
    print(f"\n[INFO] Log guardado en: log_lamport_udp_server.txt")

def main():
    # SOCK_DGRAM = UDP
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind((HOST, PORT))

    log(f"{'='*55}")
    log(f"  SERVIDOR LAMPORT UDP - {PC_ID}")
    log(f"  Escuchando en {HOST}:{PORT} (UDP)")
    log(f"  Reloj lógico inicial: {lamport_clock}")
    log(f"  NOTA: UDP no garantiza orden ni entrega.")
    log(f"{'='*55}")
    log("Esperando datagramas... (Ctrl+C para detener)\n")

    msg_count = 0

    try:
        while True:
            # recvfrom devuelve (datos, (ip_origen, puerto_origen))
            data, client_addr = server_sock.recvfrom(BUFFER)
            client_ip = client_addr[0]

            try:
                message = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                log(f"  [ERROR] Datagrama inválido de {client_ip}")
                continue

            msg_count += 1
            sender_id    = message.get("sender", "?")
            sender_clock = message.get("lamport_clock", 0)
            text         = message.get("text", "")
            msg_number   = message.get("msg_number", "?")

            # ── Aplicar regla de Lamport ──────────────────────────────────────
            new_clock = update_clock(sender_clock)

            log(f"  [RECIBIDO #{msg_count}] {sender_id} → {PC_ID} | "
                f"L_recibido={sender_clock} | "
                f"L_local={new_clock} | "
                f"Msg#{msg_number}: '{text}'")

            # ── Enviar ACK UDP (sin conexión: usamos sendto) ──────────────────
            reply_clock = increment_clock()
            response = {
                "sender":        PC_ID,
                "lamport_clock": reply_clock,
                "text":          f"ACK UDP de {PC_ID}",
                "type":          "ack",
                "ack_for":       msg_number
            }

            # En UDP se envía directamente a la dirección del remitente
            server_sock.sendto(
                json.dumps(response).encode('utf-8'),
                client_addr
            )

            log(f"  [ENVIADO ACK #{msg_count}] {PC_ID} → {sender_id} | "
                f"L={reply_clock} | Puerto destino: {client_addr[1]}")

    except KeyboardInterrupt:
        log(f"\n[INFO] Servidor UDP detenido.")
        log(f"[INFO] Total mensajes procesados: {msg_count}")
        log(f"[INFO] Reloj lógico final: L={lamport_clock}")
    finally:
        save_log()
        server_sock.close()

if __name__ == "__main__":
    main()