"""
FASE 4 - Relojes Lógicos de Lamport
Servidor TCP
Universidad Nacional de Loja - Sistemas Distribuidos
 
Ejecutar en PC1 (192.168.1.10):
    python lamport_tcp_server.py
 
El servidor:
- Mantiene su propio reloj lógico de Lamport
- Acepta mensajes de múltiples clientes
- Aplica la regla: clock = max(local, recibido) + 1
- Registra todos los eventos con sus timestamps lógicos
"""
 
import socket
import threading
import json
import time
from datetime import datetime
 
# ─── Configuración ─────────────────────────────────────────────────────────────
HOST = '0.0.0.0'       # Escucha en todas las interfaces
PORT = 5001            # Puerto TCP para Lamport
PC_ID = "PC1"          # Identificador de este nodo
# ────────────────────────────────────────────────────────────────────────────────
 
lamport_clock = 0
clock_lock = threading.Lock()
log_entries = []
 
def log(msg):
    """Imprime con timestamp real y guarda en log."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}"
    print(line)
    log_entries.append(line)
 
def increment_clock():
    """Evento interno: incrementa el reloj lógico."""
    global lamport_clock
    with clock_lock:
        lamport_clock += 1
        return lamport_clock
 
def update_clock(received_clock):
    """
    Regla de Lamport al RECIBIR:
    clock = max(local, recibido) + 1
    """
    global lamport_clock
    with clock_lock:
        lamport_clock = max(lamport_clock, received_clock) + 1
        return lamport_clock
 
def handle_client(conn, addr):
    """Maneja la conexión de un cliente en un hilo separado."""
    client_ip = addr[0]
    log(f"Nueva conexión TCP desde {client_ip}")
 
    try:
        while True:
            # Recibir datos (hasta 4096 bytes)
            data = conn.recv(4096)
            if not data:
                break
 
            # Decodificar mensaje JSON
            try:
                message = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                log(f"  [ERROR] Mensaje inválido de {client_ip}")
                continue
 
            sender_id    = message.get("sender", "Desconocido")
            sender_clock = message.get("lamport_clock", 0)
            text         = message.get("text", "")
            msg_type     = message.get("type", "message")
 
            # ── Aplicar regla de Lamport ──────────────────────────────────────
            new_clock = update_clock(sender_clock)
            log(f"  [RECIBIDO] {sender_id} → {PC_ID} | "
                f"L_recibido={sender_clock} | "
                f"L_local={new_clock} | "
                f"Texto='{text}'")
 
            # ── Preparar y enviar respuesta ───────────────────────────────────
            if msg_type == "message":
                # Incrementar antes de enviar la respuesta
                reply_clock = increment_clock()
                response = {
                    "sender": PC_ID,
                    "lamport_clock": reply_clock,
                    "text": f"ACK de {PC_ID}",
                    "type": "ack"
                }
                conn.sendall(json.dumps(response).encode('utf-8'))
                log(f"  [ENVIADO]  {PC_ID} → {sender_id} | "
                    f"L={reply_clock} | ACK enviado")
 
    except ConnectionResetError:
        log(f"  [INFO] Cliente {client_ip} desconectado abruptamente")
    except Exception as e:
        log(f"  [ERROR] {e}")
    finally:
        conn.close()
        log(f"Conexión cerrada con {client_ip}")
 
def save_log():
    """Guarda el log al finalizar."""
    with open("log_lamport_tcp_server.txt", "w", encoding="utf-8") as f:
        f.write(f"=== LOG SERVIDOR TCP LAMPORT - {PC_ID} ===\n")
        f.write(f"Inicio: {datetime.now()}\n\n")
        for entry in log_entries:
            f.write(entry + "\n")
    print("\n[INFO] Log guardado en: log_lamport_tcp_server.txt")
 
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
 
    log(f"{'='*55}")
    log(f"  SERVIDOR LAMPORT TCP - {PC_ID}")
    log(f"  Escuchando en {HOST}:{PORT}")
    log(f"  Reloj lógico inicial: {lamport_clock}")
    log(f"{'='*55}")
    log("Esperando clientes... (Ctrl+C para detener)\n")
 
    try:
        while True:
            conn, addr = server_socket.accept()
            # Cada cliente en su propio hilo
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        log(f"\n[INFO] Servidor detenido. Reloj final: L={lamport_clock}")
    finally:
        save_log()
        server_socket.close()
 
if __name__ == "__main__":
    main()