import serial
import time
import subprocess

import socket
import select
import time

from AuxFunctions import AuxFunctions
af = AuxFunctions ()

class ArduinoController:

    # Set the IP address and port of the Arduino server
    server_ip = "192.168.1.86"  # Replace with the actual IP address of your Arduino
    #server_ip = "192.168.1.23"  # Replace with the actual IP address of your Arduino
    server_port = 2390
    client_socket = 0
    data_model = 0
    MAGNET_OFF,MAGNET_ON=0,1

    #arduino_port = "COM11"
    arduino_port = "COM4"
    #grbl_port = "COM10"
    #serial_port = 0
    skip = False
    
    screen = 0
    current_pos= 0
    camera = 0

    

    
    def EstablishTCPClient(self):
        
        # Create a socket connection
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))


    def SendToArduinoTCP(self,str):
        
        # Send a string to the server
        print ("Sending Arduino:",str)
        self.client_socket.sendall(str.encode()) # type: ignore

    def ReceiveFromArduinoTCP(self,wait = True):
        #global i
        # Set the socket to non-blocking mode
        self.client_socket.setblocking(0) # type: ignore
        while True:
            # Wait for the socket to become readable
            ready, _, _ = select.select([self.client_socket], [], [], 0.1)  # Timeout set to 1 second
            time.sleep(0.01)
            if ready:
                # Receive the response from the server
                server_response = self.client_socket.recv(1024) # type: ignore
                if not server_response:
                    break  # Connection closed by the server
                print(server_response.decode())
                
                return server_response
            else:
                if wait == False:
                    return None

    def find_controlling_process(self,port_name):
        try:
            result = subprocess.run(['lsof', port_name], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running lsof: {e}")
            return None
    
    def __init__(self,screen,data_model):
        self.data_model = data_model
        if not self.data_model.disable_robot:
            self.EstablishTCPClient() 

        self.screen = screen

    def CheckConfirmtionTCPNoWait(self):
        ret_val = False
        stop_wait = False

        #ret = self.ReceiveFromArduinoTCP(wait = False).decode()
        ret = self.ReceiveFromArduinoTCP(wait = False)
        if ret == None:
            return ret_val,stop_wait
        ret = ret.decode()
        if ret.startswith("OK"):
            print ("Received OK")
            stop_wait = True
            ret_val = False
        if ret.startswith("ALARM"):
            print("Alarm during WaitForConfirmationTCP")
            #time.sleep(0.5)
            #self.Home()
            stop_wait = True
            ret_val = True
        return ret_val,stop_wait

    def WaitForConfirmationTCP(self):
        stop_wait = False
        ret_val = False
        while (not stop_wait):
            ret_val,stop_wait = self.CheckConfirmtionTCPNoWait()
        return ret_val

    """def WaitForConfirmationTCP(self):
        stop_wait = False
        while (not stop_wait):
            ret = self.ReceiveFromArduinoTCP().decode()
            if ret.startswith("OK"):
                print ("Received OK")
                stop_wait = True
                return False
            if ret.startswith("ALARM"):
                print("Alarm during WaitForConfirmationTCP")
                #time.sleep(0.5)
                #self.Home()
                stop_wait = True
                return True"""



    """def WaitForConfirmation(self):
        received = False
        while received == False:
            self.camera.TakeDiceSnapshot()
            self.screen.ShowWindows()
            try:
                if self.serial_port.in_waiting > 0:
                    #received_data = self.serial_port.readline().decode().strip()
                    received_data = self.serial_port.read(self.serial_port.in_waiting)
                    received_data = received_data.decode('utf-8')
                    if received_data == "OK":
                        received = True
                    print(f"Received: {received_data}")
            except Exception as e:
                controlling_process = self.find_controlling_process(self.arduino_port)
                if controlling_process:
                    print(f"The process controlling {self.arduino_port}:\n{controlling_process}")
                else:
                    print(f"No information found for {self.arduino_port}")
                #self.InitCommunication()"""
            

    """def InitSerialCommunication(self):
        pass"""




    def RollDice(self):
        self.SendToArduinoTCP("Roll")
        self.WaitForConfirmationTCP()

    def MagnetOn(self):
        self.SendToArduinoTCP("MagnetOn") 
        self.WaitForConfirmationTCP()
        self.magnet_state = self.MAGNET_ON


    def MagnetOff(self):
        self.SendToArduinoTCP("MagnetOff")
        self.WaitForConfirmationTCP()
        self.magnet_state = self.MAGNET_OFF

    def CheckAlarm(self):
        self.SendToArduinoTCP("CheckAlarm")
        return self.WaitForConfirmationTCP()
    def Home(self):
        self.SendToArduinoTCP("Home")
        self.WaitForConfirmationTCP()
    def ShowText(self):
        pass

    def WaitForPlayer(self):
        self.SendToArduinoTCP("MagnetOff")
        self.WaitForConfirmationTCP()

    def SendCommand(self,command,wait = True):
        if (self.data_model.disable_robot):
            pass
            #time.sleep(5)
        else:
            self.SendToArduinoTCP(command)
            if wait == True:
                self.WaitForConfirmationTCP()

    def MoveTo(self,pos):
        move_command = "GRBL:G0 X{:.2f} Y{:.2f}".format(pos[0], pos[1])
        continue_send = True
        while continue_send == True:
            self.SendToArduinoTCP(move_command)
            continue_send = self.WaitForConfirmationTCP() #repeat the command, since ALARM was encountered
            if continue_send == True: # alarm was encountered - perform Home
                self.Home()
        
        self.current_pos = pos
    
    def ManeuverTo(self,pos):
        move_command = "GRBL:G1 X{:.2f} Y{:.2f} F400".format(pos[0], pos[1])
        continue_send = True
        while continue_send == True:
            self.SendToArduinoTCP(move_command)
            continue_send = self.WaitForConfirmationTCP() #repeat the command, since ALARM was encountered
            if continue_send == True: # alarm was encountered - perform Home
                while(True):
                    pass
        
        self.current_pos = pos
