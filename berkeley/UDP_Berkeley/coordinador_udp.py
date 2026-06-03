#!/usr/bin/env python3
"""
=============================================================
ALGORITMO DE BERKELEY - COORDINADOR (UDP)
=============================================================
El coordinador de Berkeley:
  1. Envía "GET_TIME" por UDP a todos los nodos esclavos
  2. Espera y recibe los tiempos de los nodos
  3. Calcula el promedio de todos los tiempos (incluyendo el suyo)
  4. Calcula el offset (diferencia) y lo envía a cada nodo por UDP

PROTOCOLO UDP:
  Coordinador → Nodo: "GET_TIME"
  Nodo → Coordinador: timestamp (float en texto)
  Coordinador → Nodo: offset firmado ("+0.234" o "-0.121")

EJECUTAR:
    python3 coordinador_udp.py

WIRESHARK: Filtrar con:  udp.port == 6000
=============================================================
"""

import socket       # Sockets UDP
import time         # Timestamps reales
import os           # Para chequear permisos si se requiere

# ─────────────────────────────────────────────
#  CONFIGURACIÓN — ajusta según tu red LAN
# ─────────────────────────────────────────────
HOST_COORDINADOR = '0.0.0.0'   
PORT_COORDINADOR = 6000         

# Lista de nodos esclavos: (IP, Puerto)
NODOS = [
    ('192.168.1.11', 6001),
    ('192.168.1.12', 6002),
    ('192.168.1.13', 6003),
]

TIMEOUT = 0.5   # Reducido para no demorar cuando hay nodos apagados

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

def ejecutar_ronda_berkeley_udp():
    print("\n" + "─" * 60)
    print(f"  INICIANDO RONDA DE SINCRONIZACIÓN (UDP)")
    print(f"  Tiempo coordinador: {time.strftime('%H:%M:%S')}")
    print("─" * 60)

    # ── PASO 1: Obtener tiempo de todos los nodos (UDP) ──────
    print("\n[PASO 1] Solicitando tiempo a todos los nodos (Broadcast/Unicast UDP)...")

    t_coordinador = time.time()   # Tiempo del coordinador AHORA
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_COORDINADOR, PORT_COORDINADOR))
    sock.settimeout(TIMEOUT)

    # Enviar GET_TIME a todos
    for ip, puerto in NODOS:
        try:
            sock.sendto(b"GET_TIME", (ip, puerto))
            print(f"  [ENVIADO]    'GET_TIME' a {ip}:{puerto}")
        except Exception as e:
            print(f"  [ERROR]      No se pudo enviar a {ip}:{puerto} → {e}")

    resultados = {}  # addr -> timestamp
    
    # Recibir respuestas
    end_time = time.time() + TIMEOUT
    while time.time() < end_time and len(resultados) < len(NODOS):
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode('utf-8').strip()
            t_nodo = float(msg)
            resultados[addr] = t_nodo
            print(f"  [RECIBIDO]   Nodo {addr[0]}:{addr[1]} → T = {t_nodo:.6f} s  "
                  f"({time.strftime('%H:%M:%S', time.localtime(t_nodo))})")
        except socket.timeout:
            break
        except ValueError:
            print(f"  [ERROR]      Mensaje inválido recibido de {addr}")
        except Exception as e:
            print(f"  [ERROR]      Error al recibir: {e}")

    if not resultados:
        print("\n[ERROR] Ningún nodo respondió. Abortando ronda.")
        sock.close()
        return

    # ── PASO 2: Calcular el promedio de tiempos ──────────────────────
    print(f"\n[PASO 2] Calculando promedio de tiempos...")
    print(f"  T_coordinador = {t_coordinador:.6f} s")

    todos_los_tiempos = [t_coordinador]

    for addr, t_nodo in resultados.items():
        todos_los_tiempos.append(t_nodo)
        print(f"  T_nodo {addr[0]}:{addr[1]} = {t_nodo:.6f} s  "
              f"(diferencia: {(t_nodo - t_coordinador)*1000:+.1f} ms)")

    t_promedio = sum(todos_los_tiempos) / len(todos_los_tiempos)

    print(f"\n  Tiempos recopilados: {len(todos_los_tiempos)}")
    print(f"  T_promedio = {t_promedio:.6f} s  "
          f"({time.strftime('%H:%M:%S', time.localtime(t_promedio))})")

    # ── PASO 3: Calcular y enviar offsets ────────────────────────────
    print(f"\n[PASO 3] Calculando y enviando offsets a cada nodo...")

    offset_coordinador = t_promedio - t_coordinador
    print(f"  Coordinador debe ajustar: {offset_coordinador*1000:+.3f} ms")
    if offset_coordinador != 0:
        cambiar_hora_sistema(offset_coordinador)

    for addr, t_nodo in resultados.items():
        offset = t_promedio - t_nodo   # positivo → adelantar; negativo → atrasar

        # Enviar offset como texto: "+0.00123" o "-0.00456"
        mensaje_offset = f"{offset:+.6f}"
        try:
            sock.sendto(mensaje_offset.encode('utf-8'), addr)
            print(f"  → Nodo {addr[0]}:{addr[1]} | offset = {offset*1000:+.3f} ms | "
                  f"{'adelantar' if offset > 0 else 'atrasar'}")
        except Exception as e:
            print(f"  [ERROR]      Error al enviar offset a {addr}: {e}")

    print(f"\n[OK] Ronda completada. {len(resultados)}/{len(NODOS)} nodos sincronizados.")
    sock.close()

def main():
    print("=" * 60)
    print("  COORDINADOR - ALGORITMO DE BERKELEY (UDP)")
    print("=" * 60)
    print(f"  Hora inicial del coordinador: {time.strftime('%H:%M:%S')}")
    print(f"  Nodos configurados: {len(NODOS)}")
    for ip, p in NODOS:
        print(f"    • {ip}:{p}")
    print("=" * 60)
    print("\n[INFO] Ejecutando rondas de sincronización cada 3 segundos.")
    print("[INFO] Presiona Ctrl+C para detener.\n")

    try:
        while True:
            ejecutar_ronda_berkeley_udp()
            print("\n[ESPERA] Próxima ronda en 3 segundos...")
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n[INFO] Coordinador detenido.")

if __name__ == "__main__":
    main()
