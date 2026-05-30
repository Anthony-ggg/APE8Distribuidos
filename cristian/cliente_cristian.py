#!/usr/bin/env python3
"""
=============================================================
ALGORITMO DE CRISTIAN - CLIENTE
=============================================================
El cliente envía una solicitud de tiempo al servidor,
mide el RTT (Round Trip Time) y ajusta su reloj local.

FÓRMULA DE CRISTIAN:
    RTT = T_recv_client - T_send_client
    Delay = RTT / 2   (asume red simétrica)
    T_ajustado = T_servidor + Delay

EJECUTAR:
    python3 cliente_cristian.py

    Para cambiar el servidor: edita SERVER_HOST abajo.
    Ejemplo LAN: SERVER_HOST = '192.168.1.10'

WIRESHARK: Filtrar con:  udp.port == 5000
=============================================================
"""

import socket   # Para socket UDP
import time     # Para timestamps reales
import struct   # Para desempaquetar el tiempo recibido

# ─────────────────────────────────────────────
#  CONFIGURACIÓN — cambia SERVER_HOST a la IP
#  del servidor en tu red LAN
# ─────────────────────────────────────────────
SERVER_HOST = '127.0.0.1'   # IP del servidor (localhost para pruebas locales)
SERVER_PORT = 5000           # Puerto UDP del servidor
TIMEOUT     = 5              # Segundos de espera máxima por respuesta
NUM_SINCRONIZACIONES = 5     # Cuántas veces sincronizar (para ver estadísticas)

def sincronizar_con_servidor():
    """
    Realiza una sincronización con el servidor de Cristian.
    Retorna (t_ajustado, rtt, delay) o None si hay error.
    """

    # Crear socket UDP para este cliente
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Tiempo máximo de espera por la respuesta del servidor
    cliente.settimeout(TIMEOUT)

    try:
        # ── PASO 1: Enviar solicitud de tiempo ──────────────────────
        # Registrar T1: momento ANTES de enviar (usado para calcular RTT)
        t1 = time.time()

        solicitud = "REQUEST_TIME".encode('utf-8')
        cliente.sendto(solicitud, (SERVER_HOST, SERVER_PORT))

        print(f"  [ENVIADO]   REQUEST_TIME → {SERVER_HOST}:{SERVER_PORT}")
        print(f"  [T1]        Tiempo de envío:     {t1:.6f} s  ({time.strftime('%H:%M:%S.') + f'{int((t1 % 1)*1000000):06d}'})")

        # ── PASO 2: Recibir respuesta del servidor ───────────────────
        datos, _ = cliente.recvfrom(1024)

        # Registrar T4: momento DESPUÉS de recibir la respuesta
        t4 = time.time()

        # Desempaquetar el timestamp del servidor (double 8 bytes)
        t_servidor = struct.unpack('!d', datos)[0]

        print(f"  [RECIBIDO]  Timestamp del servidor: {t_servidor:.6f} s")
        print(f"  [T4]        Tiempo de recepción:    {t4:.6f} s")

        # ── PASO 3: Calcular RTT y Delay ────────────────────────────
        rtt   = t4 - t1           # Round Trip Time total
        delay = rtt / 2.0         # Delay unidireccional (red simétrica)

        # ── PASO 4: Calcular hora ajustada ──────────────────────────
        # El tiempo del servidor llegó hace 'delay' segundos,
        # por eso sumamos el delay para compensar.
        t_ajustado = t_servidor + delay

        return t_ajustado, rtt, delay

    except socket.timeout:
        print("  [ERROR] Tiempo de espera agotado. ¿El servidor está activo?")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None
    finally:
        cliente.close()   # Siempre cerrar el socket

def main():
    print("=" * 60)
    print("  CLIENTE DE TIEMPO - ALGORITMO DE CRISTIAN")
    print("=" * 60)
    print(f"  Servidor objetivo: {SERVER_HOST}:{SERVER_PORT}")
    print(f"  Hora LOCAL antes de sync: {time.strftime('%H:%M:%S')}")
    print("=" * 60)

    rtts   = []   # Lista para calcular estadísticas al final
    delays = []

    for i in range(1, NUM_SINCRONIZACIONES + 1):
        print(f"\n── Sincronización #{i} ──────────────────────────────────")

        resultado = sincronizar_con_servidor()

        if resultado:
            t_ajustado, rtt, delay = resultado

            rtts.append(rtt)
            delays.append(delay)

            # ── Mostrar resultados detallados ──────────────────────
            print(f"\n  ┌─ RESULTADOS ─────────────────────────────────────┐")
            print(f"  │  RTT (ida+vuelta):    {rtt*1000:.3f} ms")
            print(f"  │  Delay (estimado):    {delay*1000:.3f} ms")
            print(f"  │  Hora SERVIDOR:       {time.strftime('%H:%M:%S', time.localtime(t_ajustado))}")
            print(f"  │  Hora AJUSTADA:       {t_ajustado:.6f} s (Unix)")
            print(f"  │  Diferencia con local:{(t_ajustado - time.time())*1000:.3f} ms")
            print(f"  └──────────────────────────────────────────────────┘")

        # Esperar 1 segundo entre sincronizaciones
        if i < NUM_SINCRONIZACIONES:
            time.sleep(1)

    # ── Estadísticas finales ─────────────────────────────────────────
    if rtts:
        print("\n" + "=" * 60)
        print("  ESTADÍSTICAS FINALES")
        print("=" * 60)
        print(f"  RTT mínimo:   {min(rtts)*1000:.3f} ms")
        print(f"  RTT máximo:   {max(rtts)*1000:.3f} ms")
        print(f"  RTT promedio: {(sum(rtts)/len(rtts))*1000:.3f} ms")
        print(f"  Delay prom.:  {(sum(delays)/len(delays))*1000:.3f} ms")
        print("=" * 60)

    print("\n[INFO] Sincronización completada.")

# Punto de entrada del script
if __name__ == "__main__":
    main()
