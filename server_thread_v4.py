
from bluetooth import *
import threading
from Queue import *
import json
import time
server_queue_send = Queue()
server_queue_recieve = Queue()
my_address="00:1A:7D:DA:71:13"
import os
#Create a dictionary for storing the threads for each device
#devices = {"00:1A:7D:DA:71:13":"piserv", "00:1A:7D:DA:71:14":"pi3", "00:1A:7D:DA:71:16":"pi2" }
#dict = {"destination": dest, "data": message}
#data=("00:1A:7D:DA:71:16", "Hai, hai")  #just seldom packet to test
#server_queue_send.put(data)             #put the tupple to the que
class update_queue(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        while True:
            self.data_in = raw_input("Type-in data to send \n")
            if (len(self.data_in) > 0):
                if (self.data_in == "exit"):
                    print("Exiting update_queue()..")
                    exit(0)
                self.data_list=("00:1A:7D:DA:71:16", self.data_in) 
                server_queue_send.put(self.data_list)
                print("Queue updated")
            
class echoThread(threading.Thread):
    def __init__(self, client_sock, client_info):
        threading.Thread.__init__(self)
        self.client_sock=client_sock    #this is the client socket
        self.client_info=client_info    #client bluetooth address
        self.destination=None           #destination address
        self.data=None                  #actual data to be sent
        self.item_to_send=None          #the dictionary containing the data to be sent
        

    def decode_queue(self):
        self.destination=self.item_to_send[0]
        self.data=self.item_to_send[1]

    def send_data(self):
        self.item_to_send = server_queue_send.get()
        self.decode_queue()
        print(self.destination)
        print(self.client_info)
        if self.destination == self.client_info[0]:
            self.data_serialized=json.dumps(self.item_to_send).encode('utf-8')
            self.client_sock.send(self.data_serialized)
            print("data sent")   
        else:
            server_queue_send.put(self.item_to_send)
            print("data not sent")

    def run(self):
        try:
            while True:
                self.send_data()
        except IOError:
            pass

        self.client_sock.close()
        print (self.client_info, ": disconnected")

class receiveThread(threading.Thread):
    def __init__(self, client_sock, client_info):
        threading.Thread.__init__(self)
        self.client_sock=client_sock    #this is the client socket
        self.client_info=client_info    #client bluetooth address
        self.recieved_item=None         #the tupple containing the recieved data
    
    def decode_queue(self):
        self.destination=self.recieved_item[0]
        self.data=self.recieved_item[1]
            
    def receive_data(self):
        b=b''
        self.recieved_item_ns=self.client_sock.recv(1024)
        b+=self.recieved_item_ns
        self.recieved_item=json.loads(b.decode('utf-8'))
        print "recieved: " 
        self.decode_queue()
        if (self.destination==my_address):
            print(self.client_info, self.recieved_item)
        else:
            servere_queue_send.put(self.recieved_item)
        
    def run(self):
        try:
            while True:
                self.receive_data()
               
        except IOError:
            pass
            
        self.client_sock.close()
        print(self.client_info, "disconnected")
        
class bluetooth_server(threading.Thread):
    def __init__(self):
        super(bluetooth_server, self).__init__()
        self.name = "BluetoothChat"
        self.uuid = "fa87c0d0-afac-11de-8a39-0800200c9a66"
        

    def run(self):
        #Create a socket for the server
        server_sock=BluetoothSocket(RFCOMM)

        #Bind the devices
        server_sock.bind(("",PORT_ANY))

        #Listen for incoming connections
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        #uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        #uuid="1e0ca4ea-299d-4335-93eb-27fcfe7fa848"

        #Advertise the server service
        advertise_service( server_sock, self.name, self.uuid)
        os.system("sudo hciconfig hci0 piscan")  #Makes the device discoverable
        print("Waiting for connection on RFCOMM channel %d \n" % port)
        queue = update_queue()
        queue.setDaemon(True)
        queue.start()
        
        while True:
            os.system("sudo hciconfig hci0 piscan")  #Makes the device discoverable
            client_sock, client_info=server_sock.accept()
            send=echoThread(client_sock, client_info)
            receive=receiveThread(client_sock, client_info)
            print (client_info, ": connection accepted \n")
            send.setDaemon(True)
            receive.setDaemon(True)
            send.start()
            receive.start()
            

server=bluetooth_server()
server.setDaemon(True)
server.start()

while True:
    ar=True 