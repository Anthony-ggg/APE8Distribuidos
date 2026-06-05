#!/usr/bin/env python3
"""
=============================================================
ALGORITMO DE BERKELEY - COORDINADOR (Maestro)
=============================================================
El coordinador de Berkeley:
  1. Solicita la hora a todos los nodos esclavos
  2. Calcula el promedio de todos los tiempos (incluyendo el suyo)
  3. Calcula el offset (diferencia) que cada nodo debe aplicar
  4. Envía cada offset al nodo correspondiente

PROTOCOLO TCP:
  Coordinador → Nodo: "GET_TIME"
  Nodo → Coordinador: timestamp (float en texto)
  Coordinador → Nodo: offset firmado ("+0.234" o "-0.121")

EJECUTAR:
    python3 coordinador_berkeley.py

WIRESHARK: Filtrar con:  tcp.port == 6000
=============================================================
"""

import socket       # Sockets TCP
import time         # Timestamps reales
import threading    # Para conectarse a varios nodos en paralelo
import os           # Para chequear permisos si se requiere

# ─────────────────────────────────────────────
#  CONFIGURACIÓN — ajusta según tu red LAN
# ─────────────────────────────────────────────
HOST_COORDINADOR = '192.168.1.10'   # Escuchar en IP del coordinador
PORT_COORDINADOR = 6000         # Puerto del coordinador

# Lista de nodos esclavos: (IP, Puerto)
# Apunta a tu máquina (192.168.1.11)
NODOS = [
    ('192.168.1.11', 6001),   # Nodo 1
    ('192.168.1.11', 6002),   # Nodo 2
    ('192.168.1.11', 6003),   # Nodo 3
]

TIMEOUT = 0.5   # Reducido para no demorar cuando hay nodos apagados

offset_acumulado = 0.0

def hora_local_ajustada():
    """Retorna el tiempo Unix ajustado con el offset acumulado."""
    return time.time() + offset_acumulado

def obtener_tiempo_nodo(ip, puerto, resultados, indice):
    """
    Se conecta a un nodo, solicita su tiempo y guarda el resultado.
    Se ejecuta en un hilo independiente por cada nodo.

    Args:
        ip, puerto: dirección del nodo
        resultados: lista compartida donde guardar (ip, puerto, timestamp)
        indice: posición en la lista de resultados
    """
    try:
        # Crear conexión TCP al nodo esclavo
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((ip, puerto))

        print(f"  [CONECTADO]  Nodo {ip}:{puerto}")

        # Enviar solicitud de tiempo
        sock.sendall("GET_TIME\n".encode('utf-8'))

        # Recibir timestamp del nodo (como texto con salto de línea)
        datos = sock.recv(1024).decode('utf-8').strip()
        t_nodo = float(datos)

        print(f"  [RECIBIDO]   Nodo {ip}:{puerto} → T = {t_nodo:.6f} s  "
              f"({time.strftime('%H:%M:%S', time.localtime(t_nodo))})")

        resultados[indice] = (ip, puerto, t_nodo, sock)   # Guardamos el socket para enviar offset después

    except socket.timeout:
        print(f"  [TIMEOUT]    Nodo {ip}:{puerto} no respondió.")
        resultados[indice] = None
    except ConnectionRefusedError:
        print(f"  [ERROR]      Nodo {ip}:{puerto} rechazó la conexión. ¿Está activo?")
        resultados[indice] = None
    except Exception as e:
        print(f"  [ERROR]      Nodo {ip}:{puerto} → {e}")
        resultados[indice] = None

def ejecutar_ronda_berkeley():
    """
    Ejecuta una ronda completa del algoritmo de Berkeley:
    solicitar tiempos → calcular promedio → enviar offsets.
    """
    print("\n" + "─" * 60)
    print(f"  INICIANDO RONDA DE SINCRONIZACIÓN")
    print(f"  Tiempo coordinador: {time.strftime('%H:%M:%S')}")
    print("─" * 60)

    # ── PASO 1: Obtener tiempo de todos los nodos (en paralelo) ──────
    print("\n[PASO 1] Solicitando tiempo a todos los nodos...")

    t_coordinador = hora_local_ajustada()   # Tiempo del coordinador AHORA
    resultados = [None] * len(NODOS)
    hilos = []

    for i, (ip, puerto) in enumerate(NODOS):
        hilo = threading.Thread(
            target=obtener_tiempo_nodo,
            args=(ip, puerto, resultados, i)
        )
        hilos.append(hilo)
        hilo.start()

    # Esperar a que todos los hilos terminen
    for hilo in hilos:
        hilo.join()

    # Filtrar nodos que respondieron correctamente
    nodos_activos = [r for r in resultados if r is not None]

    if not nodos_activos:
        print("\n[ERROR] Ningún nodo respondió. Abortando ronda.")
        return

    # ── PASO 2: Calcular el promedio de tiempos ──────────────────────
    print(f"\n[PASO 2] Calculando promedio de tiempos...")
    print(f"  T_coordinador = {t_coordinador:.6f} s")

    todos_los_tiempos = [t_coordinador]   # Incluir el tiempo del coordinador

    for ip, puerto, t_nodo, _ in nodos_activos:
        todos_los_tiempos.append(t_nodo)
        print(f"  T_nodo {ip}:{puerto} = {t_nodo:.6f} s  "
              f"(diferencia: {(t_nodo - t_coordinador)*1000:+.1f} ms)")

    t_promedio = sum(todos_los_tiempos) / len(todos_los_tiempos)

    print(f"\n  Tiempos recopilados: {len(todos_los_tiempos)}")
    print(f"  T_promedio = {t_promedio:.6f} s  "
          f"({time.strftime('%H:%M:%S', time.localtime(t_promedio))})")

    # ── PASO 3: Calcular y enviar offsets ────────────────────────────
    print(f"\n[PASO 3] Calculando y enviando offsets a cada nodo...")

    global offset_acumulado
    offset_coordinador = t_promedio - t_coordinador
    print(f"  Coordinador debe ajustar: {offset_coordinador*1000:+.3f} ms")
    if offset_coordinador != 0:
        offset_acumulado += offset_coordinador

    for ip, puerto, t_nodo, sock in nodos_activos:
        offset = t_promedio - t_nodo   # positivo → adelantar; negativo → atrasar

        # Enviar offset como texto: "+0.00123" o "-0.00456"
        mensaje_offset = f"{offset:+.6f}\n"
        sock.sendall(mensaje_offset.encode('utf-8'))
        sock.close()

        print(f"  → Nodo {ip}:{puerto} | offset = {offset*1000:+.3f} ms | "
              f"{'adelantar' if offset > 0 else 'atrasar'}")

    print(f"\n[OK] Ronda completada. {len(nodos_activos)}/{len(NODOS)} nodos sincronizados.")

def main():
    print("=" * 60)
    print("  COORDINADOR - ALGORITMO DE BERKELEY")
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
            ejecutar_ronda_berkeley()
            print("\n[ESPERA] Próxima ronda en 3 segundos...")
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n[INFO] Coordinador detenido.")

if __name__ == "__main__":
    main()
