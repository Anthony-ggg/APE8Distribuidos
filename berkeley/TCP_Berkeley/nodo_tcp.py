#!/usr/bin/env python3
"""
=============================================================
ALGORITMO DE BERKELEY - NODO ESCLAVO
=============================================================
El nodo esclavo:
  1. Escucha conexiones TCP del coordinador
  2. Responde con su hora actual cuando recibe "GET_TIME"
  3. Recibe el offset del coordinador y ajusta su reloj lógico

EJECUTAR (en terminales separadas, cambiando el puerto):
    python3 nodo_berkeley.py --puerto 6001
    python3 nodo_berkeley.py --puerto 6002
    python3 nodo_berkeley.py --puerto 6003

    Si no pasas argumentos, usa el puerto por defecto (6001).

WIRESHARK: Filtrar con:  tcp.port == 6001
=============================================================
"""

import socket   # Sockets TCP
import time     # Timestamps reales
import sys      # Para leer argumentos de línea de comandos
import os       # Para chequear permisos si se requiere

# ─────────────────────────────────────────────
#  CONFIGURACIÓN — ajusta HOST/PORT según tu red
# ─────────────────────────────────────────────
HOST = '192.168.1.11'   # Escuchar en todas las interfaces

# Leer puerto desde argumento de línea de comandos, o usar 6001 por defecto
if '--puerto' in sys.argv:
    idx = sys.argv.index('--puerto')
    PORT = int(sys.argv[idx + 1])
else:
    PORT = 6001

# ─────────────────────────────────────────────
#  Reloj lógico del nodo (offset acumulado)
# ─────────────────────────────────────────────
# En un sistema real ajustarías el reloj del SO, pero para
# efectos académicos mantenemos un offset acumulado.
# Leer un desfase (en segundos) para simular que el reloj está mal
if '--desfase' in sys.argv:
    idx = sys.argv.index('--desfase')
    offset_acumulado = float(sys.argv[idx + 1])
else:
    offset_acumulado = 0.0   # segundos

def hora_local_ajustada():
    """Retorna el tiempo Unix ajustado con el offset acumulado."""
    return time.time() + offset_acumulado

def manejar_coordinador(conn, addr):
    """
    Maneja una conexión del coordinador:
    envía el tiempo local y espera recibir el offset.

    Args:
        conn: socket de la conexión establecida
        addr: (ip, puerto) del coordinador
    """
    global offset_acumulado

    try:
        print(f"\n[CONEXIÓN]  Coordinador conectado desde {addr}")

        # ── Recibir solicitud ──────────────────────────────────────
        datos = conn.recv(1024).decode('utf-8').strip()
        print(f"[RECIBIDO]  '{datos}' desde {addr}")

        if datos == "GET_TIME":
            # ── Enviar tiempo actual al coordinador ────────────────
            t_actual = hora_local_ajustada()
            respuesta = f"{t_actual:.6f}\n"
            conn.sendall(respuesta.encode('utf-8'))

            print(f"[ENVIADO]   Mi tiempo: {t_actual:.6f} s  "
                  f"({time.strftime('%H:%M:%S', time.localtime(t_actual))})")

            # ── Esperar el offset del coordinador ──────────────────
            datos_offset = conn.recv(1024).decode('utf-8').strip()
            offset_nuevo = float(datos_offset)

            t_antes = hora_local_ajustada()
            # Ajustar el reloj logico en lugar de cambiar la hora del sistema
            offset_acumulado += offset_nuevo
            t_despues = hora_local_ajustada()

            print(f"[OFFSET]    Recibido: {offset_nuevo*1000:+.3f} ms")
            print(f"[AJUSTE]    Antes:  {time.strftime('%H:%M:%S', time.localtime(t_antes))}")
            print(f"[AJUSTE]    Después:{time.strftime('%H:%M:%S', time.localtime(t_despues))}")
        else:
            print(f"[IGNORADO]  Mensaje desconocido: '{datos}'")

    except Exception as e:
        print(f"[ERROR]     {e}")
    finally:
        conn.close()   # Cerrar la conexión con el coordinador

def main():
    # Crear socket TCP del nodo
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Reusar el puerto si el proceso anterior terminó abruptamente
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))

    # Cola de conexiones pendientes (máx. 5)
    servidor.listen(5)

    print("=" * 60)
    print(f"  NODO ESCLAVO - ALGORITMO DE BERKELEY  (Puerto: {PORT})")
    print("=" * 60)
    print(f"  Escuchando en {HOST}:{PORT} (TCP)")
    print(f"  Hora local inicial: {time.strftime('%H:%M:%S')}")
    print("  Esperando al coordinador... (Ctrl+C para detener)")
    print("=" * 60)

    try:
        while True:
            # Aceptar conexión del coordinador (bloqueante)
            conn, addr = servidor.accept()

            # Manejar la solicitud en el hilo actual
            # (El coordinador se conecta de uno en uno por diseño)
            manejar_coordinador(conn, addr)

    except KeyboardInterrupt:
        print("\n\n[INFO] Nodo detenido por el usuario.")
    finally:
        servidor.close()
        print("[INFO] Socket cerrado correctamente.")

if __name__ == "__main__":
    main()
