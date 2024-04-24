import cv2
import numpy as np
import math
from CheckersDetection import CheckersDetection
import json
import DataModel
from AuxFunctions import AuxFunctions
from itertools import chain
import copy
import time

af = AuxFunctions ()

class CameraController:

    skip = False
    screen_controller = 0
    data_model = 0
    board_simulation = 0
    board = 0
    cap = 0
    calibration_magnet_pos = 0  #1 for calibration position, 0 for (0,0)
    calibration_test_pos = 0
    #to be measured on screen
    point_scr = [[672,124],[88,124],[88,600]]
    
    #points_area = [[[545, 69],[645, 149]],[[1077, 69],[1176, 149]],[[1103, 580],[1172, 660]]]
    points_area = [[[500, 10],[570, 90]],[[1140, 10],[1230, 90]],[[1150, 640],[1240, 720]]]
    
    #fixed points
    #point_mach = [[270,30],    [60,30],[60,230],[270,230]]
    #point_mach = [[284,3],     [27.5,3],[30.5,246],[284.5,245]]
    point_mach =  [[9.62,0.22],[1.04,0.25],[1.13,8.46],[9.68,8.39]]
    #test_area = [[563,590],[633, 650]]
    test_area = [[508,640],[600, 720]]
    
    #represents 1 mm on board. not too accurate. to be used for tolerance purposes only, since it cannot be accumulated 
    mm_tolerance = 1

    horizontal_line = [[100,10],[1240,40]]
    vertical_line = [[10,10],[10,700]]
    distortion_factor_y = 0
    distortion_factor_x = 0
    image_angle = 0
    image_rotation_matrix = None
    

    
    #to be calculated:
    slope = 10000
    mmperpixel = (0.3,0.3)
    mach_origin = (20,20)    #screen coordinates which represent the origin of the machine
    screen_height = 0
    #cal_circle = (570,100) #original position of the calibrated circle is located (screen coordinates)

    #x_axis = 2.0
    #y_axis = 2.0
    
    MANEUVER_TOLERANCE = 4 #in mm. is being set again after mm_tolerance is set

    cal_player_pos = 0 #(220,220) #the position where the calibrated player is (machine coordinates, CM)

    CALIBRATION_LENGTH = 250 #distance, in mm between P1 and P2
    #board_left_rect = [[154,46],[450, 649]]
    #board_right_rect = [[480,46],[781, 649]]

    board_left_rect = [[505,10],[842,716]]
    board_right_rect = [[878,15],[1228,713]]

    test_line = ((200,200),(400,200))


    dice_center = (300,300)
    dice_radius = 60

    ignore_rects = [[[142, 276], [332, 381]],[[492, 283], [677, 406]],[[399, 474], [443, 529]],[[389, 176], [433, 221]]]

    is_dragging = 0

    cur_x,cur_y = 0,0
    checkers_detection = 0

    MODE_CALIBRATION,MODE_GAME = 0,1
    screen_mode = MODE_CALIBRATION


    #calculate the point, in screen coordinates, which represent the origin of the machine
    def CalculateMachineParams(self):
        self.mmperpixel = ((self.point_mach[0][0]-self.point_mach[1][0])/(self.point_scr[1][0]-self.point_scr[0][0]),(self.point_mach[2][1]-self.point_mach[1][1])/(self.point_scr[2][1]-self.point_scr[0][1]))
        #self.mmperpixel = ((self.point_scr[0][0]-self.point_scr[1][0])/(self.point_mach[0][0]-self.point_mach[1][0]),(self.point_scr[2][1]-self.point_scr[1][1])/(self.point_mach[2][1]-self.point_mach[1][1]))

        pixelpermm = ((1./self.mmperpixel[0]),(1./self.mmperpixel[1]))
        
        self.mm_tolerance = (self.point_mach[3][0] - self.point_mach[2][0]) /256.0
        self.MANEUVER_TOLERANCE = self.mm_tolerance*4

        self.mach_origin = (self.point_scr[1][0] + self.point_mach[1][0]*pixelpermm[0],
                            self.point_scr[1][1] - self.point_mach[1][1]*pixelpermm[1])
        
        if self.point_scr[1][0]-self.point_scr[2][0] == 0:
            self.slope = 10000000
        else:
            self.slope = (self.point_scr[1][1]-self.point_scr[2][1]) / (self.point_scr[1][0]-self.point_scr[2][0])
        

    #pos in screen coordinates, return machine coordinates
    def GetMachineCoords(self,pos):
        #pos = (self.screen_width - pos[0],pos[1]) #screen coorinates start from top

        ret_val_x = (self.mach_origin[0] - pos[0] + (pos[1] - self.mach_origin[1])/self.slope) * self.mmperpixel[0]
        ret_val_y = (pos[1] - self.mach_origin[1])*self.mmperpixel[1]

        #  Sx,Sy (pos)
        #  Mx My  (Ret_val_x,_y)
        #  Sl (slope)
        #mmperpixel
        #MOx,MOy

        # Mx = (MOx - Sx + (Sy -MOY)/Sl) * mmperpixel_x





        #ret_val_x = (pos[0] - self.mach_origin[0] - (pos[1] - self.mach_origin[1])/self.slope) * self.mmperpixel[0]
        #ret_val_y = (pos[1] - self.mach_origin[1])*self.mmperpixel[1]
        return (ret_val_x,ret_val_y)

    #pos in mach coordinates, return screen coordinates
    #the screen coordinates assumes 0,0 of screen is 1top left
    def GetScreenCoords(self,pos):


        ret_val_y = (pos[1])/self.mmperpixel[1] + self.mach_origin[1]
        ret_val_x = self.mach_origin[0] - pos[0]/self.mmperpixel[0] + ((ret_val_y-self.mach_origin[1])/self.slope)

        #ret_val_y = self.screen_height - ret_val_y  #screen coorinates start from top

        return (int(ret_val_x),int(ret_val_y))



    def InitChekersDetection(self):
        self.checkers_detection.InitDetection(self.board_left_rect,self.board_right_rect,self.screen_controller,self.data_model,self.ignore_rects)

    def __init__(self,screen_controller,data_model,board):
        self.checkers_detection = CheckersDetection(self)
        self.screen_controller = screen_controller
        self.data_model = data_model
        self.board = board
        #self.cal_player_pos = (board.CALIBRATION_POS_X,board.CALIBRATION_POS_Y)
        cv2.setMouseCallback(self.screen_controller.board_window, self.mouse_callback)
        self.InitChekersDetection()
        self.data_model.UpdateBoardRects(self.board_left_rect,self.board_right_rect)
    
    def UnregisterMouse(self):
        #cv2.setMouseCallback(self.screen_controller.board_window, lambda *args : None)
        pass
    


    def CalculateMovement2(self,P1, P2, P3, Pnt):
        dist_x,dist_y  = af.distance_between_lines(P1, P2, P3, Pnt)
        return dist_x,dist_y

    
    def ToDictionary(self):

        rotation_matrix_list = self.image_rotation_matrix.tolist()

        return {
            'point_scr': self.point_scr,
            'horizontal_line':self.horizontal_line,
            'vertical_line':self.vertical_line,
            'image_angle': self.image_angle,
            'image_rotation_matrix':rotation_matrix_list,
            'distortion_factor_y' : self.distortion_factor_y,
            'distortion_factor_x' : self.distortion_factor_x,
            'board_left_rect': self.board_left_rect,
            'board_right_rect': self.board_right_rect,
            'dice_center': self.dice_center,
            'dice_radius': self.dice_radius,
            'ignore_rects': self.ignore_rects,
            'slope':self.slope,
            'mmperpixel' : self.mmperpixel
        }
    
    @classmethod
    def FromDictionary(cls,screen,data_model, data,board):

        ret_val = cls(screen,data_model,board)
        ret_val.horizontal_line = data['horizontal_line']
        ret_val.vertical_line = data['vertical_line']
        ret_val.image_angle = data['image_angle']
        rotation_matrix = data['image_rotation_matrix']

        ret_val.image_rotation_matrix = np.array(rotation_matrix)

        ret_val.distortion_factor_y = data['distortion_factor_y']
        ret_val.distortion_factor_x = data['distortion_factor_x']
        ret_val.point_scr = data['point_scr']

        if 'vertical_line' in data:
            ret_val.vertical_line = data['vertical_line']
        else:
            # Handle the case when 'vertical_line' key is not present in data
            ret_val.vertical_line = None 

        ret_val.slope = data['slope']
        ret_val.mmperpixel = data['mmperpixel']
        #ret_val.cal_player_pos = data['cal_player_pos']
        ret_val.board_left_rect = data['board_left_rect']
        ret_val.board_right_rect = data['board_right_rect']
        ret_val.dice_center = data['dice_center']
        ret_val.dice_radius = data['dice_radius']
        ret_val.ignore_rects = data['ignore_rects']
        #ret_val.x_axis = data['x_axis']
        #ret_val.y_axis = data['y_axis']

        #ret_val.pixelPerMM = data['pixelPerMM']
        ret_val.InitChekersDetection()
        ret_val.CalculateMachineParams()
        return ret_val
        
    def MoveMagnet(self,pos):
        pos_machine = self.GetMachineCoords(pos)
        self.board.MagnetUp()
        self.board.MoveTo(pos_machine)

    def ManeuverMagnet(self,pos):
        pos_machine = self.GetMachineCoords(pos)
        self.board.MagnetManeuver()
        self.board.ManeuverTo(pos_machine)


    def SaveToFile(self):
        with open("CameraController.json", "w") as file:
            to_dic = self.ToDictionary()
            json.dump(to_dic, file, default=lambda x: float(x))
            

    def mouse_callback(self,event, x, y, flags, param):
        self.cur_x = x
        self.cur_y = y

        if self.screen_mode == self.MODE_GAME:
            if event == cv2.EVENT_LBUTTONDOWN:
                if (af.IsCloseTo(self.test_line[0],(x,y))):
                        self.is_dragging = 1
                if (af.IsCloseTo(self.test_line[1],(x,y))):
                        self.is_dragging = 2

            elif event == cv2.EVENT_MOUSEMOVE:
                if self.is_dragging == 1:
                    self.test_line = ((x,y),self.test_line[1])
                if self.is_dragging == 2:
                    self.test_line = (self.test_line[0],(x,y))
            if event == cv2.EVENT_LBUTTONUP:
                        self.is_dragging = 0
        #elif self.screen_mode == self.MODE_CALIBRATION:
        else:
            if event == cv2.EVENT_LBUTTONDOWN:
                # Set the starting point of the line
                
                #if not a specific action - move the magnet
                if self.is_dragging == 0:
                    if flags & cv2.EVENT_FLAG_CTRLKEY:
                        self.is_dragging = 20
                    if flags & cv2.EVENT_FLAG_SHIFTKEY:
                        self.is_dragging = 21

                y_for_point_scr = y#self.screen_height - y
                if (self.is_dragging == 0 and af.IsCloseTo(self.point_scr[0],(x,y_for_point_scr))):
                    self.is_dragging = 1
                if (self.is_dragging == 0 and af.IsCloseTo(self.point_scr[1],(x,y_for_point_scr))):
                    self.is_dragging = 2
                if (self.is_dragging == 0 and af.IsCloseTo(self.point_scr[2],(x,y_for_point_scr))):
                    self.is_dragging = 3

                #board rect
                if (af.IsCloseTo(self.board_right_rect[0],[x,y])):
                    self.is_dragging = 5
                if (af.IsCloseTo(self.board_right_rect[1],[x,y])):
                    self.is_dragging = 6
                #calibration circle 
                """if (af.IsCloseTo(self.cal_circle,(x,y))):
                    self.is_dragging = 7"""

                #dice rect
                if (af.IsCloseTo(self.dice_center,(x,y))):
                    self.is_dragging = 8

                drag_num = 10
                for rect in self.ignore_rects:
                    if (af.IsCloseTo(rect[0],(x,y))):
                        self.is_dragging = drag_num
                    if (af.IsCloseTo(rect[1],(x,y))):
                        self.is_dragging = drag_num +1

                    drag_num+=2

                if (af.IsCloseTo(self.board_left_rect[0],(x,y))):
                    self.is_dragging = 18
                if (af.IsCloseTo(self.board_left_rect[1],(x,y))):
                    self.is_dragging = 19
                
                if (af.IsCloseTo(self.horizontal_line[0],(x,y))):
                    self.is_dragging = 22
                if (af.IsCloseTo(self.horizontal_line[1],(x,y))):
                    self.is_dragging = 23

                if (af.IsCloseTo(self.vertical_line[0],(x,y))):
                    self.is_dragging = 24
                if (af.IsCloseTo(self.vertical_line[1],(x,y))):
                    self.is_dragging = 25


                #if not a specific action - move the magnet
                if self.is_dragging == 0:
                    if flags & cv2.EVENT_FLAG_CTRLKEY:
                        self.is_dragging = 20
                    if flags & cv2.EVENT_FLAG_SHIFTKEY:
                        self.is_dragging = 21
                


            elif event == cv2.EVENT_LBUTTONUP:
                if self.is_dragging == 20:
                    self.MoveMagnet((x,y))
                if self.is_dragging == 21:
                    self.ManeuverMagnet((x,y))

                if self.is_dragging != 0:
                    self.SaveToFile()
                # Set the end point of the line
                self.is_dragging = 0
            elif event == cv2.EVENT_MOUSEMOVE:
                # Set the end point of the line
                if self.is_dragging == 1:
                    #distance = math.sqrt((self.point3[0] - self.point2[0])*(self.point3[0] - self.point2[0])+ (self.point3[1] - self.point2[1])*(self.point3[1] - self.point2[1]))
                    #self.point1 = (x,y)
                    self.point_scr[0] = (x,y)
                    self.point_scr[1] = (self.point_scr[1][0],y)  #point 1 and point 2 have the same y
                    self.CalculateMachineParams()
                    #self.CalcPoint3(distance)
                if self.is_dragging == 2:
                    self.point_scr[1] = (x,y)
                    self.point_scr[0] = (self.point_scr[0][0],y)  #point 1 and point 2 have the same y
                    self.CalculateMachineParams()
                    #CalcPoint3()
                if self.is_dragging == 3:
                    self.point_scr[2] = (x,y)
                    self.CalculateMachineParams()
                    #self.CalcPoint1(distance)
                if self.is_dragging == 4:
                    point4 = (x,y)
                if self.is_dragging == 5:
                    self.board_right_rect = [[x,y],self.board_right_rect[1]]
                if self.is_dragging == 6:
                    self.board_right_rect = [self.board_right_rect[0],[x,y]]

                if self.is_dragging == 8:
                    self.dice_center = (x,y)


                for i in range (10,18,2):
                    rect_num = int((i-10)/2)
                    if self.is_dragging == i:
                        self.ignore_rects[rect_num] = ((x,y),self.ignore_rects[rect_num][1])
                    if self.is_dragging == i+1:
                        self.ignore_rects[rect_num] = (self.ignore_rects[rect_num][0],(x,y))

                if self.is_dragging == 18:
                    self.board_left_rect = ((x,y),self.board_left_rect[1])
                if self.is_dragging == 19:
                    self.board_left_rect = (self.board_left_rect[0],(x,y))
                
                if self.is_dragging == 22:
                    self.horizontal_line = [[self.horizontal_line[0][0],y],[self.horizontal_line[1][0],y]]
                if self.is_dragging == 23:
                    self.horizontal_line = [[self.horizontal_line[0][0],y],[self.horizontal_line[1][0],y]]

                if self.is_dragging == 24:
                    self.vertical_line = [[x,self.vertical_line[0][1]],[x,self.vertical_line[1][1]]]
                if self.is_dragging == 25:
                    self.vertical_line = [[x,self.vertical_line[0][1]],[x,self.vertical_line[1][1]]]

                if (self.is_dragging != 0):
                    self.checkers_detection.InitDetection(self.board_left_rect,self.board_right_rect,self.screen_controller,self.data_model,self.ignore_rects)
                    self.data_model.UpdateBoardRects(self.board_left_rect,self.board_right_rect)



                #self.pixelPerMM = (math.sqrt((self.point3[0]-self.point2[0]) ** 2 + (self.point3[1]-self.point2[1]) ** 2))/self.CALIBRATION_LENGTH
                #print ("new mm per pixel:" , self.pixelPerMM)
            

    def MoveMagnetToTest(self):
        self.calibration_test_pos +=1

        if self.calibration_test_pos == 2:
            self.calibration_test_pos = 0
        self.board.MoveMagnetToTest(self.calibration_test_pos)
    
    def MoveMagnetAway(self):
        self.calibration_magnet_pos +=1

        if self.calibration_magnet_pos == 4:
            self.calibration_magnet_pos = 0
        self.board.MoveMagnetAwayInCalibration(self.calibration_magnet_pos)
    
    def InitCalibrate(self):
        self.cap=cv2.VideoCapture(0)
        #cv2.namedWindow(self.screen_controller.board_window, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.screen_controller.board_window, self.mouse_callback)

    def DrawPointsRectangles(self,image):
        cv2.rectangle(image, self.points_area[0][0], self.points_area[0][1], (0, 255, 0), 2)
        cv2.rectangle(image, self.points_area[1][0], self.points_area[1][1], (0, 255, 0), 2)
        cv2.rectangle(image, self.points_area[2][0], self.points_area[2][1], (0, 255, 0), 2)
        cv2.rectangle(image, self.test_area[0], self.test_area[1], (0, 255, 0), 2)
    


    def DrawBoardRectangles(self,image):
        cv2.rectangle(image, self.board_right_rect[0], self.board_right_rect[1], (0, 255, 0), 2)
        cv2.rectangle(image, self.board_left_rect[0], self.board_left_rect[1], (0, 255, 0), 2)

        cv2.circle(image, self.dice_center,self.dice_radius,(0, 255, 0),2)
        cv2.circle(image, self.dice_center,4,(0, 255, 0),2)


    def DrawBarNextSpotPosition(self,image):
        pos = self.GetNextSpotOnBar()
        if pos != None:
            cv2.circle(image, pos, 20, (0, 0, 255), 2)  

    def GetBarMidX(self):
        return (self.board_left_rect[1][0]+self.board_right_rect[0][0])/2.
    def DrawTestLine(self,image):
        pass
        cv2.line(image,self.test_line[0],self.test_line[1], (255, 0, 0), 1)

        mach_pos1 = self.mach_pos = self.GetMachineCoords((self.test_line[0][0], self.test_line[0][1]))
        mach_pos2 = self.mach_pos = self.GetMachineCoords((self.test_line[1][0], self.test_line[1][1]))

        dist = af.calculate_distance(mach_pos1,mach_pos2)

        str1 = f"({self.test_line[0][0]}, {self.test_line[0][1]}) --> ({self.test_line[1][0]}, {self.test_line[1][1]})"
        dist_str = f"dist: {dist}"

        cv2.putText(image, str1, (900, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (64, 128, 255), 2)
        cv2.putText(image, dist_str, (900, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (64, 128, 255), 2)



    def DrawCoordinates(self,image):
        #cur_pos = str(self.cur_x) + "," + str(self.screen_height - self.cur_y)
        cur_pos = str(self.cur_x) + "," + str(self.cur_y)
        #mach_pos = self.GetMachineCoords((self.cur_x, self.cur_y))
        mach_pos = self.GetMachineCoords((self.cur_x, self.cur_y))
        mach_pos_text = "{:.2f},{:.2f}".format(round(mach_pos[0], 2), round(mach_pos[1], 2))
        if self.data_model.dice != 0:
            dice = str(self.data_model.dice[0]) + ":" + str(self.data_model.dice[1]) + "|" + str(self.data_model.movement)
            cv2.putText(image, dice, (50,130),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255, 255), 2)
        cv2.putText(image, cur_pos, (50,50),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        cv2.putText(image, mach_pos_text, (50,90),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255, 255), 2)
        

    def Calibrate(self):
        image = self.CreateImageFromCamera()
        image = self.ApplyTransformationOnImageFromCamera(image)
        height, width = image.shape[:2]
        
        self.screen_height = height
        self.screen_width = width

        # Create a blank canvas with the new dimensions
        canvas = np.zeros((height, width, 3), dtype=np.uint8)

        # Copy the original image to the top of the canvas
        # Copy the grayscale image to all three channels of the canvas
        #canvas[:height, :, :] = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        canvas[:height, :, :] = image
        
        
        self.DrawBoardRectangles(canvas)

        self.DrawPointsRectangles(canvas)
        for rect in self.ignore_rects:
            cv2.rectangle(canvas, rect[0], rect[1], (0,0,255), 2)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        checker_rad = self.DrawCalibrationPoints(canvas)

        

        
        cv2.line(canvas, self.horizontal_line[0],self.horizontal_line[1],(0,0,255),2)
        cv2.line(canvas, self.vertical_line[0],self.vertical_line[1],(0,0,255),2)
        
        
        self.DrawTestPoint(canvas, checker_rad)

        self.DrawCoordinates(canvas)
       
        self.screen_controller.board_image = canvas
        #cv2.imshow(self.screen_controller.board_window, canvas)
        self.TakeDiceSnapshot(image_available=True,image=image)
        char_input = self.screen_controller.ShowWindows()
        if self.skip == True:
            return False
        else:   
            if char_input & 0xFF == ord('c'):
                self.FinishCalibration()
                return True
            self.HandleKeyboard(char_input)
        return False

    def DrawCalibrationPoints(self, canvas):
        checker_rad = 20
        for i in range (3):
            cv2.circle(canvas, (self.point_scr[i][0], self.point_scr[i][1]), checker_rad, (0, 97, 193), 2)  
            cv2.putText(canvas, str(i+1), (self.point_scr[i][0]+20, self.point_scr[i][1]),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 97, 193), 2)
            cv2.circle(canvas, (self.point_scr[i][0], self.point_scr[i][1]), 2, (0, 255, 0), 2)
        return checker_rad

    def DrawTestPoint(self, canvas, checker_rad):
        test_calculated = self.GetScreenCoords (self.point_mach[3])
        cv2.circle(canvas, (test_calculated[0], test_calculated[1]), checker_rad, (0, 97, 193), 2)
        cv2.circle(canvas, (test_calculated[0], test_calculated[1]), 2, (0, 97, 193), 2)

    def AdjustRectangles(self):
        self.checkers_detection.AdjustRectangles()
        self.SaveToFile()

    def HandleKeyboard(self, char_input):
        
        if char_input == -1:
            return

        

        if char_input & 0xFF == ord('1'):
            self.dice_radius+=1
        if char_input & 0xFF == ord('2'):
            self.dice_radius-=1






        if char_input & 0xFF == ord('r'):
            self.board.HandleRollDice()

        
        if char_input & 0xFF == ord('+'):
            self.RotateImage(0.05)
        if char_input & 0xFF == ord('-'):
            self.RotateImage(-0.05)

       
        
        self.SaveToFile()

    def FinishCalibration(self):
        if not self.data_model.disable_robot:
            self.board.MoveToOrigin()   
        
    def RotateImage(self,angle):
        self.image_angle +=angle

    def DistortImageY(self,factor):
        self.distortion_factor_y +=factor

    def DistortImageX(self,factor):
        self.distortion_factor_x +=factor

        for i in range(24):
            if self.data_model.all_checkers != []:
                manouver_point = self.CalculatePickupHoverPoint(i)

                if (manouver_point != None):
                    cv2.circle(self.screen_controller.board_image,(manouver_point[0],manouver_point[1]),6,(172, 79, 163),2)
                
    def DrawLastCheckers(self):
        for i in range(24):
            next_spot = self.GetNextSpot(i)
            if (next_spot != None):
                cv2.circle(self.screen_controller.board_image,(next_spot[0],next_spot[1]),6,(0, 0, 255),2)
            last_checker = self.data_model.GetLastChecker(i)
            if last_checker != None:
                cv2.circle(self.screen_controller.board_image,(last_checker[0],last_checker[1]),6,(0,255, 0),2)

    def GetCircleInRect(self,rect,circles):
        #circles = self.checkers_detection.CalcCirclesFromCache()
        for point in circles:
            if rect[0][0] <= point[0] <= rect[1][0] and rect[0][1] <= point[1] <= rect[1][1]:
                return [point[0],point[1]]
        return None

    def DrawCommandLines(self,image):
        if self.data_model.command == 0 or self.data_model.command == '':
            return image
        split_commands = self.data_model.command.split('^')
        return af.TextToImage(image,split_commands,(0,150), highlighted_line=self.data_model.max_subcommand, n=None)


    def UpdateCalibrationPoints(self,image):
        circles = self.checkers_detection.ExtractCirclesFromImage (image)
        self.point_scr[0] = self.GetCircleInRect(self.points_area[0],circles)
        self.point_scr[1] = self.GetCircleInRect(self.points_area[1],circles)
        self.point_scr[2] = self.GetCircleInRect(self.points_area[2],circles)

        """self.point_scr[0] = [round(item) for item in self.point_scr[0]]
        self.point_scr[1] = [round(item) for item in self.point_scr[1]]
        self.point_scr[2] = [round(item) for item in self.point_scr[2]]"""
        self.CalculateMachineParams()

    def CalibrateBoard(self):
        cal_image_orig = self.CreateImageFromCamera()

        for i in range (2):
            cal_image = cal_image_orig.copy()
            cal_image = self.ApplyTransformationOnImageFromCamera(cal_image)

            self.UpdateCalibrationPoints(cal_image)

            self.image_rotation_matrix = af.FindRotationMatrix(self.point_scr[0],self.point_scr[1],cal_image)
            
            cal_image = self.ApplyTransformationOnImageFromCamera(cal_image_orig)

            self.UpdateCalibrationPoints(cal_image)
            
            """self.point_scr[0] = self.GetScreenCoords(self.point_mach[0])
            self.point_scr[1] = self.GetScreenCoords(self.point_mach[1])
            self.point_scr[2] = self.GetScreenCoords(self.point_mach[2])"""


            test_calculated = self.GetScreenCoords(self.point_mach[3])
            #tmp = self.GetMachineCoords(test_calculated)
            circles = self.checkers_detection.ExtractCirclesFromImage (cal_image)
            test_actual = self.GetCircleInRect(self.test_area,circles)
            
            print (f"actual : {test_actual} | calculated: {test_calculated}")
            while (abs(test_calculated[0] - test_actual[0]) > 1):
                delta = 0.0001

                delta = 0.001 if abs(test_calculated[0] - test_actual[0]) > 2 else 0.0001

                if test_actual[0] > test_calculated[0]:
                    self.DistortImageX(delta)
                else:
                    self.DistortImageX(-delta)
                cal_image = cal_image_orig.copy()
                cal_image = self.ApplyTransformationOnImageFromCamera(cal_image_orig)

                circles = self.checkers_detection.ExtractCirclesFromImage (cal_image)
                test_actual = self.GetCircleInRect(self.test_area,circles)
                print (f"X remaining distance : {(test_calculated[0] - test_actual[0])}")


            while (abs(test_calculated[1] - test_actual[1]) > 1):
                delta = 0.001 if abs(test_calculated[1] - test_actual[1]) > 2 else 0.0001
                if test_actual[1] > test_calculated[1]:
                    self.DistortImageY(-delta)
                else:
                    self.DistortImageY(delta)
                cal_image = cal_image_orig.copy()
                cal_image = self.ApplyTransformationOnImageFromCamera(cal_image_orig)

                circles = self.checkers_detection.ExtractCirclesFromImage (cal_image)
                test_actual = self.GetCircleInRect(self.test_area,circles)
                print (f"Y remaining distance : {(test_calculated[1] - test_actual[1])}")

        self.point_scr[0] = [round(item) for item in self.point_scr[0]]
        self.point_scr[1] = [round(item) for item in self.point_scr[1]]
        self.point_scr[2] = [round(item) for item in self.point_scr[2]]
        #self.SaveToFile()
        
    def CreateImageFromCamera(self):
        if af.IsSnapshotAvailable():
            image = af.GetSnapshot()
        else:
            image = None
            while image is None:
                ret,image=self.cap.read()
                if image is None:
                    print ("Image is none!!!!!!")
                    time.sleep(0.5)
        return image

    def ApplyTransformationOnImageFromCamera(self, image):
        #image = cv2.flip(image,-1)
        #image = af.RotateImage(image,self.image_angle)
        if self.image_rotation_matrix is not None:
            image = cv2.warpAffine(image, self.image_rotation_matrix,(image.shape[1], image.shape[0]))
        image = af.DistortImageY(image,self.distortion_factor_y)
        image = af.DistortImageX(image,self.distortion_factor_x)
        return image
      

    def GetBoardPlayers(self):
        image = self.CreateImageFromCamera()
        image = self.ApplyTransformationOnImageFromCamera(image)
        self.screen_controller.board_image = image
        
        self.data_model.current_image = image   #for debug purposes
        self.checkers_detection.ArrangeColumns()
        checkers = self.checkers_detection.DetectCheckers(image)
        board = self.checkers_detection.calc_checkers_on_board(image,checkers)
        self.checkers_detection.DrawBoard(image,checkers)
        self.DrawLastCheckers()
        
        self.DrawBoardRectangles(image)
        self.DrawCalibrationPoints(image)
        self.DrawTestLine(image)
        self.DrawBarNextSpotPosition(image)
        self.DrawCoordinates(image)
        self.DrawPointsRectangles(image)
        self.DrawTestPoint(image, 20)
        image = self.DrawCommandLines(image)
        test,_,_,_ = self.board_simulation.DrawCommand(image,self.data_model.command,(0,0),self.board.UP,self.board.MAGNET_OFF)
        if test == False:
            print ("***********************ERROR****************************")
        self.data_model.UpdateBoardFromCamera(board)
        self.screen_controller.board_image = image

 

    def TakeDiceSnapshot(self,image_available = False,image = None):
        if image_available == False:
            #cap=cv2.VideoCapture(0)
            ret, frame = self.cap.read()
            #frame = cv2.flip(frame,-1)
        else:
            frame = image

        
        #frame= self.screen_controller.board_image
        
        ((x1, y1), (x2, y2)) = af.BoundingRect(self.dice_center,self.dice_radius)
        
        if y2 > frame.shape[0] or x2 > frame.shape[1]:
            return

        cropped1_image = frame[y2:y1, x1:x2 ]

        height, width, _ = cropped1_image.shape

        self.screen_controller.dice1_image = cropped1_image

        #cv2.resizeWindow(self.screen_controller.dice1_window, width, height)

        """cv2.namedWindow("test", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("test", (x2-x1), (y2-y1)*2)
        cv2.imshow("test", cropped1_image)"""
        #self.screen_controller.dice_image = cropped_image
        return cropped1_image

    #get the columns from which to move and where to move and returns the exact positions, according to the recent detection
    """def GetCheckersPosition(self,origin_column,target_column):
        origin = self.data_model.GetLastChecker(origin_column)
        target = self.GetNextSpot(target_column)

        origin = self.GetMachineCoords(origin)
        target = self.GetMachineCoords(target)

        return origin,target"""

    #return screen coordinates
    def GetNextSpot(self,column):
        if self.data_model.all_checkers == []:
            return None
        
        if column in (26,27):   #home position
            return self.GetScreenCoords(self.board.home_position)

        if len(self.data_model.all_checkers[column]) > 0:
            #if ((column+1) in self.data_model.white_pieces or (column+1) in self.data_model.black_pieces):  #black_pieces is one based, checker_num is zero based, hence +1
            return self.CalculateNextSpot(column)
        else:
            return self.GetDefaultPosition(column)

    #returns the default position to place the checker if it's empty
    def GetDefaultPosition(self,column):
        column_width,column_height = self.checkers_detection.GetColumnDimensions(column)

        #magnet_rad = self.data_model.MAGNET_RADIUS * self.pixelPerMM
        magnet_rad = self.data_model.MAGNET_RADIUS / self.mmperpixel[1]

        pos = self.checkers_detection.columns_positions[column]

        if column < 12:
            ret_val = [int(pos[0] + column_width/2),int(pos[1] + magnet_rad)]
        else:
            ret_val = [int(pos[0] + column_width/2),int(pos[1]+column_height - magnet_rad)]
        return ret_val

    def CalculateNextSpot(self,column):
        next_spot = self.GetDefaultPosition(column)
        if self.data_model.GetLastChecker(column) != None:
            next_spot = (self.GetDefaultPosition(column)[0],self.data_model.GetLastChecker(column)[1])
        #distance from last checker in column
        threshold = 0   #no threshold, manouver will compensate

        #checker_rad = self.data_model.CHECKER_RADIUS * self.pixelPerMM
        checker_rad = self.data_model.CHECKER_RADIUS / self.mmperpixel[1]

        if (column < 12):
            next_spot = (next_spot[0],next_spot[1] + 2 * checker_rad + threshold)
        else:
            next_spot = (next_spot[0],next_spot[1] - 2 * checker_rad - threshold)
        next_spot = [int(next_spot[0]),int(next_spot[1])]
        return next_spot
    
    def GetBoardCount(self,column_num):
        if self.data_model.board_columns_count == []:
            return -1
        if column_num == -1 or column_num == 24:
            return -1
        return self.data_model.board_columns_count[column_num]
    
    #output format: ((column before,num of checkers),(column,num of checkers),(column after,num of checkers))
    def GetNeighboursCheckerNextSpot(self,column_num):
        #ret_val = [[column_num-1,self.GetBoardCount(column_num-1)],[column_num,self.GetBoardCount(column_num)],[column_num+1,self.GetBoardCount(column_num+1)]]

        prev_col_next_spot = self.GetNextSpot(column_num-1) if column_num!= 0 else [0,3000]
        next_col_next_spot = self.GetNextSpot(column_num+1) if column_num!= 23 else [0,3000]
        ret_val = [[column_num-1,prev_col_next_spot],[column_num+1,next_col_next_spot]]
        #taking care of the other 'walls' that were not handled in GetBoardCount
        if column_num in (5,11,17): 
            ret_val [1][1] = [0,3000]

        if column_num in (6,12,18):
            ret_val [0][1] = [0,3000]

        return ret_val
    
    #calculate landing spot to start manouver from, for PICKING checkers. it works only if there's only one checker in the columns,
    #oterwise, there's no need
    #return the position in screen coordinates, None otherwise
    def CalculatePickupHoverPoint(self,pick_col):
        """if self.data_model.board_columns_count == []:
            return 0"""
        if len(self.data_model.all_checkers[pick_col]) != 1 and pick_col not in (0,23,5,18,6,17,11,12):
            return None #function does nothing if there's no one checker in the column
        #tolerance = self.MANEUVER_TOLERANCE * self.pixelPerMM
        #magnet_rad = self.data_model.MAGNET_RADIUS * self.pixelPerMM

        tolerance = self.MANEUVER_TOLERANCE / self.mmperpixel[1]
        magnet_rad = self.data_model.MAGNET_RADIUS / self.mmperpixel[1]


        pos = self.data_model.GetLastChecker(pick_col)

        #handle x dimension
        if pos == None:
            return None
        if pick_col in (0,23):
            max_x = self.board_right_rect[1][0] - magnet_rad - tolerance
            pos = (min(pos[0],max_x),pos[1]) 
        if pick_col in (5,18):
            max_x = self.board_right_rect[0][0] + magnet_rad + tolerance
            pos = (max(pos[0],max_x),pos[1]) 

        if pick_col in (6,17):
            max_x = self.board_left_rect[1][0] - magnet_rad - tolerance
            pos = (min(pos[0],max_x),pos[1]) 

        if pick_col in (11,12):
            max_x = self.board_left_rect[0][0] + magnet_rad + tolerance
            pos = (max(pos[0],max_x),pos[1]) 

        #handle y dimension
        if 0 <= pick_col < 6:
            max_y = self.board_right_rect[0][1] + magnet_rad + tolerance
            pos = (pos[0],max(pos[1],max_y))

        if 6 <= pick_col < 12:
            max_y = self.board_left_rect[0][1] + magnet_rad + tolerance
            pos = (pos[0],max(pos[1],max_y))

        if 12 <= pick_col < 18:
            max_y = self.board_left_rect[1][1] - magnet_rad - tolerance
            pos = (pos[0],min(pos[1],max_y))

        if 18 <= pick_col < 24:
            max_y = self.board_right_rect[1][1] - magnet_rad - tolerance
            pos = (pos[0],min(pos[1],max_y))

        if pos == self.data_model.GetLastChecker(pick_col): #if there was no need to adjust the pick maneuver - discard it
            return None
        return (int(pos[0]),int(pos[1])) 
    

    #calculate landing spot to start manouver from, for PUTTING checkers
    #step 0 - landing spot, step 1- only in case of neighbours - go to the middle of the column
    def CalculatePutManeuverPoint(self,from_pos,to_col,step = 0):
        ret_val=[0,0]

        if to_col in (26,27):
            return 

        magnet_rad = self.data_model.MAGNET_RADIUS / self.mmperpixel[1]

        put_maneuver_spots = self.GetNeighboursCheckerNextSpot(to_col)    #how many checkers are in the columns before and after the column and in the column
        if put_maneuver_spots is None:
            return (-1,-1)
        if put_maneuver_spots[0][1] == -1:  #the board is not populated yet, ignore
            return (-1,-1)
        y_tolerance = self.MANEUVER_TOLERANCE /self.mmperpixel[1]  #2 mm in pixels
        col_next_spot = self.GetNextSpot(to_col)

        if af.GetColumnSide(to_col) == 1:    #top side
            col_next_spot = (col_next_spot[0],col_next_spot[1] +y_tolerance)
        else:
            col_next_spot = (col_next_spot[0],col_next_spot[1] -y_tolerance)

        put_maneuver_spots[0][1][0] = (put_maneuver_spots[0][1][0] + col_next_spot[0])/2.
        put_maneuver_spots[1][1][0] = (put_maneuver_spots[1][1][0] + col_next_spot[0])/2.

        if af.GetColumnSide(to_col) == 1:    #top side
            put_maneuver_spots[0][1][1] = max(col_next_spot[1],put_maneuver_spots[0][1][1])
            put_maneuver_spots[1][1][1] = max(col_next_spot[1],put_maneuver_spots[1][1][1])
        else:
            put_maneuver_spots = [[item[0], [item[1][0], -3000] if item[1][1] == 3000 else item[1]] for item in put_maneuver_spots]
            put_maneuver_spots[0][1][1] = min(col_next_spot[1],put_maneuver_spots[0][1][1])
            put_maneuver_spots[1][1][1] = min(col_next_spot[1],put_maneuver_spots[1][1][1])
        
        if put_maneuver_spots[0][1][1] == put_maneuver_spots[1][1][1] == col_next_spot[1]:  #no neighbours, just return the col_next_spot
            if step == 0:
                return col_next_spot
            else:
                return None

        ret_val = 0
        if abs(put_maneuver_spots[0][1][1]- put_maneuver_spots[1][1][1]) < magnet_rad:  #spots are relatively close, take the one that is closest to cur_position:
            ret_val = af.FindClosestPoint(from_pos,put_maneuver_spots)
        else:
            ret_val = af.FindClosestPoint(col_next_spot,put_maneuver_spots)
        
        

        if step == 1:
            if ret_val[1] != col_next_spot[1]:
                return [col_next_spot[0],ret_val[1]]
            else:
                return None

        return ret_val

    def GetMidPositionForBar(self):
        y_boundaries = [max(self.board_left_rect[0][1],self.board_right_rect[0][1]),min(self.board_left_rect[1][1],self.board_right_rect[1][1])]
         #the middle of the space between the furhtest checker on the top board and and furthest on the bottom
        topmost_col_5 = y_boundaries[0] if self.data_model.GetLastChecker(5) is None else self.data_model.GetLastChecker(5)[1]
        topmost_col_6 = y_boundaries[0] if self.data_model.GetLastChecker(6) is None else self.data_model.GetLastChecker(6)[1]
        topmost = max(topmost_col_5,topmost_col_6)

        bottommost_col_17 = y_boundaries[1] if self.data_model.GetLastChecker(17) is None else self.data_model.GetLastChecker(17)[1]
        bottommost_col_18 = y_boundaries[1] if self.data_model.GetLastChecker(18) is None else self.data_model.GetLastChecker(18)[1]
        bottommost = min(bottommost_col_17,bottommost_col_18)
        if topmost < bottommost:
            return (int(self.GetBarMidX()),int((topmost+bottommost)/2))
        else:
            return (int(self.GetBarMidX()),int((y_boundaries[0]+y_boundaries[1])/2.))
        
    def GetNextSpotOnBar(self):
        y_boundaries = [max(self.board_left_rect[0][1],self.board_right_rect[0][1]),min(self.board_left_rect[1][1],self.board_right_rect[1][1])]

        if (self.data_model.all_checkers is None) or self.data_model.all_checkers == []:
            return (int(self.GetBarMidX()),int((y_boundaries[0]+y_boundaries[1])/2.))
        
        if self.data_model.bar_checkers == [[],[]]: 
            return self.GetMidPositionForBar()

        bar_y_values = [item[1] for sublist in self.data_model.bar_checkers for item in sublist]
        bar_y_values.extend(y_boundaries)
        checker_rad = self.data_model.CHECKER_RADIUS / self.mmperpixel[1]
        tolerance = (7*self.mm_tolerance) / self.mmperpixel[1]
        pos = af.FindClosestMidPosition(bar_y_values,(4* checker_rad) + tolerance,(checker_rad) + tolerance,self.GetMidPositionForBar()[1])
        if pos != None:
            return (int(self.GetBarMidX()),int(pos))
        else:
            return None 