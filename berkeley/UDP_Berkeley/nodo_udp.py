#!/usr/bin/env python3
"""
=============================================================
ALGORITMO DE BERKELEY - NODO ESCLAVO (UDP)
=============================================================
El nodo esclavo:
  1. Escucha paquetes UDP del coordinador
  2. Responde con su hora actual cuando recibe "GET_TIME"
  3. Recibe el offset del coordinador y ajusta su reloj lógico

EJECUTAR (en terminales separadas, cambiando el puerto):
    python3 nodo_udp.py --puerto 6001
    python3 nodo_udp.py --puerto 6002
    python3 nodo_udp.py --puerto 6003

    Si no pasas argumentos, usa el puerto por defecto (6001).

WIRESHARK: Filtrar con:  udp.port == 6001
=============================================================
"""

import socket   # Sockets UDP
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
if '--desfase' in sys.argv:
    idx = sys.argv.index('--desfase')
    offset_acumulado = float(sys.argv[idx + 1])
else:
    offset_acumulado = 0.0   # segundos

def hora_local_ajustada():
    """Retorna el tiempo Unix ajustado con el offset acumulado."""
    return time.time() + offset_acumulado

import subprocess
import datetime

def cambiar_hora_sistema(offset):
    """Intenta cambiar la hora real del Sistema Operativo usando date -s."""
    nuevo_tiempo_unix = time.time() + offset
    nuevo_tiempo_dt = datetime.datetime.fromtimestamp(nuevo_tiempo_unix)
    tiempo_formateado = nuevo_tiempo_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        print(f"  [SISTEMA] Aplicando nueva hora al SO: {tiempo_formateado} ...")
        subprocess.run(['sudo', 'date', '-s', tiempo_formateado], check=True)
        print("  [SISTEMA] ¡El reloj físico se ha sincronizado correctamente!")
    except Exception as e:
        print(f"  [SISTEMA] Error al cambiar la hora: {e}")

def main():
    global offset_acumulado
    
    # Crear socket UDP del nodo
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Reusar el puerto si es necesario
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))

    print("=" * 60)
    print(f"  NODO ESCLAVO - ALGORITMO DE BERKELEY (UDP)  (Puerto: {PORT})")
    print("=" * 60)
    print(f"  Escuchando en {HOST}:{PORT} (UDP)")
    print(f"  Hora local inicial: {time.strftime('%H:%M:%S')}")
    print("  Esperando mensajes del coordinador... (Ctrl+C para detener)")
    print("=" * 60)

    try:
        while True:
            # ── 1. Esperar mensaje del coordinador (GET_TIME) ─────────────
            # servidor.settimeout(None) # bloquea indefinidamente hasta recibir algo
            data, addr = servidor.recvfrom(1024)
            msg = data.decode('utf-8').strip()

            print(f"\n[MENSAJE]   Recibido '{msg}' desde {addr}")

            if msg == "GET_TIME":
                # ── 2. Enviar tiempo actual al coordinador ────────────────
                t_actual = time.time()
                respuesta = f"{t_actual:.6f}"
                servidor.sendto(respuesta.encode('utf-8'), addr)

                print(f"[ENVIADO]   Mi tiempo: {t_actual:.6f} s  "
                      f"({time.strftime('%H:%M:%S', time.localtime(t_actual))})")

                # ── 3. Esperar el offset del coordinador ──────────────────
                # Aquí asumimos que el coordinador responderá pronto. 
                # Ponemos un timeout por si el paquete se pierde en UDP.
                servidor.settimeout(5.0)
                try:
                    data_offset, addr_offset = servidor.recvfrom(1024)
                    # Verificar que viene del mismo coordinador
                    if addr_offset == addr:
                        msg_offset = data_offset.decode('utf-8').strip()
                        offset_nuevo = float(msg_offset)

                        t_antes = time.time()
                        # Intentar cambiar la hora del sistema operativo
                        cambiar_hora_sistema(offset_nuevo)
                        t_despues = time.time()

                        print(f"[OFFSET]    Recibido: {offset_nuevo*1000:+.3f} ms")
                        print(f"[AJUSTE]    Antes:  {time.strftime('%H:%M:%S', time.localtime(t_antes))}")
                        print(f"[AJUSTE]    Después:{time.strftime('%H:%M:%S', time.localtime(t_despues))}")
                    else:
                        print(f"[IGNORADO]  Mensaje de remitente inesperado ({addr_offset})")
                except socket.timeout:
                    print(f"[TIMEOUT]   No se recibió offset de {addr}. Se omitirá el ajuste.")
                except ValueError:
                    print(f"[ERROR]     Mensaje de offset inválido: '{msg_offset}'")
                finally:
                    # Restaurar modo bloqueante
                    servidor.settimeout(None)
            else:
                print(f"[IGNORADO]  Comando no soportado.")

    except KeyboardInterrupt:
        print("\n\n[INFO] Nodo detenido por el usuario.")
    finally:
        servidor.close()
        print("[INFO] Socket cerrado correctamente.")

if __name__ == "__main__":
    main()
