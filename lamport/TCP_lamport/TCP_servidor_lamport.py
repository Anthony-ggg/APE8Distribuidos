"""
FASE 4 - Relojes Lógicos de Lamport
Cliente TCP
Universidad Nacional de Loja - Sistemas Distribuidos

Ejecutar en PC2-PC5, ejemplo en PC2:
    python lamport_tcp_client.py

Modifica las variables PC_ID y SERVER_IP según el equipo donde ejecutes.
"""

import socket
import json
import time
import random
from datetime import datetime

# ─── Configuración — CAMBIAR SEGÚN EL EQUIPO ───────────────────────────────────
PC_ID     = "PC2"           # Cambiar a PC2, PC3, PC4 o PC5 según corresponda
SERVER_IP = "192.168.1.10"  # IP del servidor (PC1)
PORT      = 5001            # Puerto TCP (debe coincidir con el servidor)
NUM_MSGS  = 3               # La guía pide 3 mensajes por integrante
# ────────────────────────────────────────────────────────────────────────────────

lamport_clock = 0
log_entries   = []

# Mensajes de ejemplo para el "chat distribuido"
SAMPLE_MESSAGES = [
    "Hola desde {}! Iniciando sincronización.",
    "Evento de prueba número {} desde {}.",
    "Mensaje final de {}. Reloj lógico activo.",
    "Comprobando causalidad en el sistema distribuido.",
    "Sistemas Distribuidos - UNL 2026.",
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}"
    print(line)
    log_entries.append(line)

def increment_clock():
    """Evento de ENVÍO: incrementa antes de enviar."""
    global lamport_clock
    lamport_clock += 1
    return lamport_clock

def update_clock(received_clock):
    """
    Regla de Lamport al RECIBIR:
    clock = max(local, recibido) + 1
    """
    global lamport_clock
    lamport_clock = max(lamport_clock, received_clock) + 1
    return lamport_clock

def send_message(sock, text, msg_number):
    """Envía un mensaje con el reloj de Lamport actual y espera ACK."""
    global lamport_clock

    # Regla: incrementar ANTES de enviar
    send_clock = increment_clock()

    message = {
        "sender":        PC_ID,
        "lamport_clock": send_clock,
        "text":          text,
        "type":          "message",
        "msg_number":    msg_number
    }

    payload = json.dumps(message).encode('utf-8')

    log(f"  [ENVIANDO]  Msg #{msg_number} | L={send_clock} | '{text}'")

    t_send = time.time()
    sock.sendall(payload)

    # Esperar ACK del servidor
    data = sock.recv(4096)
    t_recv = time.time()

    if data:
        ack = json.loads(data.decode('utf-8'))
        ack_clock = ack.get("lamport_clock", 0)
        new_clock  = update_clock(ack_clock)
        rtt_ms = (t_recv - t_send) * 1000

        log(f"  [ACK RECIBIDO] De {ack.get('sender')} | "
            f"L_ack={ack_clock} → L_nuevo={new_clock} | "
            f"RTT={rtt_ms:.2f}ms")
    else:
        log(f"  [ADVERTENCIA] Sin respuesta para Msg #{msg_number}")

def save_log():
    filename = f"log_lamport_tcp_{PC_ID.lower()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"=== LOG CLIENTE TCP LAMPORT - {PC_ID} ===\n")
        f.write(f"Inicio: {datetime.now()}\n\n")
        for entry in log_entries:
            f.write(entry + "\n")
    print(f"\n[INFO] Log guardado en: {filename}")

def main():
    log(f"{'='*55}")
    log(f"  CLIENTE LAMPORT TCP - {PC_ID}")
    log(f"  Servidor destino: {SERVER_IP}:{PORT}")
    log(f"  Reloj lógico inicial: {lamport_clock}")
    log(f"{'='*55}\n")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, PORT))
        log(f"Conexión TCP establecida con {SERVER_IP}:{PORT}\n")

        # Enviar NUM_MSGS mensajes con pausa aleatoria entre ellos
        for i in range(1, NUM_MSGS + 1):
            text = random.choice(SAMPLE_MESSAGES).format(PC_ID, i)
            send_message(sock, text, i)

            if i < NUM_MSGS:
                delay = random.uniform(0.5, 1.5)
                log(f"  [PAUSA] Esperando {delay:.2f}s antes del siguiente mensaje...\n")
                time.sleep(delay)

        log(f"\n{'='*55}")
        log(f"  RESUMEN FINAL - {PC_ID}")
        log(f"  Mensajes enviados: {NUM_MSGS}")
        log(f"  Reloj lógico final: L={lamport_clock}")
        log(f"{'='*55}")

    except ConnectionRefusedError:
        log(f"[ERROR] No se pudo conectar a {SERVER_IP}:{PORT}")
        log("[ERROR] Verifique que el servidor esté ejecutándose.")
    except Exception as e:
        log(f"[ERROR] {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass
        save_log()

if __name__ == "__main__":
    main()