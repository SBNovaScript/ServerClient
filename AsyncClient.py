"""AsyncClient.py

usage: Async Client [-h] [-p port] [-c cafile] [-t time_on] [-u user_on]
                    [-s space_on]
                    host

Example:
    > python AsyncClient.py localhost -p 1060 -t n

Author:              Steven Baumann
Class:               CSI-235
Assignment:          Final Project
Date Assigned:       4/6/2018
Due Date:            4/26/2018 11:59 PM

Description:
    This client allows for asynchronous communication between the server it connects to.
    The client connects to this server over a TLS SSL connection, then can send messages freely to other users.

"""

import json
import argparse
import asyncio
import time
import datetime
import struct
import ssl
import webbrowser


class AsyncClient(asyncio.Protocol):
    '''This is the main Client class, used to connect to the server.

    This class is used later in the " if __name__ == '__main__' " condition,
    where it is passed to a create_connection function.

    Args:
        time_on (str): This is a parsed command, which specifies
                 whether or not the user would like to see the time before each individual message. The default is yes.

        user_on (str): Similar to time_on, except allows the user to filter out usernames before each message.
                       The default is yes.

        space_on (str): Similar to the other two arguments, except that this allows the user
                        to put an extra space in between each message. The default is no.

    '''

    def __init__(self, time_on, user_on, space_on):
        self.buffer = b''
        self.user = input("Please enter your username: ")
        self.time_on = time_on
        self.user_on = user_on
        self.space_on = space_on
        self.connected = 0
        self.total_len = 0

    def connection_made(self, transport):
        '''Used by asyncio after a connection has been established.

        The connection_made function is called after the client
        successfully connects to the server though the asyncio protocol.

        args:
            transport (obj): The transport is the representation between the client and the server,
                             allowing communications between them.

        '''
        self.transport = transport
        self.address = transport.get_extra_info('peername')

        message_data = {"USERNAME": self.user}
        json_data = json.dumps(message_data).encode('ascii')
        message_len = struct.pack('!I', len(json_data))
        self.transport.write(message_len + json_data)

    def data_received(self, data):
        '''Called after the client receives an amount of data from the server.

        The data_received function is called after the client receives a piece of data from the server.
        since data_received is called every time a piece of data is sent, it is important to have member variables
        that can differentiate between the different states that the client is in. For instance, I am using
            self.connected
        here, to differentiate between the times that I am connected to the server and receiving data, or when
        I am not connected and receiving data.

        In general, the data that we receive with this function must be parsed through json.loads(), then allocated
        to the correct variable, or printed out to the screen when necessary. We receive data by calling their key
        values, e.g. response.get("MESSAGES") or response.get("USERS_JOINED"). The great thing about this method
        is that we can pick and choose which pieces of datat we would like to utilize from the dataset that we are given.

        args:
            data (bytes): The data that the server has send to the client to be evaluated.

        '''
        if self.buffer == b'':
            self.buffer = data
            self.total_len = struct.unpack('!I', self.buffer[:4])[0]

            if len(self.buffer)+len(data) >= self.total_len and self.connected == 0:
                response = json.loads(self.buffer[4:])

                status = response.get("USERNAME_ACCEPTED")
                info = response.get("INFO", "No info provided.")

                if not status:
                    print(info + " please type quit to try again.")
                else:
                    self.connected = 1
                    print("\n We have connected to {} successfully with username {}!".format(address[0], self.user))
                    print("The server says, {}".format(info))
                    if response.get("USER_LIST") == [self.user]:
                        print("You are the only user online! \n")
                    else:
                        print("Users online: {} \n".format(response.get("USER_LIST")))

                    messages = response.get("MESSAGES")
                    if messages:
                        for i in messages:
                            if self.time_on == 'n' and self.user_on == 'y':
                                print(i[0] + " said: " + i[3])
                            elif self.time_on == 'y' and self.user_on == 'n':
                                print(str(datetime.datetime.fromtimestamp(i[2])) + ": " + i[3])
                            elif self.time_on == 'n' and self.user_on == 'n':
                                print(i[3])
                            else:
                                print("At " + str(datetime.datetime.fromtimestamp(i[2])) + ", " + i[0] + " said: " + i[3])
                            if self.space_on == 'y':
                                print('')

                    self.buffer = b''

            elif len(self.buffer)+len(data) >= self.total_len and self.connected == 1:
                response = json.loads(self.buffer[4:])

                messages = response.get("MESSAGES")
                users_joined = response.get("USERS_JOINED")
                users_left = response.get("USERS_LEFT")
                other_info = response.get("INFO")
                error_info = response.get("ERROR")
                browser_info = response.get("BROWSER")

                if messages:
                    for i in messages:
                        if self.time_on == 'n' and self.user_on == 'y':
                            print(i[0] + " said: " + i[3])
                        elif self.time_on == 'y' and self.user_on == 'n':
                            print(str(datetime.datetime.fromtimestamp(i[2])) + ": " + i[3])
                        elif self.time_on == 'n' and self.user_on == 'n':
                            print(i[3])
                        else:
                            print("At " + str(datetime.datetime.fromtimestamp(i[2])) + ", " + i[0] + " said: " + i[3])
                        if self.space_on == 'y':
                            print('')

                if users_joined:
                    for i in users_joined:
                        print(i + " has joined the server!")

                if users_left:
                    for i in users_left:
                        print(i + " has left the server. Bye!")

                if other_info:
                    print("The server says: " + other_info)

                if error_info:
                    print("The server responded with this error: " + error_info)

                if browser_info:
                    webbrowser.open(browser_info)

                self.buffer = b''
        elif len(self.buffer)+len(data) < self.total_len:
            self.buffer += data

        elif len(self.buffer)+len(data) >= self.total_len and self.connected == 0:
            self.buffer += data
            response = json.loads(self.buffer[4:])

            status = response.get("USERNAME_ACCEPTED")
            info = response.get("INFO", "No info provided.")

            if not status:
                print(info + " please type quit to try again.")
            else:
                self.connected = 1
                print("\n We have connected to {} successfully with username {}!".format(address, self.user))
                print("The server says, {}".format(info))
                if response.get("USER_LIST") == [self.user]:
                    print("You are the only user online! \n")
                else:
                    print("Users online: {} \n".format(response.get("USER_LIST")))

                messages = response.get("MESSAGES")
                if messages:
                    for i in messages:
                        if self.time_on == 'n' and self.user_on == 'y':
                            print(i[0] + " said: " + i[3])
                        elif self.time_on == 'y' and self.user_on == 'n':
                            print(str(datetime.datetime.fromtimestamp(i[2])) + ": " + i[3])
                        elif self.time_on == 'n' and self.user_on == 'n':
                            print(i[3])
                        else:
                            print("At " + str(datetime.datetime.fromtimestamp(i[2])) + ", " + i[0] + " said: " + i[3])
                        if self.space_on == 'y':
                            print('')

            self.buffer = b''

        elif len(self.buffer)+len(data) >= self.total_len and self.connected == 1:
            self.buffer += data
            response = json.loads(self.buffer[4:])

            messages = response.get("MESSAGES")
            users_joined = response.get("USERS_JOINED")
            users_left = response.get("USERS_LEFT")
            other_info = response.get("INFO")
            error_info = response.get("ERROR")
            browser_info = response.get("BROWSER")

            if messages:
                for i in messages:
                    if self.time_on == 'n' and self.user_on == 'y':
                        print(i[0] + " said: " + i[3])
                    elif self.time_on == 'y' and self.user_on == 'n':
                        print(str(datetime.datetime.fromtimestamp(i[2])) + ": " + i[3])
                    elif self.time_on == 'n' and self.user_on == 'n':
                        print(i[3])
                    else:
                        print("At " + str(datetime.datetime.fromtimestamp(i[2])) + ", " + i[0] + " said: " + i[3])
                    if self.space_on == 'y':
                        print('')

            if users_joined:
                for i in users_joined:
                    print(i + " has joined the server!")

            if users_left:
                for i in users_left:
                    print(i + " has left the server. Bye!")

            if other_info:
                print("The server says: " + other_info)

            if error_info:
                print("The server responded with this error: " + error_info)

            if browser_info:
                webbrowser.open(browser_info)

            self.buffer = b''

    def connection_lost(self, exc):
        '''Called when connection is lost with the server.

        args:
            exc: The exception that was raised which led to the loss of connection.

        '''
        print('Client {} closed socket'.format(self.address))

    @asyncio.coroutine
    def messaging(self, loop):  #in message / receiving mode
        '''Messaging is called in an asynchronous manner, to send messages to the server.

        While we call the AsyncClient class to evaluate what the server is sending to us, we call the messaging
        coroutine to send messages to the server (that the user would like to send).

        There are two types of JSON messages that we send here; the MESSAGES messages, and the BROWSER message.
        the MESSAGES message is a standard message, with a 4 byte unsigned integer prefixed as it's length, which
        is then send to the server (and the messages recipient). BROWSER is a web browser message, which sends
        a message to the server telling it we would like to search for something on the internet
        (we can optionally choose to share our search with others as well, by prefixing with !y instead of !).
        The server then responds, as the client automatically opens the search in their web browser.

        An optional @ sign can be used at the beginning of a message to specify a private recipient for the message;
        if none are chosen, the default is ALL, or all users.

        args:
            loop (obj): loop is the event loop which causes messaging to constantly run,
                        and await for further user input.

        '''
        while True:
            message = yield from loop.run_in_executor(None, input, "")
            if message == 'quit':
                loop.stop()
                return
            if self.connected == 1:
                if message.startswith('@'):
                    space_location = message.find(' ')
                    user_to_send = message[1:space_location]

                    message_data = {"MESSAGES": [(self.user, user_to_send, int(time.time()), message)]}
                    json_data = json.dumps(message_data).encode('ascii')
                    message_len = struct.pack('!I', len(json_data))
                    self.transport.write(message_len + json_data)
                elif message.startswith('!'):
                    if message[1] == 'y':
                        message_data = {"BROWSER": (message[2:], self.user, 1)}
                        json_data = json.dumps(message_data).encode('ascii')
                        message_len = struct.pack('!I', len(json_data))
                        self.transport.write(message_len + json_data)
                    else:
                        message_data = {"BROWSER": (message[1:], self.user, 0)}
                        json_data = json.dumps(message_data).encode('ascii')
                        message_len = struct.pack('!I', len(json_data))
                        self.transport.write(message_len + json_data)
                else:
                    message_data = {"MESSAGES": [(self.user, 'ALL', int(time.time()), message)]}
                    json_data = json.dumps(message_data).encode('ascii')
                    message_len = struct.pack('!I', len(json_data))
                    self.transport.write(message_len + json_data)

