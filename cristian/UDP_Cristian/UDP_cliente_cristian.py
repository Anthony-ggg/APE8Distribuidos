import socket
import datetime
import subprocess

# --- CONFIGURACIÓN DEL CLIENTE UDP ---
IP_COORDINADOR = '192.168.1.10'  # IP estática del Servidor/Coordinador
PUERTO_COORDINADOR = 12345       # Debe coincidir con el del servidor

def iniciar_cliente_udp(host_servidor, puerto):
    print("="*60)
    print(" ⏱️  CLIENTE UDP DE SINCRONIZACIÓN (CRISTIAN) ⏱️ ")
    print("="*60)
    print("[*] Preparando envío de datagrama al coordinador maestro...")
    print(f"    - IP Destino: {host_servidor}")
    print(f"    - Puerto: {puerto}\n")

    # Crear el socket UDP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # IMPORTANTE en UDP: Establecer un tiempo de espera por si se pierde el paquete
    client_socket.settimeout(3.0) 

    # Mensaje de prueba para "despertar" al servidor
    mensaje_peticion = "DAME_LA_HORA"

    try:
        # t1: Hora local justo antes de enviar el datagrama
        print("[*] Registrando mi hora local de envío (t1)...")
        t1 = datetime.datetime.now()
        
        # Enviar el datagrama al coordinador
        print(f"[*] Enviando solicitud ('{mensaje_peticion}') a {host_servidor}:{puerto}...")
        client_socket.sendto(mensaje_peticion.encode('utf-8'), (host_servidor, puerto))

        print("[*] Datagrama enviado. Esperando respuesta del servidor...")
        
        # Esperar la respuesta (t2) del coordinador
        respuesta, servidor_addr = client_socket.recvfrom(1024)
        
        # t3: Hora local justo al recibir la respuesta
        t3 = datetime.datetime.now()
        print("[*] Respuesta recibida. Registrando mi hora local de llegada (t3)...\n")

        # Decodificar y convertir el string recibido de vuelta a datetime
        tiempo_str = respuesta.decode('utf-8')
        t2 = datetime.datetime.strptime(tiempo_str, '%Y-%m-%d %H:%M:%S.%f')

        # Calcular el RTT y el Delay
        rtt_segundos = (t3 - t1).total_seconds()
        delay = rtt_segundos / 2

        # Calcular la hora sincronizada (Algoritmo de Cristian)
        nuevo_tiempo = t2 + datetime.timedelta(seconds=delay)

        # Mostrar métricas
        print("┌──────────────────────────────────────────────────────────┐")
        print("│           📊 RESULTADOS DEL CÁLCULO DE TIEMPO            │")
        print("├──────────────────────────────────────────────────────────┤")
        print(f"│ [t1] Mi hora al enviar      : {t1}")
        print(f"│ [t2] Hora del servidor      : {t2}")
        print(f"│ [t3] Mi hora al recibir     : {t3}")
        print("├──────────────────────────────────────────────────────────┤")
        print(f"│ RTT (Tiempo total de viaje) : {rtt_segundos:.6f} segundos")
        print(f"│ Delay (Viaje de un solo lado): {delay:.6f} segundos")
        print("├──────────────────────────────────────────────────────────┤")
        print(f"│ 🎯 NUEVA HORA CALCULADA     : {nuevo_tiempo}")
        print("└──────────────────────────────────────────────────────────┘\n")

        # Formatear y aplicar la hora en el sistema operativo (requiere sudo)
        tiempo_formateado = nuevo_tiempo.strftime('%Y-%m-%d %H:%M:%S')
        print("[*] Aplicando la nueva hora al sistema operativo...")
        print(f"    Comando a ejecutar: sudo date -s \"{tiempo_formateado}\"")
        
        subprocess.run(['sudo', 'date', '-s', tiempo_formateado], check=True)
        print("\n[+] ¡ÉXITO! El reloj físico se ha sincronizado correctamente por UDP.")

    except socket.timeout:
        print(f"\n[!] ERROR: El paquete UDP se perdió o el servidor en {host_servidor} no responde (Timeout de 3.0s).")
    except Exception as e:
        print(f"\n[!] ERROR: Ocurrió un error inesperado:\n    Detalle: {e}")
    finally:
        client_socket.close()
        print("[*] Socket cerrado. Proceso finalizado.")

if __name__ == '__main__':
    # Se pasan los parámetros definidos en la parte superior
    iniciar_cliente_udp(IP_COORDINADOR, PUERTO_COORDINADOR)