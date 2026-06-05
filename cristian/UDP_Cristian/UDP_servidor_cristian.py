import socket
import datetime

# --- CONFIGURACIÓN DEL SERVIDOR UDP ---
HOST_SERVIDOR = '0.0.0.0'      # Escucha en todas las interfaces de red
PUERTO_SERVIDOR = 12345        # ¡Cámbialo aquí fácilmente!
IP_ESPERADA_RED = '192.168.1.10' # IP estática para mostrar en consola

def iniciar_coordinador_udp(host, puerto):
    # Crear el socket UDP (SOCK_DGRAM es la clave aquí)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, puerto))
    
    print("="*55)
    print(" 🕒 COORDINADOR UDP (ALGORITMO DE CRISTIAN) 🕒 ")
    print("="*55)
    print("[*] Inicializando servidor maestro...")
    print(f"[*] Escuchando en la interfaz: {host}")
    print(f"[*] Puerto configurado: {puerto}")
    print(f"[*] (IP esperada en la red LAN: {IP_ESPERADA_RED})")
    print("[*] Estado: Esperando datagramas de las PCs clientes...\n")

    while True:
        # Espera recibir cualquier dato. addr contiene la IP y puerto del cliente
        mensaje, addr = server_socket.recvfrom(1024)
        print(f"[+] ¡Nuevo datagrama de sincronización recibido!")
        print(f"    - Desde el cliente con IP: {addr[0]}:{addr[1]}")
        print(f"    - Mensaje recibido: '{mensaje.decode('utf-8')}'")
        
        # t2: Hora exacta del servidor en cuanto recibe el paquete
        t2 = datetime.datetime.now()
        tiempo_str = t2.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # Envía la hora de vuelta directamente a la dirección del cliente
        server_socket.sendto(tiempo_str.encode('utf-8'), addr)
        
        print(f"    - [t2] Hora exacta enviada: {tiempo_str}")
        print(f"    - Respuesta enviada a {addr[0]} correctamente.\n")
        print("[*] Esperando el siguiente datagrama...")

if __name__ == '__main__':
    # Se pasan los parámetros definidos en la parte superior
    iniciar_coordinador_udp(HOST_SERVIDOR, PUERTO_SERVIDOR)