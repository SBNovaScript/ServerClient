"""AsyncServer.py

usage: Async Server [-h] [-p port] host

Example:
    > python AsyncServer.py localhost -p 1060

Author:              Steven Baumann
Class:               CSI-235
Assignment:          Final Project
Date Assigned:       4/6/2018
Due Date:            4/26/2018 11:59 PM

Description:
This server allows for asynchronous communication between it's clients. The client connects to this server over
a TLS SSL connection, then can send messages freely to other users.

"""

import json
import asyncio
import socket
import argparse
import time
import struct
import ssl


list_users = {}
message_list = []
backup_loaded = 0

@asyncio.coroutine
def handle_conversation(reader, writer):
    '''Called when we receive a new connection from a client.

    After a connection is made with the client through asyncio, this function is called to handle the conversation
    between client and server.

    The overall purpose of handle_conversation is to greet new clients by
    supplying them with a greeting, a list of currently online users,
    give all of the past messages to them (including their direct messages),
    and allow them to add their messages to the pool of messages.

    args:
        reader (obj): The reader object is used to read messages from the client.
        writer (obj): The writer object is used to write messages to the client.

    raises:
        ConnectionResetError: In the event that a client should close unexpectedly,
                              we can gracefully tell other users that they have left,
                              and remove their name and IP from list_users.

    '''
    global backup_loaded
    global list_users
    global message_list
    address = writer.get_extra_info('peername')
    print('Accepted connection from {}'.format(address))
    accepted_user = 0
    has_connection = 1

    while has_connection == 1:
        try:
            data = yield from reader.read(4)
            if data == b'':
                if address in list_users:
                    print('Connection with {} closed.'.format(list_users[address][0]))
                    del list_users[address]
                    for j in list_users.values():
                        send_message({"INFO": "{} has left the server!".format(user)}, j[1])
                else:
                    print('Connection with {} closed.'.format(address))
                    has_connection = 0
                return
            else:
                if accepted_user == 0:
                    more_data = yield from reader.read(struct.unpack('!I', data)[0])
                    user = json.loads(more_data).get('USERNAME')

                    if user in list_users.values():
                        print("{} tried to connect with a duplicate username.".format(user))
                        send_message({"USERNAME_ACCEPTED": "false","INFO": "Username already in use."}, writer)
                    else:
                        if backup_loaded == 0:
                            try:
                                backup_messages = open('backup.txt','r')
                                if len(backup_messages.read()) > 1:
                                    restore_backup()
                                    backup_loaded = 1
                                backup_messages.close()
                            except IOError:
                                backup_messages = open('backup.txt','w')
                                backup_loaded = 1
                                backup_messages.close()

                        accepted_user = 1
                        print("Welcome {} !".format(user))

                        for j in list_users.values():
                            send_message({"INFO": "{} has joined the server!".format(user)}, j[1])

                        list_users[address] = (user, writer)

                        users_online = []

                        for i in list_users.values():
                            users_online += [i[0]]

                        sendable_messages = []

                        for i in message_list:
                            if i[1] == 'ALL' or i[1] == user:
                                sendable_messages += [i]

                        send_message({"USERNAME_ACCEPTED": "true", "INFO": "Welcome to the server!", "USER_LIST": users_online, "MESSAGES": sendable_messages}, writer)
                else:
                    message_raw = yield from reader.read(struct.unpack('!I', data)[0])

                    browser_data = json.loads(message_raw).get("BROWSER")
                    if browser_data:
                        total_url = "https://www.google.com/search?q=" + browser_data[0]
                        send_message({"BROWSER": total_url}, writer)
                        if browser_data[2] == 1:
                            print("{} has just searched the following: ".format(browser_data[1]) + browser_data[0])
                            for j in list_users.values():
                                send_message({"INFO": "{} has just searched the following: ".format(browser_data[1]) + browser_data[0]}, j[1])

                    message_data = json.loads(message_raw).get("MESSAGES")
                    send_mass_messages(message_data, writer, address)

        except ConnectionResetError:
            print('Connection with {} closed.'.format(list_users[address][0]))
            has_connection = 0
            if address in list_users:
                    del list_users[address]
                    for j in list_users.values():
                        send_message({"INFO": "{} has left the server!".format(user)}, j[1])


