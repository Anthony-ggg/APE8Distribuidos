import socket
import datetime

def iniciar_coordinador_udp():
    host = '0.0.0.0'
    puerto = 12345

    # Crear el socket UDP (SOCK_DGRAM es la clave aquí)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, puerto))
    
    print(f"Coordinador UDP iniciado en la IP 192.168.1.10, puerto {puerto}.")
    print("Esperando datagramas de las PCs clientes...")

    while True:
        # Espera recibir cualquier dato. addr contiene la IP y puerto del cliente
        mensaje, addr = server_socket.recvfrom(1024)
        
        # t2: Hora exacta del servidor en cuanto recibe el paquete
        t2 = datetime.datetime.now()
        tiempo_str = t2.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # Envía la hora de vuelta directamente a la dirección del cliente
        server_socket.sendto(tiempo_str.encode('utf-8'), addr)
        
        print(f"Petición atendida desde: {addr[0]}. Hora enviada: {tiempo_str}")

if __name__ == '__main__':
    iniciar_coordinador_udp()