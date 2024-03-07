#importing the required libraries

from http import server
import socket
import os
import sys
import threading
import select
from getpass import getpass
from cryptography.fernet import Fernet
from tinydb import TinyDB, Query
os.getcwd()



host = "127.0.0.1"
port = 5555 # Choose any random port which is not so common (like 80)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Bind the server to IP Address
server.bind((host, port))
#Start Listening Mode
server.listen()
#List to contain the Clients getting connected and nicknames
clients = []
nicknames = []


#Function to check if directory for chat data is existing on folder if not it will make directory
def checkDBExists():
    if not os.path.isdir("Data"):
        os.mkdir("Data")

#function calling
checkDBExists()


file = open('Data/users.json', 'w')
file.close()

file = open('bans.txt', 'w')
file.close()

file = open('Data/log.txt', 'w')
file.close()

db = TinyDB('Data/users.json')

#to truncate the DB
db.truncate()


#generating the key for encryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)
file = open('Data/key.key', 'wb')
file.write(key)
file.close()


#General log for chat application. This function logs all activity in chat application
class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass


sys.stdout = Logger("Data/server.txt")

#to create user object which include different parameter to save user details in database
class User(object):
    def __init__(self, nickname):
        self.nickname = nickname
        self.password = ""
        self.warn = 0



# Broadcasting Method
def broadcast(message):
    for client in clients:
        client.send(message)
        file = open('Data/log.txt', 'wb')
        encrypted = cipher_suite.encrypt(message)
        file.write(encrypted)
        file.close()


# Recieving Messages from client then broadcasting
def handle(client):
    while True:
        try:
            msg = message = client.recv(1024)  
            if msg.decode('ascii').startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = msg.decode('ascii')[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command Refused!'.encode('ascii'))
            elif msg.decode('ascii').startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = msg.decode('ascii')[4:]
                    kick_user(name_to_ban)
                    with open('bans.txt','a') as f:
                        f.write(f'{name_to_ban}\n')
                    print(f'{name_to_ban} was banned by the Admin!')
                else:
                    client.send('Command Refused!'.encode('ascii'))
            else:

                # As soon as message recieved, broadcast it.
                broadcast(message)
        except:
            if client in clients:
                index = clients.index(client)
                #Index is used to remove client from list after getting diconnected
                clients.remove(client)
                client.close
                nickname = nicknames[index]
                broadcast(f'{nickname} left the Chat!'.encode('ascii'))
                nicknames.remove(nickname)
                break
# Main Recieve method
def recieve():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")
        # Ask the clients for Nicknames
        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        password = client.recv(1024).decode('ascii')
        # If the Client is an Admin promopt for the password.
        with open('bans.txt', 'r') as f:
            bans = f.readlines()
        
        if nickname+'\n' in bans:
            client.send('BAN'.encode('ascii'))
            client.close()
            continue

        if nickname == 'admin':
            client.send('PASS'.encode('ascii'))
            password = client.recv(1024).decode('ascii')
            # I know it is lame, but my focus is mainly for Chat system and not a Login System
            if password != 'adminpass':
                client.send('REFUSE'.encode('ascii'))
                client.close()
                continue

        nicknames.append(nickname)
        clients.append(client)

        #checks the user if not insert
        db.truncate()
        for nickname in nicknames:
            query = Query()
            checkIfUsernameExists(nickname,password,query)
        
        print(f'Nickname of the client is {nickname}')
        broadcast(f'{nickname} joined the Chat'.encode('ascii'))
        client.send('Connected to the Server!'.encode('ascii'))

        # Handling Multiple Clients Simultaneously
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('You Were Kicked from Chat !'.encode('ascii'))
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f'{name} was kicked from the server!'.encode('ascii'))



def checkIfUsernameExists(nickname,password, query):
    if not db.search(query.nickname == nickname):
        data = {
            "nickname": nickname,
            "password": password
        }
        db.insert(data)

#Calling the main method
print('Server is Listening ...')
recieve()