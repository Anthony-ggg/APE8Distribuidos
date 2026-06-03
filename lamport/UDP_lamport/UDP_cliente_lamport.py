"""
FASE 4 - Relojes Lógicos de Lamport
Cliente UDP
Universidad Nacional de Loja - Sistemas Distribuidos

Ejecutar en PC2-PC5, ejemplo en PC2:
    python lamport_udp_client.py

Modifica PC_ID y SERVER_IP según el equipo.

Diferencia clave con TCP:
- Cada mensaje es un datagrama independiente: no hay conexión establecida.
- El cliente usa un timeout para esperar el ACK (puede no llegar).
- Wireshark mostrará paquetes UDP individuales sin establecimiento de sesión.
"""

import socket
import json
import time
import random
from datetime import datetime

# ─── Configuración — CAMBIAR SEGÚN EL EQUIPO ───────────────────────────────────
PC_ID     = "PC2"           # Cambiar a PC2, PC3, PC4 o PC5
SERVER_IP = "192.168.1.10"  # IP de PC1
PORT      = 5002            # Puerto UDP del servidor
NUM_MSGS  = 3               # 3 mensajes por la guía
TIMEOUT   = 3.0             # Segundos a esperar el ACK (UDP puede perderse)
BUFFER    = 4096
# ────────────────────────────────────────────────────────────────────────────────

lamport_clock = 0
log_entries   = []

SAMPLE_MESSAGES = [
    "Datagrama UDP #{} de {}. Sin conexión establecida.",
    "Evento Lamport #{} vía UDP. ¿Llegará en orden?",
    "Mensaje #{} desde {}. Analizando causalidad UDP.",
    "Reloj lógico en acción — UDP no garantiza orden.",
    "Comprobando concurrencia en protocolo sin conexión.",
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}"
    print(line)
    log_entries.append(line)

def increment_clock():
    """Incrementa antes de enviar."""
    global lamport_clock
    lamport_clock += 1
    return lamport_clock

def update_clock(received_clock):
    """max(local, recibido) + 1"""
    global lamport_clock
    lamport_clock = max(lamport_clock, received_clock) + 1
    return lamport_clock

def send_message(sock, text, msg_number):
    """Envía datagrama UDP y espera ACK con timeout."""
    global lamport_clock

    send_clock = increment_clock()

    message = {
        "sender":        PC_ID,
        "lamport_clock": send_clock,
        "text":          text,
        "type":          "message",
        "msg_number":    msg_number
    }

    payload = json.dumps(message).encode('utf-8')

    log(f"  [ENVIANDO UDP] Msg #{msg_number} | L={send_clock} | '{text}'")
    log(f"               Destino: {SERVER_IP}:{PORT}")

    t_send = time.time()

    # sendto: envía el datagrama directamente (sin conexión)
    sock.sendto(payload, (SERVER_IP, PORT))

    # Esperar ACK con timeout
    try:
        sock.settimeout(TIMEOUT)
        data, server_addr = sock.recvfrom(BUFFER)
        t_recv = time.time()

        ack = json.loads(data.decode('utf-8'))
        ack_clock = ack.get("lamport_clock", 0)
        new_clock  = update_clock(ack_clock)
        rtt_ms    = (t_recv - t_send) * 1000

        log(f"  [ACK RECIBIDO] De {ack.get('sender')} | "
            f"L_ack={ack_clock} → L_nuevo={new_clock} | "
            f"RTT={rtt_ms:.2f}ms")

        # ── Análisis de causalidad para el log ───────────────────────────────
        if ack_clock > send_clock:
            log(f"  [CAUSALIDAD OK] El ACK (L={ack_clock}) > Envío (L={send_clock})")
        else:
            log(f"  [ADVERTENCIA] Posible desorden: ACK(L={ack_clock}) ≤ Envío(L={send_clock})")

    except socket.timeout:
        log(f"  [TIMEOUT] No se recibió ACK para Msg #{msg_number} "
            f"en {TIMEOUT}s (normal en UDP con pérdida de paquetes)")

def save_log():
    filename = f"log_lamport_udp_{PC_ID.lower()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"=== LOG CLIENTE UDP LAMPORT - {PC_ID} ===\n")
        f.write(f"Inicio: {datetime.now()}\n\n")
        for entry in log_entries:
            f.write(entry + "\n")
    print(f"\n[INFO] Log guardado en: {filename}")

def main():
    log(f"{'='*55}")
    log(f"  CLIENTE LAMPORT UDP - {PC_ID}")
    log(f"  Servidor destino: {SERVER_IP}:{PORT} (UDP)")
    log(f"  Reloj lógico inicial: {lamport_clock}")
    log(f"  NOTA: UDP no garantiza entrega ni orden.")
    log(f"{'='*55}\n")

    # SOCK_DGRAM = UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind local opcional pero útil para que el servidor sepa a quién responder
    sock.bind(('', 0))  # Puerto local asignado por el SO
    local_port = sock.getsockname()[1]
    log(f"Puerto local UDP asignado: {local_port}\n")

    try:
        for i in range(1, NUM_MSGS + 1):
            text = random.choice(SAMPLE_MESSAGES).format(i, PC_ID)
            send_message(sock, text, i)

            if i < NUM_MSGS:
                delay = random.uniform(0.3, 1.2)
                log(f"  [PAUSA] {delay:.2f}s...\n")
                time.sleep(delay)

        log(f"\n{'='*55}")
        log(f"  RESUMEN FINAL - {PC_ID} (UDP)")
        log(f"  Mensajes enviados: {NUM_MSGS}")
        log(f"  Reloj lógico final: L={lamport_clock}")
        log(f"{'='*55}")

    except Exception as e:
        log(f"[ERROR] {e}")
    finally:
        sock.close()
        save_log()

if __name__ == "__main__":
    main()