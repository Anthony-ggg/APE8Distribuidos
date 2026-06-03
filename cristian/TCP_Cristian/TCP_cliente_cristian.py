import socket
import datetime
import subprocess

def iniciar_cliente():
    host_servidor = '192.168.1.10'  # Asegúrate de que esta sea la IP estática del Coordinador
    puerto = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # t1: Hora local antes de enviar la solicitud al servidor
    t1 = datetime.datetime.now()

    try:
        # Conectar y recibir datos
        client_socket.connect((host_servidor, puerto))
        respuesta = client_socket.recv(1024).decode('utf-8')

        # t3: Hora local al recibir la respuesta
        t3 = datetime.datetime.now()

        # Convertir el string recibido (t2) de vuelta a un objeto datetime
        t2 = datetime.datetime.strptime(respuesta, '%Y-%m-%d %H:%M:%S.%f')

        # Calcular el RTT y el Delay
        rtt_segundos = (t3 - t1).total_seconds()
        delay = rtt_segundos / 2

        # Calcular la hora sincronizada
        nuevo_tiempo = t2 + datetime.timedelta(seconds=delay)

        # Mostrar métricas en consola
        print("--- RESULTADOS DEL ALGORITMO DE CRISTIAN ---")
        print(f"t1 (Mi hora al enviar) : {t1}")
        print(f"t2 (Hora del servidor) : {t2}")
        print(f"t3 (Mi hora al recibir): {t3}")
        print(f"RTT Total              : {rtt_segundos} segundos")
        print(f"Delay (Tiempo de viaje): {delay} segundos")
        print(f"NUEVA HORA CALCULADA   : {nuevo_tiempo}")
        print("--------------------------------------------")

        # Formatear la nueva hora para el comando de la terminal
        # Se omite el .%f (microsegundos) porque el comando date general no lo suele aceptar
        tiempo_formateado = nuevo_tiempo.strftime('%Y-%m-%d %H:%M:%S')

        # Ejecutar el comando para actualizar el reloj del sistema en Linux
        print("Aplicando nueva hora al sistema operativo...")
        
        # El comando date -s requiere privilegios de superusuario
        subprocess.run(['sudo', 'date', '-s', tiempo_formateado], check=True)
        print("¡El reloj físico se ha sincronizado correctamente!")

    except Exception as e:
        print(f"Ocurrió un error en la conexión o sincronización: {e}")
    finally:
        client_socket.close()

if __name__ == '__main__':
    iniciar_cliente()