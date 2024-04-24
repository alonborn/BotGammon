import ArduinoController
import DataModel
import re
import json
import cv2
from AuxFunctions import AuxFunctions 
import time
import numpy as np

af = AuxFunctions()

class BoardController:

    data_model = 0
    arduino = 0
    camera = 0
    UP,BAR,HOVER,MANOUVER,DOWN = 0,1,2,3,4
    MAGNET_OFF,MAGNET_ON = 0,1

    magnet_angle_code = UP
    magnet_state = MAGNET_OFF
    current_position = (0,0)    #machine coordinates

    FEED_AT_MANEUVER = 400
    FEED_AT_HOVER = 400
    magnet_angle_up = 0
    magnet_angle_down = 68
    magnet_angle_bar = 45
    magnet_angle_maneuver = 60

    home_position =(0,100)  #machine coordinates

    MOVEMENT_UP,MOVEMENT_DOWN = 0,1
    MAGNET_COMMAND_PREFIX = "Magnet:"

    #which section of the board the magnet is (helps to calculate the changing of magnet eight during movement)
    BOARD_SECTION_HOME,BOARD_SECTION_LEFT,BOARD_SECTION_BAR,BOARD_SECTION_RIGHT = 0,1,2,3

    #CALIBRATION_POS_X = 240
    #CALIBRATION_POS_X = 40
    CALIBRATION_POS_Y = 220

    cur_calibration_point = 0
    sim_mode = True
    def __init__(self,data_model,arduino) -> None:
        self.data_model = data_model
        self.arduino = arduino
        if not data_model.disable_robot:
            self.SendHomeCommand()     #XXXXXXXXXXXXXXXXXXXX
            pass

        
        #self.arduino.MoveTo((self.CALIBRATION_POS,self.CALIBRATION_POS))

    def ToDictionary(self):
        return {
            'magnet_angle_up': self.magnet_angle_up,
            'magnet_angle_down': self.magnet_angle_down,
            'magnet_angle_bar': self.magnet_angle_bar,
            'magnet_angle_maneuver': self.magnet_angle_maneuver,
        }

    @classmethod
    def FromDictionary(cls,data_model,arduino,data):
        ret_val = cls(data_model,arduino)
        ret_val.magnet_angle_up = data['magnet_angle_up']
        ret_val.magnet_angle_down = data['magnet_angle_down']
        ret_val.magnet_angle_bar = data['magnet_angle_bar']
        ret_val.magnet_angle_maneuver = data['magnet_angle_maneuver']
        return ret_val
    
    def SaveToFile(self):
        success = 0
        while success == 0:
            try:
                with open("BoardController.json", "w") as file:
                    json.dump(self.ToDictionary(), file) 
                success = 1
            finally:
                    pass
            time.sleep (1)

    def MoveToOrigin(self):
        commands = []
        commands.append(self.GetMagnetUpCommand(2))
        commands.append(self.GetMoveToCommand((0,0)))
        commands = af.ConcatenateCommand(commands)
        self.SendCommand(commands)

    def MoveMagnetToTest(self,pos_type):
        commands = []
        commands.append(self.GetMagnetUpCommand(2))
        new_point = 0,0
        if pos_type == 1:
            new_point = self.camera.point_mach[3]
        commands.append(self.GetMoveToCommand(new_point))

        commands = af.ConcatenateCommand(commands)
        self.SendCommand(commands)
    
    
    def MoveMagnetAwayInCalibration(self,pos_type):
        commands = []
        commands.append(self.GetMagnetUpCommand(2))
        new_point = 0,0
        if pos_type > 0:
            new_point = self.camera.point_mach[pos_type-1]
        commands.append(self.GetMoveToCommand(new_point))

        commands = af.ConcatenateCommand(commands)
        self.SendCommand(commands)
            
        

    def GetMagnetOnCommand(self):
        return "MagnetOn"
    def GetMagnetOffCommand(self):
        return "MagnetOff"
        
    
    def ToggleMagnetState(self):
        commands = []

        if self.magnet_state == self.MAGNET_ON:
            commands.append(self.GetMagnetOffCommand())
        else:
            commands.append(self.GetMagnetOnCommand())
        commands = af.ConcatenateCommand(commands)
        self.SendCommand(commands)
    
    def HandleRollDice(self):
        pass
        """self.arduino.RollDice()"""

    def PlayNextMove(nextMove):
        # Use regular expression to extract numbers and split them into pairs
        numbers = re.findall(r'\d+', nextMove)
        number_pairs = [numbers[i:i+2] for i in range(0, len(numbers), 2)]

        print(number_pairs)

    def GetMagnetDownCommand(self,speed = 1):
        return "Magnet:"+ str(speed) + ":" + str(self.magnet_angle_down)   
     
    def GetMagnetUpCommand(self,speed = 1):
        return "Magnet:"+ str(speed) + ":" + str(self.magnet_angle_up)  
    
    def GetMagnetManeuverCommand(self,adjust_maneuver_height=0):
        return "Magnet:1:"+ str(self.magnet_angle_maneuver + adjust_maneuver_height)   

    def GetMagnetHoverCommand(self):
        return "Magnet:2:"+ str(self.magnet_angle_maneuver)     #hover is like maneuver without checker attached
    
    def GetWaitForPlayerCommand(self):
        return "WaitForPlayer"
    
    def GetMagnetBarCommand(self,speed = 1):
        return "Magnet:"+ str(speed) + ":" + str(self.magnet_angle_bar)    

    def SendTextCommand(self,text):
        self.SendCommand("RGB:TEXT:" + text)

    def MagnetDown(self):
        self.SendCommand(self.GetMagnetDownCommand(2))

    def MagnetUp(self):
        self.SendCommand(self.GetMagnetUpCommand(2))

    def MagnetBar(self):
        self.SendCommand(self.GetMagnetBarCommand())


    def MagnetManeuver(self):
        self.SendCommand(self.GetMagnetManeuverCommand())

    def MagnetHover(self):
        self.SendCommand(self.GetMagnetHoverCommand())

    def WaitForPlayer(self, wait_for_refresh):
        self.arduino.SendCommand(self.GetWaitForPlayerCommand(),wait = False)
        stop_wait = False
        refresh_count = 0
        while stop_wait == False and (wait_for_refresh == False or refresh_count >= 40):
            self.camera.GetBoardPlayers()
            self.camera.screen_controller.PrepareWindows()
            self.camera.screen_controller.ShowWindows()
            _,stop_wait = self.arduino.CheckConfirmtionTCPNoWait()
            refresh_count +=1


    
    def ManeuverTo(self,pos):
        """self.CheckAlarm()
        
        if self.magnet_position != self.MANOUVER:
            print ("Cannot move while magnet is not maneuver")
            return
        if self.data_model.IsMovementAllowed(pos) == False:
            print ("Movement to position " + str(pos) + " is not allowed")
            return
        
        if pos[0] < 0:
            pos = (0,pos[1])
        if pos[1] < 0:
            pos= (pos[0],0)

        self.arduino.ManeuverTo(pos)"""

    """def f(self,pos,feed =0):
        if pos[0] < 0:
            pos = (0,pos[1])
        if pos[1] < 0:
            pos= (pos[0],0)
        move_command = "GRBL:G0 X{:.2f} Y{:.2f}".format(pos[0], pos[1])
        if feed!=0:
            move_command += " F" + feed
        return move_command"""

    def MoveTo(self,pos):
        #self.CheckAlarm()
        
        """if self.magnet_position != self.UP:
            print ("Cannot move while magnet is not up")
            return
        if self.data_model.IsMovementAllowed(pos) == False:
            print ("Movement to position " + str(pos) + " is not allowed")
            return"""
        
        if pos[0] < 0:
            pos = (0,pos[1])
        if pos[1] < 0:
            pos= (pos[0],0)
        self.SendCommand(self.GetMoveToCommand(pos))
        #self.arduino.MoveTo(pos)

    def HandleMagnetServoPos(self, delta):
        if self.magnet_angle_code == self.UP:
            self.magnet_angle_up +=delta
            self.MagnetUp()
        if self.magnet_angle_code == self.DOWN:
           self.magnet_angle_down +=delta
           self.MagnetDown()
        if self.magnet_angle_code == self.BAR:
            self.magnet_angle_bar +=delta
            self.MagnetBar()
        if self.magnet_angle_code == self.MANOUVER:
            self.magnet_angle_maneuver +=delta
            self.MagnetManeuver()

        self.SaveToFile()
    def CheckAlarm(self):
        if (self.arduino.CheckAlarm() == True):
            print ("Alarm was encountered, performing Home")
            self.arduino.Home()

    def GetMoveToCommand (self,pos,f = -1):
        if pos[0] > 293 or pos[1] > 254 or pos[0] < 0 or pos[1] < 0:
            print ("ERROR: Exceeding machine coordinates!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            while False:
                pass
        formatted_x = "{:.2f}".format(pos[0])
        formatted_y = "{:.2f}".format(pos[1])
        command = "Move:G0 X{} Y{}".format(formatted_x, formatted_y)
        
        """if f!= -1:
            command += " F" + str (f)"""
        return command

    #for debug purposes
    def draw_rectangles_on_image(self,image, rectangles):
        # Create a copy of the image to draw on
        image_with_rectangles = image

        # Draw rectangles on the image
        for rect in rectangles:
            pt1 = (int(rect[0]), int(rect[1]))
            pt2 = (int(rect[2]), int(rect[3]))
            color = (0, 255, 0)  # Green color for rectangles (BGR format)
            thickness = 2  # Thickness of the rectangle border
            image_with_rectangles = cv2.rectangle(image_with_rectangles, pt1, pt2, color, thickness)

        return image_with_rectangles
    
    #get rectangles of all columns checkers, except given column
    def GetColumnRectangle(self,column):
        checker_rad = self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[0]

        centers_of_checkers = self.data_model.all_checkers[column]
        if centers_of_checkers!= []:
            return af.GetBoundingRectangle(centers_of_checkers,checker_rad)
        return None

    

    #add command for raching pick maneuver and then, move to checker and pick it up
    #change_to_maneuver - whether to move magnet to maneuver position
    def GetTargetPickManeuverCommand(self,target,change_to_maneuver):
        pass

    #once the checker is picked up, return which columns interfering on its way to target, based on their checkers
    def AreColumnsColiding(self,cur_pos,origin,target):
        
        checker_rad = self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[0]
        target_point = self.camera.CalculatePutManeuverPoint(cur_pos,target,0)

        #all columns in origin and target quadrants, excluding the origin and target columns
        columns_under_test = list(set(af.GetQuadrantColumns(origin)))
        columns_under_test.extend(list(set(af.GetQuadrantColumns(target))))

        columns_under_test = list(set(columns_under_test))

        circles_under_test = [pos for column in columns_under_test for pos in self.data_model.all_checkers[column]]

        circles_along_the_path = af.generate_internal_points(cur_pos,target_point,15)

        show = False
        colliding_columns = []
    
        if show == True:    #debugging purposes
            import numpy as np
            height, width = 900,1300
            img = np.zeros((height, width, 3), dtype=np.uint8)

            af.draw_circles(img,circles_along_the_path,checker_rad,(200,0,200))
            af.draw_circles(img,circles_under_test,checker_rad,(0,200,0))
            
            cv2.circle(img, (int(cur_pos[0]),int(cur_pos[1])), 3, (200,0,200), thickness=cv2.FILLED)
            cv2.circle(img, (int(target_point[0]),int(target_point[1])), 3, (200,0,200), thickness=cv2.FILLED)
            cv2.imshow('Line', img)
            cv2.waitKey(0)
                
        if af.circles_intersect(circles_along_the_path,circles_under_test,checker_rad):
            return True

        return False
    
    #cur_pos,dest_pos in screen coordinates
    #return value in machine coordinates
    def CalculateXPosForMagnetServoMovement(self,cur_pos,dest_pos):
        checker_rad = self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[0]
        tolerance = checker_rad + 0.7 * self.camera.mm_tolerance
        x_boundaries = [self.camera.board_left_rect[0][0]+tolerance,self.camera.board_left_rect[1][0]-tolerance,self.camera.board_right_rect[0][0]+tolerance]
        furthest_point = af.FindFurthestPointFromPoint1(cur_pos,dest_pos,x_boundaries)

        if furthest_point:
            return self.camera.GetMachineCoords(furthest_point)[0]
        return None

    def GetMoveAndRotateCommand(self,move_command,target_angle,direction,start_servo_from,magnet_speed):
        command = "%{}%{}{}:{}:{}:{:.2f}%".format(move_command, self.MAGNET_COMMAND_PREFIX, magnet_speed,target_angle,direction, start_servo_from)
        return command

    #add command for raching target checker and then,attach it to magnet 
    #start_from - screen coordinates
    #allow_move_rotate - there are cases when the descent during move is only delaying the maneuver, so it should be possible to skip it. 
    def GetPickHoverCommand(self,target_scr,start_from,allow_move_rotate):
        start_servo_from = 0
        #on the way from 0,0 to the pick column - check if we cross only th left rectangle or the right one as well:

        start_servo_from = self.CalculateXPosForMagnetServoMovement(start_from, target_scr)

        target_mach_coords = self.camera.GetMachineCoords(target_scr)
        start_from_mach = self.camera.GetMachineCoords(start_from)

        command = []
        move_command = self.GetMoveToCommand(target_mach_coords) 
        if allow_move_rotate and (start_servo_from != None and (start_from_mach[0] < start_servo_from < target_mach_coords[0] or
            target_mach_coords[0] < start_servo_from < start_from_mach[0])):  #there are some situations (like near borders) where the start from is not with path
            command.append(self.GetMoveAndRotateCommand(move_command,self.magnet_angle_maneuver,"X",start_servo_from,2))
        else:   #if there's no point to do both together
            command.append(move_command)
        return command

    #checks if it should decent on it's way to the put-maneuver point
    def ShouldDecentToPutManeuver(self,cur_pos,from_col,to_col):
        if from_col in (25,26,27) or not af.AreColumnsSameHalf(from_col,to_col) :  #bar or home
            return False

        if af.AreColumnsSameQuadrant(from_col,to_col) and self.AreColumnsColiding(cur_pos,from_col,to_col):    #only if moving within a quadrant and path is not free
        #if af.AreColumnsSameQuadrant(from_col,to_col):     
            return False
        if af.AreColumnsSameHalf(from_col,to_col) and self.AreColumnsColiding(cur_pos,from_col,to_col):
            return False
        return True 

    def CalculateDescendingPointAfterBar(self,cur_pos,to_col):
        checker_rad = self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[0]
 

        #check if it is needed to go to maneuver position before picking the checker
        end_point = self.camera.CalculatePutManeuverPoint(cur_pos,to_col,0)
        if end_point == 0:   #if yes, go to maneuver before picking the checker
            end_point =  self.camera.GetNextSpot(to_col)

        retval =[0,0]
        bar_borders = [self.camera.board_left_rect[1][0]-checker_rad,self.camera.board_right_rect[0][0]+checker_rad]
        retval[0] = max(bar_borders, key=lambda x: abs(x - cur_pos[0]))

        retval[1] = af.FindYForX(cur_pos,end_point,retval[0])

        return retval

    #if same quadrant - start descent immediately, otherwise, check for the last checker
    def CalculateDescendingPoint(self,from_col,to_col):
        checker_rad = self.data_model.CHECKER_RADIUS / self.camera.mmperpixel[0]

        if af.AreColumnsSameQuadrant(from_col,to_col):
            return self.data_model.GetLastChecker(from_col)[0]    #return the X value of the last checker
        else:
            columns = list(af.GetQuadrantColumns(from_col))
            columns.remove(from_col)
            last_checkers = [self.data_model.GetLastChecker(col) for col in columns]
            last_checkers = [item for item in last_checkers if item is not None]
            if last_checkers == []:
                return -10  #return a very small value, so that descent will start immediately
            if af.GetColumnSide(from_col) == 0: #bottom side
                return min(last_checkers,key=lambda point: point[1])[1] - checker_rad
            else:
                return max(last_checkers,key=lambda point: point[1])[1] + checker_rad

    #creates the command for moving to the put-maneuver point. Assumption - head is at pick location, playing in one half    
    #cur_pos = screen coordinates
    def GetMoveToPutManeuverCommand(self,from_col,to_col,cur_pos, keep_magnet_on):
        commands = []

        if to_col in (26,27):    #home
            return commands
        #go  to the checker position 
        put_maneuver_point = self.camera.CalculatePutManeuverPoint(cur_pos,to_col,0)
        put_maneuver_point_mach_coords = self.camera.GetMachineCoords(put_maneuver_point)
        move_command = self.GetMoveToCommand(put_maneuver_point_mach_coords)

        should_descent = self.ShouldDecentToPutManeuver(cur_pos,from_col,to_col)
        

        if keep_magnet_on == True: #no reason to descent if eventually moving to next target position
            should_descent = False
        if should_descent:
            #check when to start moving the magnet to maneuver point (depending on the blocking columns)
            head_position = self.camera.GetMachineCoords(cur_pos)
            if (not af.AreColumnsSameHalf(from_col,to_col)):
                direction = 'X'
                start_angle_from = self.CalculateDescendingPointAfterBar(cur_pos,to_col)
                

                if af.IsBeforeStart(start_angle_from[0],cur_pos[0],put_maneuver_point[0]):
                    start_angle_from = cur_pos
                else:
                    if af.IsAfterEnd(start_angle_from[0],cur_pos[0],put_maneuver_point[0]):
                        should_descent = False

                start_angle_from = self.camera.GetMachineCoords(start_angle_from)[0]
            else:
                if (af.AreColumnsSameQuadrant(from_col,to_col)):
                    direction = 'X'
                    start_angle_from = head_position[0]    #if same quadrant- start immediately descending
                else:   #not the same quadrant - opposite to each other
                    direction = 'Y'
                    start_angle_from = self.CalculateDescendingPoint(from_col,to_col)   #screen  coords
                    x_along_line = af.FindXForY(cur_pos,put_maneuver_point,start_angle_from) #screen  coords
                    start_angle_from = self.camera.GetMachineCoords((x_along_line,start_angle_from))
                    start_angle_from = start_angle_from[1]

                    #if mid point is not along path - dont descend
                    if af.IsBeforeStart(start_angle_from,head_position[1],put_maneuver_point_mach_coords[1]):
                        start_angle_from = head_position[1]
                    else:
                        if af.IsAfterEnd(start_angle_from,head_position[1],put_maneuver_point_mach_coords[1]):
                            should_descent = False
        adjust_maneuver_height = 0  # the table is not completely horizontal. the 3rd quarter (12-17) is a bit higher, so maneuver should be higher
        if 12 <= to_col <=23:
            adjust_maneuver_height = -2
            #print ("adjusting put maneuver")

        if should_descent:
            commands.append(self.GetMoveAndRotateCommand(move_command,self.magnet_angle_maneuver+adjust_maneuver_height,direction,start_angle_from,1))
        else:   #if cant descend- just move to the put position and then down to maneuver
            commands.append(move_command)
            if keep_magnet_on == False:  #do not descent if moving to next target position
                commands.append(self.GetMagnetManeuverCommand(adjust_maneuver_height))

        if keep_magnet_on == False:
            put_maneuver_point2 = self.camera.CalculatePutManeuverPoint(cur_pos,to_col,1)
            if put_maneuver_point2 != None:
                head_position = self.camera.GetMachineCoords(put_maneuver_point2)
                commands.append(self.GetMoveToCommand(head_position,self.FEED_AT_MANEUVER))


        return commands
                
      
    #if pos is too close to the border - take an offset of 1 mm
    #pos - mach coord

    def AdjustLandingSpotToBorders(self,from_col,pos):
        magnet_rad = self.data_model.MAGNET_RADIUS / self.camera.mmperpixel[1]
        tolerance_x = (2*self.camera.mm_tolerance) / self.camera.mmperpixel[0] + magnet_rad
        tolerance_y = (2*self.camera.mm_tolerance) / self.camera.mmperpixel[1] + magnet_rad

        rect = self.camera.board_right_rect if af.GetQuadrant(from_col) in (0,3) else self.camera.board_left_rect
            
        pos = (max(rect[0][0]+tolerance_x,pos[0]),max(rect[0][1]+tolerance_y,pos[1]))
        pos = (min(rect[1][0]-tolerance_x,pos[0]),min(rect[1][1]-tolerance_y,pos[1]))

        pos = self.camera.GetMachineCoords(pos)
        return pos
            
    def IsRetreatNeeded(self,from_col):
        if from_col in (0,5,6,11,12,17,18,23):
            return True
        if len(self.data_model.all_checkers[from_col]) == 1:
            return True
        return False

    def PickupChecker(self, from_col,start_from,color):
        command = []

        if (color == 'w' and from_col == 26) or color == 'b' and from_col == 25:    # pick from bar
            pos = self.data_model.GetBarChecker(color)
            pos_mach = self.camera.GetMachineCoords(pos)
            command.append(self.GetMoveToCommand(pos_mach))
            command.append(self.GetMagnetBarCommand())
            command.append(self.GetMagnetOnCommand())
            command.append(self.GetMagnetUpCommand())
            return command,pos

        checker_pos_scr = self.data_model.GetLastChecker(from_col)
        checker_pos_mach = self.camera.GetMachineCoords(checker_pos_scr)

        #check if it is needed to go to maneuver position before picking the checker
        pick_maneuver_point = self.camera.CalculatePickupHoverPoint(from_col) 
        if pick_maneuver_point != None:   #if yes, go to maneuver before picking the checker
            new_command = self.GetPickHoverCommand(pick_maneuver_point,start_from,True)
            command.extend(new_command) 
            #checker_pos_mach = self.AdjustLandingSpotToBorders(from_col,checker_pos_mach)
            checker_pos_mach = self.AdjustLandingSpotToBorders(from_col,checker_pos_scr)
            command.append(self.GetMagnetHoverCommand())
            command.append(self.GetMoveToCommand(checker_pos_mach,self.FEED_AT_MANEUVER))
        else:
            command.extend(self.GetPickHoverCommand(checker_pos_scr,start_from,False))
            #command.extend(self.GetPickHoverCommand(checker_pos_scr,start_from))
            pass
        #move to the origin checker
        #command.append(self.GetMoveToCommand(origin_mach))
        cur_pos  = checker_pos_mach
        command.append(self.GetMagnetDownCommand())
        command.append(self.GetMagnetOnCommand())

        #handle 'retreat' maneuver:
        if self.IsRetreatNeeded(from_col):
            adjust_maneuver_height = 0
            if 12 <= from_col <=23:
                adjust_maneuver_height = -2            
            command.append(self.GetMagnetManeuverCommand(adjust_maneuver_height))   #need to go up a bit, before retreat

            if from_col in (0,5,6,11,12,17,18,23):
                retreat_pos = self.camera.CalculatePutManeuverPoint(checker_pos_scr,from_col,1)  #check if it needs to 'retreat' to a safe position before lifting up the checker
                if retreat_pos is not None:
                    retreat_mach_pos = self.camera.GetMachineCoords(retreat_pos)
                    command.append(self.GetMoveToCommand(retreat_mach_pos))
                    
                retreat_pos2 = self.camera.CalculatePutManeuverPoint(retreat_pos,from_col,0)
                retreat_mach_pos2 = self.camera.GetMachineCoords(retreat_pos2)
                command.append(self.GetMoveToCommand(retreat_mach_pos2))
                checker_pos_mach = retreat_mach_pos2
            elif len(self.data_model.all_checkers[from_col]) == 1:
                retreat_pos = self.camera.CalculatePutManeuverPoint(checker_pos_scr,from_col,1)  #check if it needs to 'retreat' to a safe position before lifting up the checker
                if retreat_pos is None:
                    retreat_pos = self.camera.CalculatePutManeuverPoint(checker_pos_scr,from_col,0)  #check if it needs to 'retreat' to a safe position before lifting up the checker                    
                retreat_mach_pos = self.camera.GetMachineCoords(retreat_pos)
                command.append(self.GetMoveToCommand(retreat_mach_pos))
                checker_pos_mach = retreat_mach_pos

        command.append(self.GetMagnetUpCommand())   #need to go up, to straighten the checker

        checker_pos_scr = self.camera.GetScreenCoords(checker_pos_mach)

        return command,checker_pos_scr
    
    def GetPutOnBarCommand(self):
        command = []
        bar_pos = self.camera.GetNextSpotOnBar()
        bar_pos_mach = self.camera.GetMachineCoords(bar_pos)
        command.append(self.GetMoveToCommand(bar_pos_mach))
        command.append(self.GetMagnetBarCommand())
        command.append(self.GetMagnetOffCommand())
        command.append(self.GetMagnetUpCommand(2))
        return bar_pos,command
    
    def BarOpponentIfNeeded(self,take_from_col,start_from,color):
        command = []
        target_column_color = self.data_model.GetColorForColumn(take_from_col)

        if target_column_color == '0' or target_column_color == color:
            return command,start_from   #no need to put opponent on bar

        pickup_command,_ = self.PickupChecker(take_from_col,start_from,color)
        command.extend(pickup_command)
        target_pos,bar_commands = self.GetPutOnBarCommand()
        command.extend(bar_commands)
        return command,target_pos
    
    def GetPutAtHomeCommand(self):
        home_position = (0,100) #machine coordinates
        command = self.GetMoveToCommand(home_position)
        command.append(self.GetMagnetOffCommand())
        command.append(self.GetMagnetManeuverCommand())
        command.append(self.GetMagnetUpCommand(2))
        return command,home_position

    #move from original column to target column, which are in the same half, different quadrant
    def MoveCheckerBetweenQuardants(self,from_col,to_col,start_from,color,keep_magnet_on,skip_pickup):
        command = []
        cur_pos = start_from

        if skip_pickup == False:
            pickup_command,cur_pos = self.PickupChecker(from_col,start_from,color)
            command.extend(pickup_command)
            #cur_pos = self.data_model.GetLastChecker(from_col]    #keep the cur_pos before removing it. it is needed later to calculate path
            #now, go to put maneuver position. start to descend as soon as possible  
            self.data_model.RemoveCheckerFromColumn(from_col) 

        target_pos = 0 
        if to_col == 25:    #bar
            target_pos,bar_commands = self.GetPutOnBarCommand()
            command.extend(bar_commands)
        elif to_col == 27: # home
            target_pos_mach = (0,self.camera.GetMachineCoords(cur_pos)[1])
            target_pos = self.camera.GetScreenCoords(target_pos_mach)
            command.append(self.GetMoveToCommand(target_pos_mach))
            command.append(self.GetMagnetManeuverCommand())
            command.append(self.GetMagnetOffCommand()) 
            command.append(self.GetMagnetUpCommand(2))

        else:
            if keep_magnet_on == False:
                command.extend(self.GetMoveToPutManeuverCommand(from_col,to_col,cur_pos,keep_magnet_on))
                if keep_magnet_on == True:
                    target_pos = self.camera.CalculatePutManeuverPoint(cur_pos,to_col,0)
                    assert target_pos != 0
                else:
                    target_pos = self.camera.GetNextSpot(to_col)
                    target_pos_mach = self.camera.GetMachineCoords(target_pos)
                    command.append(self.GetMoveToCommand(target_pos_mach,400))
                    #command.append(self.GetMagnetDownCommand()) #no need to decent to 'down' - simply drop the checker
                    if keep_magnet_on == False:
                        command.append(self.GetMagnetOffCommand())
                    command.append(self.GetMagnetUpCommand(2))
                    #command.append(self.GetMoveToCommand((0,0)))
                    self.data_model.AddCheckerToTargetColumn(to_col,target_pos,color)
                    #if keep_magnet_on == True:
                    #self.data_model.RemoveCheckerFromColumn(to_col)
            else:
                target_pos = cur_pos    #if no movement was done, the current position doesnt change
        return command,target_pos

    def SendCommandToRGB(self,mode,text1,text2="NONE",pos1 = 0, pos2=0,dice1 = 0, dice2= 0):
        command = []
        rgb_command = f"RGB:{mode}:{text1}:{pos1}:{text2}:{pos2}:{dice1}:{dice2}"
        command.append(f"%{rgb_command}%")

        self.arduino.SendCommand(af.ConcatenateCommand(command))

    def SendHomeCommand(self):
        self.SendCommandToRGB ("JUST_TEXT","HOME")

        command = []
        command.append(self.GetMagnetUpCommand(2))
        command.append("%Home%")
        self.arduino.SendCommand(af.ConcatenateCommand(command))
        self.current_position = (0,0)
        #self.SendCommandToRGB ("JUST_TEXT","Ready")
        self.SendCommandToRGB("SCROLL_TEXT","Are You Ready?!?","NONE",0,0,0,0)
        #time.sleep(6)

        #self.SendCommandToRGB ("SCROLL_TEXT","Lets Play!")
    
    def ClearCommand(self):
        self.data_model.command = 0
        self.data_model.max_subcommand = -1

    def SendCommand(self,command):
        is_safe,tmp_pos,tmp_magnet_code,tmp_magnet_state = self.camera.board_simulation.ProcessCommand(command,self.current_position,self.magnet_angle_code,self.magnet_state)
        if is_safe:
            self.arduino.SendCommand(command)
            self.current_position,self.magnet_angle_code,self.magnet_state = tmp_pos,tmp_magnet_code,tmp_magnet_state
            self.ClearCommand()
        else:
            print ("******************************ERROR!!!!!**************************")

    #move checker within same half:
    def MoveCheckerBetweenColumns(self,from_col,to_col,start_from,color,keep_magnet_on,skip_pickup):
        cur_pos = 0
        command = 0
        

        command,cur_pos = self.MoveCheckerBetweenQuardants(from_col,to_col,start_from,color,keep_magnet_on,skip_pickup)

        return command,cur_pos

    def PutOnBar(self,movements,color,start_from):
        command = []
        cur_pos = start_from
        for movement in movements:
            bar_opponent_command,cur_pos = self.BarOpponentIfNeeded(movement[1],cur_pos,color)
            if bar_opponent_command != []:  #if opponent is moved to bar, remove it from column
                self.data_model.RemoveCheckerFromColumn(movement[1])
                self.data_model.AddCheckerToBar(cur_pos,af.OtherColor(color))
            command.extend(bar_opponent_command)
        return command,cur_pos
    #turns movements into commands
    def DoAllMovements(self,movements,color, skip_bar):
        cur_pos = (0,0) #machine coordinates
        cur_pos = self.camera.GetScreenCoords(cur_pos)
        commands = []
        if skip_bar == False:
            commands,cur_pos = self.PutOnBar(movements,color,cur_pos)
        for i,movement in enumerate(movements):
            if movement[1] != -1:
                
                keep_magnet_on = False
                if i< len(movements) - 1 and movement[1] == movements[i+1][0]:  #if next movement starts where current movement ends- dont pickup the checker
                    keep_magnet_on = True
                skip_pickup = False
                if i>0 and movements[i-1][1] == movement[0]:
                    skip_pickup = True
                command,cur_pos = self.MoveCheckerBetweenColumns(movement[0],movement[1],cur_pos,color,keep_magnet_on,skip_pickup)
                


                commands.extend(command)
                #self.data_model.UpdateCheckersCollections(movement,cur_pos)   #update DB (like last checkers, etc.) to reflect the movement
        return commands
        
    def ApplyCommand(self,commands):
        if commands != []:
            commands.append(self.GetMoveToCommand((0,0)))
            commands = af.ConcatenateCommand(commands)
            self.data_model.command = commands

    def MoveToOrigin(self):
        commands = []
        commands.append(self.GetMagnetUpCommand(2))
        commands.append(self.GetMoveToCommand((0,0)))
        commands = af.ConcatenateCommand(commands)
        self.SendCommand(commands)

    def ArrangeCalibrationCheckersOnBoard(self):
        commands = []
        commands.append(self.GetMagnetUpCommand(2))
        for i in range(4):
            commands.append(self.GetMoveToCommand(self.camera.point_mach[i]))
            commands.append(self.GetMagnetDownCommand())
            #commands.append(self.GetMagnetOnCommand())

            commands = af.ConcatenateCommand(commands)
            self.SendCommand(commands)
            #cv2.waitKey(0)
            self.WaitForPlayer(False)
            commands = []
            commands.append(self.GetMagnetUpCommand())
            commands.append(self.GetMagnetDownCommand())
            #commands.append(self.GetMagnetOffCommand())
            commands.append(self.GetMagnetUpCommand())
            commands = af.ConcatenateCommand(commands)
            self.SendCommand(commands)
            commands = []

        self.MoveToOrigin()        
            
        