def send_mass_messages(message_data, writer, address):
    '''send_mass_messages is used to notify all online clients of an event.

    send_mass_messages is utilized by the AsyncServer function, allowing it to parse clients messages,
    add them to the backup (past messages) file, and send them to the correct users.

    args:
        message_data (list): message_data is the message and it's data that the client has supplied us with.
                             We can parse message_data to send the message to the right users.
        writer (obj): The writer gives us the current clients writer object (the one who we have received the message from)
        address (list): The host and ip of the current client, so that we can send them user not found errors.

    '''
    global message_list
    global list_users
    if message_data:
        if list_users[address][0] != message_data[0][0]:
            send_message({"ERROR": "Source username is not correct."}, writer)
        else:
            if type(message_data[0][0]) != str or type(message_data[0][1]) != str or type(message_data[0][2]) != int or type(message_data[0][3]) != str:
                send_message({"ERROR": "Message has incorrect type."}, writer)
            else:
                message_list += message_data
                for i in message_data:
                    if i[1] == "ALL":
                        backup_messages = open('backup.txt','a')
                        backup_messages.write(json.dumps(message_data))
                        backup_messages.write('\n')
                        backup_messages.close()
                        print(i[0] + " says: " + i[3])
                        for j in list_users.values():
                            send_message({"MESSAGES": message_data}, j[1])
                    else:
                        in_users = 0
                        sending_writer = writer
                        for k in list_users.values():
                            if k[0] == i[1]:
                                in_users = 1
                                sending_writer = k[1]
                        if in_users == 1:
                            backup_messages = open('backup.txt','a')
                            backup_messages.write(json.dumps(message_data))
                            backup_messages.write('\n')
                            backup_messages.close()
                            send_message({"MESSAGES": message_data}, sending_writer)
                        else:
                            send_message({"ERROR": "The user you specified could not be found."}, writer)


def restore_backup():
    '''used by the server to restore messages.

    contrary to its name, restore_backup does not restore backed up messages for all users, or even load them into
    message_list. Instead, it allows the server to print past messages onto it's command prompt.

    '''
    global message_list
    global list_users

    backup_messages = open('backup.txt','r')

    current_location = backup_messages.readlines()

    for data in current_location:
        message_data = json.loads(data)
        for i in message_data:
            if i[1] == "ALL":
                print(i[0] + " Said: " + i[3])

    backup_messages.close()


def send_message(message, writer):
    '''Used to send messages to the client.

    The basic, yet the most powerful function, allows us to send a message to a client.
    Used in any other function that needs to communicate with the clients. It encrypts the supplied message,
    attaches a 4 byte unsigned int that displays the length as a prefix, and sends the message.

    args:
        message (list): the raw message to be sent to the client, before being encoded.
        writer (obj): the users writer that we are sending the message to.

    '''
    json_data = json.dumps(message).encode('ascii')
    message_len = struct.pack('!I', len(json_data))
    writer.write(message_len + json_data)


def parse_command_line(message):
    '''Called when we need to get args from the command line.

    This function is used by the " if __name__ == '__main__' " condition, and gives it a list of user supplied arguments.

    args:
        message (str): The help message that is displayed when the user asks for help.

    returns:
        address (list): address is a list containing the host and port that we would like to setup the AsyncServer on.

    '''
    parser = argparse.ArgumentParser(message)
    parser.add_argument('host', help='Hostname')
    parser.add_argument('-p', metavar='port', type=int, default=1060, help='Port #')
    args = parser.parse_args()
    address = (args.host, args.p)
    return address


if __name__ == '__main__':
    '''
    Here we initialize the appropriate SSL contexts, as well as loading from the backup file, 
    and starting the server loop.
    '''

    address = parse_command_line('Async Server')
    loop = asyncio.get_event_loop()

    purpose = ssl.Purpose.CLIENT_AUTH
    context = ssl.create_default_context(purpose, cafile="ca.crt")
    context.load_cert_chain('localhost.pem')

    coro = asyncio.start_server(handle_conversation, *address, ssl=context)
    server = loop.run_until_complete(coro)
    print('Listening at {}'.format(address))

    try:
        backup_messages = open('backup.txt','r')
        if len(backup_messages.read()) > 1:
            backup_messages.seek(0)
            print("Waiting for client to connect to resume session...")
            total_messages = backup_messages.readlines()
            for i in total_messages:
                message_list += json.loads(i)
        backup_messages.close()
    except IOError:
        backup_messages = open('backup.txt','w')
        backup_messages.close()

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