def parse_command_line(message):
    '''Called when we need to get args from the command line.

    When the program is invoked with AsyncClient.py (args), those args are parsed through here. There are 6 args
    in total, most of which give message formatting options.

    args:
        message (str): The default help text that the argument parser shows the user at the command line.

    returns:
        list_args (list): list_args returns the user supplied arguments to the program.
                          host and port are grouped together here, so that they may be sent to AsyncClient
                          at the same time with *list_args[0]

    '''
    parser = argparse.ArgumentParser(message)
    parser.add_argument('host', help='Hostname')
    parser.add_argument('-p', metavar='port', type=int, default=1060, help='Port #')
    parser.add_argument('-c', metavar='cafile', type=str, default='ca.crt', help='Cafile location')
    parser.add_argument('-t', metavar='time_on', type=str, default='y', help='Time on? y/n')
    parser.add_argument('-u', metavar='user_on', type=str, default='y', help='User on? y/n')
    parser.add_argument('-s', metavar='space_on', type=str, default='n', help='Extra space on? y/n')
    args = parser.parse_args()
    list_args = ([args.host, args.p], args.c, args.t, args.u, args.s)
    return list_args

if __name__ == '__main__':
    '''
    Here implement the parge_command_line function, create a secure SSL connection with the server,
    and initialize the messsaging() function.
    '''

    address = parse_command_line('Async Client')
    loop = asyncio.get_event_loop()
    client = AsyncClient(address[2], address[3], address[4])

    purpose = ssl.Purpose.SERVER_AUTH
    context = ssl.create_default_context(purpose, cafile=address[1])

    coro = loop.create_connection(lambda: client, *address[0], ssl=context)
    try:
        loop.run_until_complete(coro)
        asyncio.async(client.messaging(loop))
        loop.run_forever()
    finally:
        loop.close()

