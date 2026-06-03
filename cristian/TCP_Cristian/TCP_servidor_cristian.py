import socket
import datetime

def iniciar_coordinador():
    host = '0.0.0.0'  # Escucha en todas las interfaces de red
    puerto = 12345

    # Crear el socket TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permitir reusar la dirección si el script se reinicia rápido
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((host, puerto))
    server_socket.listen(5)
    print(f"Coordinador iniciado en la IP 192.168.1.10, puerto {puerto}.")
    print("Esperando a las PCs clientes...")

    while True:
        client_socket, addr = server_socket.accept()
        
        # t2: Hora exacta del servidor (UTC o local, según decidan)
        t2 = datetime.datetime.now()
        
        # Enviar t2 al cliente como cadena de texto
        tiempo_str = t2.strftime('%Y-%m-%d %H:%M:%S.%f')
        client_socket.send(tiempo_str.encode('utf-8'))
        
        print(f"Petición atendida desde: {addr[0]}. Hora enviada: {tiempo_str}")
        client_socket.close()

if __name__ == '__main__':
    iniciar_coordinador()