import socket
import select
import time
# Set the IP address and port of the Arduino server
server_ip = "192.168.1.15"  # Replace with the actual IP address of your Arduino
server_port = 2390
client_socket = 0
i = 0
def EstablishClient():
    global client_socket
    # Create a socket connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))


def SendToArduino(str):
    global client_socket
    # Send a string to the server
    client_socket.sendall(str.encode())

def ReceiveFromArduino():
    global client_socket
    global i
    # Set the socket to non-blocking mode
    client_socket.setblocking(0)
    while True:
        # Wait for the socket to become readable
        ready, _, _ = select.select([client_socket], [], [], 0.1)  # Timeout set to 1 second
        time.sleep(0.1)
        if ready:
            # Receive the response from the server
            server_response = client_socket.recv(1024)
            if not server_response:
                break  # Connection closed by the server
            print(f"Server response {i}")
            print(server_response.decode())
            i+=1
            return server_response

# Close the socket connection
#client_socket.close()

EstablishClient()
while True:
    #SendToArduino("aa")
    time.sleep(1)
    ReceiveFromArduino()

