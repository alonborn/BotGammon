from ast import Assert
from AuxFunctions import AuxFunctions
import cv2

af = AuxFunctions ()

class BoardSimulation:
    camera = 0
    data_model = 0
    board = 0

    def __init__(self,camera,data_model,board) -> None:
        self.camera= camera
        self.data_model = data_model
        self.board = board

    # %Move:G0 X100 Y100%Magnet:1:30:X:150% --> move to x100 y100. when x reaches 150 - start to move magnet (slowly =1) to 30
    # %Move:G0 X100 Y100%Magnet:2:30:Y:150% --> move to x100 y100. when y reaches 150 - start to move magnet (quickly =2)to 30
    # %Magnet:60% --> move magnet to 60
    # %MagnetOn% - turn magnet on 
    # %MagnetOff% - turn magnet off
    # %Move:G0 X100 Y100 F120%Magnet:120% --> move to x100 y100 and move magnet to 120
    # %Move:G0 x100 y100% -->move to x100 y100
    
    def ExtractCommand(self,command):
        movement = 0
        magnet_servo_angle = -1
        magnet_switch_on_off = -1  
        magnet_starts_at = 0
        if "%" in command:
            subcommands = command.split('%')
        else:
            subcommands = [command]
        for subcommand in subcommands:
            if subcommand.startswith("Move:"):
                strings = subcommand.split(":")
                movement = strings[1]
            if subcommand.startswith("Magnet:"):
                strings = subcommand.split(":")
                magnet_servo_angle = self.GetAngleCode (int(strings[2]))
                if len(strings) > 3:    #if to start moving the servo at some location
                    magnet_starts_at = strings[3] +":" + strings[4]

            if subcommand.startswith("MagnetOn"):
                magnet_switch_on_off = self.board.MAGNET_ON
            if subcommand.startswith("MagnetOff"):
                magnet_switch_on_off = self.board.MAGNET_OFF                
        return movement,magnet_servo_angle,magnet_switch_on_off,magnet_starts_at
    

    def SplitMovement(self,image,cur_pos,end_pos,new_servo_angle_code,magnet_starts_at,servo_angle_code):
        parts = magnet_starts_at.split(":")
        split_direction = parts[0]  #X or Y

        split_point = float(parts[1]) 

        cur_pos_mach = self.camera.GetMachineCoords(cur_pos)
        end_pos_mach = self.camera.GetMachineCoords(end_pos)

        mid_pos = 0

        if split_direction == 'X':
            split_point_y_mach = af.FindYForX(cur_pos_mach,end_pos_mach,split_point)
            mid_pos = self.camera.GetScreenCoords((split_point,split_point_y_mach))  
            if not (cur_pos[0]-2<=mid_pos[0] <= end_pos[0]+2) and not (end_pos[0]-2<=mid_pos[0] <= cur_pos[0]+2):
                return False #the mid point is not along the path
        else:
            split_point_x_mach = af.FindXForY(cur_pos_mach,end_pos_mach,split_point)
            mid_pos = self.camera.GetScreenCoords((split_point_x_mach,split_point))  
            if not (cur_pos[1]-1<=mid_pos[1] <= end_pos[1]+1) and not (end_pos[1]-1<=mid_pos[1] <= cur_pos[1]+1):
                return False #the mid point is not along the path

        if image is not None:
            cv2.line(image,cur_pos,mid_pos, self.GetLineColor(servo_angle_code), 2)
            cv2.line(image,mid_pos,end_pos, self.GetLineColor(new_servo_angle_code), 2)
        else:
            if self.CheckIfHeadCollides(cur_pos,mid_pos,servo_angle_code):
                return False
            if self.CheckIfHeadCollides(mid_pos,end_pos,servo_angle_code):
                return False
        return True
    
    #start_pos in machine coordinates
    #checks if command is safe, and return the end values of the board parameters
    def ProcessCommand(self,commands,start_pos,magnet_height,magnet_signal):
        success,end_pos,servo_angle_code,magnet_signal = self.DrawCommand(None,commands,start_pos,magnet_height,magnet_signal)
        return success,end_pos,servo_angle_code,magnet_signal

    def CheckIfHeadCollides(self,cur_pos_scr,end_pos_scr,servo_angle_code):
        if (servo_angle_code == self.board.UP or servo_angle_code == self.board.BAR):
            return False
        line = [cur_pos_scr, end_pos_scr]
        if af.DoLinesIntersect(line, self.board.camera.board_left_rect):
            return True
        if af.DoLinesIntersect(line, self.board.camera.board_right_rect):
            return True
        return False


    #start_pos in machine coordinates
    def DrawCommand(self,image,commands,start_pos,servo_angle_code_in,magnet_signal_in):
        #commands = self.data_model.command
        if commands == 0:
            return True,0,0,0
        movement = 0
        ret_val_magnet_signal = magnet_signal_in
        if commands =="":
            return True,0,0,0
        cur_pos = start_pos
        cur_pos = self.camera.GetScreenCoords(cur_pos)
        servo_angle_code = servo_angle_code_in   
        split_commands = commands.split('^')
        cur_command = None if self.data_model.max_subcommand == 0 else self.data_model.max_subcommand
        #image = af.TextToImage(image,split_commands,(600,400), highlighted_line=cur_command, n=None)
        current_subcomand = 0
        for command in split_commands:
            if image is not None and self.data_model.max_subcommand >= 0 and current_subcomand > self.data_model.max_subcommand:
            #if image is None and self.data_model.max_subcommand == -1 and (current_subcomand >= 0 and current_subcomand > (self.data_model.max_subcommand)):
                return True,0,0,0

            movement,new_servo_angle_code,magnet_switch_on_off,magnet_starts_at = self.ExtractCommand(command)
            if magnet_switch_on_off!= -1:
                ret_val_magnet_signal = magnet_switch_on_off
            if movement != 0:
                end_pos_mach,frate = af.ExtractGCodeValues(movement)
                end_pos_scr = self.camera.GetScreenCoords(end_pos_mach)
                if (magnet_starts_at == 0):
                    if image is not None:
                        cv2.line(image,cur_pos,end_pos_scr, self.GetLineColor(servo_angle_code), 2)
                    if self.CheckIfHeadCollides(cur_pos,end_pos_scr,servo_angle_code):
                        return False,0,0,0
                else:
                    
                    if (self.SplitMovement(image,cur_pos,end_pos_scr,new_servo_angle_code,magnet_starts_at,servo_angle_code)  == False):
                        return False,0,0,0
                    servo_angle_code = new_servo_angle_code
                cur_pos = end_pos_scr

            if new_servo_angle_code != -1:
                servo_angle_code = new_servo_angle_code
            current_subcomand+=1
        return True,self.camera.GetMachineCoords(cur_pos),servo_angle_code,ret_val_magnet_signal

    def GetMagnetHeight(self, magnet_angle):
        magnet_height = -1
        if magnet_angle == self.board.magnet_angle_up:
            magnet_height = self.board.UP
        if magnet_angle == self.board.magnet_angle_down:
            magnet_height = self.board.DOWN
        if magnet_angle == self.board.magnet_angle_maneuver:
            magnet_height = self.board.MANOUVER
        if magnet_angle == self.board.magnet_angle_bar:
            magnet_height = self.board.BAR
        if magnet_angle == self.board.magnet_angle_hover:
            magnet_height = self.board.HOVER
        return magnet_height
    
    def GetLineColor (self,magnet_height):
        if magnet_height == self.board.UP:  #black
            return (0,0,0)  
        if magnet_height == self.board.DOWN:    #white
            return (255,255,255)
        if magnet_height == self.board.MANOUVER: #Red
            return (0,0,255)
        if magnet_height == self.board.BAR:    #green
            return (0,255,0)
        if magnet_height == self.board.HOVER:    #green
            return (255,0,0)
        
    def GetAngleCode(self,angle):
        if angle == self.board.magnet_angle_up:  #black
            return self.board.UP 
        if angle == self.board.magnet_angle_down:    #white
            return self.board.DOWN
        if angle in (self.board.magnet_angle_maneuver,self.board.magnet_angle_maneuver-1,self.board.magnet_angle_maneuver-2) : #Red
            return self.board.MANOUVER
        if angle == self.board.magnet_angle_bar:    #green
            return self.board.BAR  
        assert False