import socket
import datetime
import subprocess

# --- CONFIGURACIÓN DEL CLIENTE ---
IP_COORDINADOR = '192.168.1.10'  # IP estática del Servidor/Coordinador
PUERTO_COORDINADOR = 12345       # Debe coincidir con el del servidor

def iniciar_cliente(host_servidor, puerto):
    print("="*60)
    print(" ⏱️  CLIENTE DE SINCRONIZACIÓN (ALGORITMO DE CRISTIAN) ⏱️ ")
    print("="*60)
    print("[*] Preparando conexión con el coordinador maestro...")
    print(f"    - IP Destino: {host_servidor}")
    print(f"    - Puerto: {puerto}\n")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # t1: Hora local antes de enviar la solicitud al servidor
    print("[*] Registrando mi hora local de envío (t1)...")
    t1 = datetime.datetime.now()

    try:
        # Conectar y recibir datos
        print(f"[*] Intentando conectar a {host_servidor}:{puerto}...")
        client_socket.connect((host_servidor, puerto))
        
        print("[*] Conexión exitosa. Esperando respuesta del servidor...")
        respuesta = client_socket.recv(1024).decode('utf-8')

        # t3: Hora local al recibir la respuesta
        t3 = datetime.datetime.now()
        print("[*] Respuesta recibida. Registrando mi hora local de llegada (t3)...\n")

        # Convertir el string recibido (t2) de vuelta a un objeto datetime
        t2 = datetime.datetime.strptime(respuesta, '%Y-%m-%d %H:%M:%S.%f')

        # Calcular el RTT y el Delay
        rtt_segundos = (t3 - t1).total_seconds()
        delay = rtt_segundos / 2

        # Calcular la hora sincronizada
        nuevo_tiempo = t2 + datetime.timedelta(seconds=delay)

        # Mostrar métricas detalladas en consola
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

        # Formatear la nueva hora para el comando de la terminal
        # Se omite el .%f (microsegundos) porque el comando date general no lo suele aceptar
        tiempo_formateado = nuevo_tiempo.strftime('%Y-%m-%d %H:%M:%S')

        # Ejecutar el comando para actualizar el reloj del sistema en Linux
        print("[*] Aplicando la nueva hora al sistema operativo...")
        print(f"    Comando a ejecutar: sudo date -s \"{tiempo_formateado}\"")
        
        # El comando date -s requiere privilegios de superusuario
        subprocess.run(['sudo', 'date', '-s', tiempo_formateado], check=True)
        print("\n[+] ¡ÉXITO! El reloj físico se ha sincronizado correctamente.")

    except ConnectionRefusedError:
        print(f"\n[!] ERROR: Conexión rechazada. Asegúrate de que el Coordinador en la IP {host_servidor} esté ejecutándose y el puerto {puerto} esté abierto.")
    except Exception as e:
        print(f"\n[!] ERROR: Ocurrió un fallo en la conexión o sincronización:\n    Detalle: {e}")
    finally:
        client_socket.close()
        print("[*] Socket cerrado. Proceso finalizado.")

if __name__ == '__main__':
    # Se pasan los parámetros definidos en la parte superior
    iniciar_cliente(IP_COORDINADOR, PUERTO_COORDINADOR)