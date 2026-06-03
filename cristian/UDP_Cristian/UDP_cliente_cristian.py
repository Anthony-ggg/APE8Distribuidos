import socket
import datetime
import subprocess

def iniciar_cliente_udp():
    host_servidor = '192.168.1.10' # IP del Coordinador (PC1)
    puerto = 12345

    # Crear el socket UDP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # IMPORTANTE en UDP: Establecer un tiempo de espera por si se pierde el paquete
    client_socket.settimeout(3.0) 

    # Mensaje de prueba para "despertar" al servidor (puede ser cualquier cosa)
    mensaje_peticion = "DAME_LA_HORA"

    try:
        # t1: Hora local justo antes de enviar el datagrama
        t1 = datetime.datetime.now()
        
        # Enviar el datagrama al coordinador
        client_socket.sendto(mensaje_peticion.encode('utf-8'), (host_servidor, puerto))

        # Esperar la respuesta (t2) del coordinador
        respuesta, servidor_addr = client_socket.recvfrom(1024)
        
        # t3: Hora local justo al recibir la respuesta
        t3 = datetime.datetime.now()

        # Decodificar y convertir el string recibido de vuelta a datetime
        tiempo_str = respuesta.decode('utf-8')
        t2 = datetime.datetime.strptime(tiempo_str, '%Y-%m-%d %H:%M:%S.%f')

        # Calcular el RTT y el Delay
        rtt_segundos = (t3 - t1).total_seconds()
        delay = rtt_segundos / 2

        # Calcular la hora sincronizada (Algoritmo de Cristian)
        nuevo_tiempo = t2 + datetime.timedelta(seconds=delay)

        # Mostrar métricas
        print("--- RESULTADOS CRISTIAN (UDP) ---")
        print(f"t1 (Envío)        : {t1}")
        print(f"t2 (Hora Servidor): {t2}")
        print(f"t3 (Recepción)    : {t3}")
        print(f"RTT Total         : {rtt_segundos} segundos")
        print(f"Delay             : {delay} segundos")
        print(f"NUEVA HORA        : {nuevo_tiempo}")
        print("---------------------------------")

        # Formatear y aplicar la hora en el sistema operativo (requiere sudo)
        tiempo_formateado = nuevo_tiempo.strftime('%Y-%m-%d %H:%M:%S')
        print("Aplicando nueva hora al sistema operativo...")
        
        subprocess.run(['sudo', 'date', '-s', tiempo_formateado], check=True)
        print("¡El reloj físico se ha sincronizado correctamente por UDP!")

    except socket.timeout:
        print("Error: El paquete UDP se perdió o el servidor no responde (Timeout).")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        client_socket.close()

if __name__ == '__main__':
    iniciar_cliente_udp()