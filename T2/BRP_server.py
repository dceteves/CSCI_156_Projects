import socket
import threading

# Get port and server info
PORT = 8000
SERVER = socket.gethostbyname(socket.gethostname())


# Store client info
client_sockets = {}

# Store rooms for multicasting/breakout room implementation
# Initialize with the main room
rooms = { 'main': [] }

# Command prefix
command_prefix = '!'

def listRooms():
    """Returns a list of available rooms
    Return:
        output (string)
    """
    output = ""
    for key in rooms:
        output += key + "\n"
    return output

def createRoom(room_name):
    if room_name in rooms:
        return "Room aleady exists"

    rooms[room_name] = []
    return "Room created" 

def joinRoom(client_socket, addr, room_name):
    if room_name not in rooms:
        return "Room does not exist"

    rooms[client_sockets[addr]['room']].remove(client_socket)
    broadcast(f"{client_sockets[addr]['name']} has left the room", client_sockets[addr]['room'])

    client_sockets[addr]['room'] = room_name
    rooms[room_name].append(client_socket)

    broadcast(f"{client_sockets[addr]['name']} has joined the room", room_name, client_socket)
    return f"You have joined room {room_name}"

def broadcast(message, room_name, client_except=None):
    """Sends a message to all clients in a room

    Args:
        message (string): Message to be broadcasted to
        room (string): name of the room to be broadcasted in 
        client_except (socket): Client socket which will not get the message (optional)
    """

    for client in rooms[room_name]:
        if client != client_except:
            client.send(message.encode('utf-8'))

def handle_command(client_socket, addr, message):
    if message[0] == '!room':
        client_socket.send(client_sockets[addr]['room'].encode('utf-8'))
    elif message[0] == '!list':
        client_socket.send(listRooms().encode('utf-8'))
    elif message[0] == '!join' and len(message) > 1:
        client_socket.send(joinRoom(client_socket, addr, message[1]).encode('utf-8'))
    elif message[0] == '!create' and len(message) > 1 and client_sockets[addr]['type']:
        client_socket.send(createRoom(message[1]).encode('utf-8'))
    else:
        client_socket.send("Unknown Command".encode('utf-8'))

def handle_message(client_socket, addr, message):
    """Handles messages from the client

    Args:
        client_socket (socket): The client socket that sent the message
        addr (string): Address of the client socket
        message (string): The client's message

    """
    if client_sockets[addr]['type']:
        client_type = "(INSTRUCTOR)" 
    else:
        client_type = "(STUDENT)"

    output = f"{client_type} {client_sockets[addr]['name']}: {message}"

    if message[0] != command_prefix:
        print(f"[{client_sockets[addr]['room']}] {output}")
        broadcast(output, client_sockets[addr]['room'], client_socket);
    else:
        handle_command(client_socket, addr, message.split())
    
def handle_client(client_socket, addr):
    """Handles client connections via multithreading

    Args:
        client_socket (socket):
        addr (string): Address of the client
    """
    connected = True
    while connected:
        message = client_socket.recv(1024).decode('utf-8')
        if message:
            if message == "!quit":
                connected = False
                rooms[client_sockets[addr]['room']].remove(client_socket)
                client_socket.close()
            else:
                handle_message(client_socket, addr, message)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER, PORT))
    server_socket.listen(5)
    print(f"Server listening on port {PORT}")

    while True:
        client_socket, addr = server_socket.accept()

        client_info = client_socket.recv(1024).decode('utf-8')
        client_sockets[addr] = {
                'type': int(client_info[0]),
                'name': client_info[1:],
                'room': 'main'
                }

        rooms['main'].append(client_socket)

        print(f"{client_sockets[addr]} connected from {addr}")
        for room in rooms:
            broadcast(f"{client_sockets[addr]['name']} has joined main room", room)

        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))


        client_handler.start()

        

if __name__ == "__main__":
    start_server()

