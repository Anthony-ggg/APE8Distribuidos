import socket
import datetime

# --- CONFIGURACIÓN DEL SERVIDOR ---
HOST_SERVIDOR = '0.0.0.0'      # Escucha en todas las interfaces de red
PUERTO_SERVIDOR = 12345        # ¡Cámbialo aquí fácilmente!
IP_ESPERADA_RED = '192.168.1.10' # IP estática para mostrar en consola

def iniciar_coordinador(host, puerto):
    # Crear el socket TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permitir reusar la dirección si el script se reinicia rápido
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((host, puerto))
    server_socket.listen(5)
    
    print("="*55)
    print(" 🕒 COORDINADOR DE RELOJES (ALGORITMO DE CRISTIAN) 🕒 ")
    print("="*55)
    print("[*] Inicializando servidor maestro...")
    print(f"[*] Escuchando en la interfaz: {host}")
    print(f"[*] Puerto configurado: {puerto}")
    print(f"[*] (IP esperada en la red LAN: {IP_ESPERADA_RED})")
    print("[*] Estado: Esperando a que las PCs clientes se conecten...\n")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[+] ¡Nueva petición de sincronización recibida!")
        print(f"    - Desde el cliente con IP: {addr[0]}:{addr[1]}")
        
        # t2: Hora exacta del servidor (UTC o local, según decidan)
        t2 = datetime.datetime.now()
        
        # Enviar t2 al cliente como cadena de texto
        tiempo_str = t2.strftime('%Y-%m-%d %H:%M:%S.%f')
        client_socket.send(tiempo_str.encode('utf-8'))
        
        print(f"    - [t2] Hora exacta enviada: {tiempo_str}")
        print(f"    - Conexión con {addr[0]} finalizada correctamente.\n")
        print("[*] Esperando la siguiente petición...")
        
        client_socket.close()

if __name__ == '__main__':
    # Se pasan los parámetros definidos en la parte superior
    iniciar_coordinador(HOST_SERVIDOR, PUERTO_SERVIDOR)