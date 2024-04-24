'''GUI for Backgammon game
Created April 2017
@author: Nate Gamble (neg6)
'''

import numpy as np
import cv2 as cv2
from backgammon_black import *
from backgammon_white import *


class GeneratedBoard:

    board_size = 0

    triangle_height = 300
    triangle_width = 60
    bar_width = 20
    data_model = 0
    screen = 0
    color_black = (0, 0, 0)
    color_red = (0, 0, 255)
    color_white = (255, 255, 255)

    color_yellow = (75, 163, 194)
    color_light_brown = (173, 216, 230)  # Adjust for the desired shade
    color_blue = (151, 107,68)
    color_dark_brown = (139, 69, 19)  # Adjust for the desired shade
    selected_column = -1
    columns = []
    STATE_SELECT_ORIGIN,STATE_SELECT_TARGET = 0,1
    state= STATE_SELECT_ORIGIN

    origin = -1
    cur_movement = -1
    movement = []

    mouse_column = -1 #in which column the mouse is

    def GetHomeRectangle(self):
        x0 = self.triangle_width*12 + self.bar_width
        x1 = x0+30

        y0 = 0
        y1 = self.board_size[1]
        return ((x0,y0),(x1,y1))
    
    def GetBarRectangle(self):
        w = self.board_size[0]
        h = self.board_size[1]

        # calculate the coordinates of the rectangle
        #x1 = w / 2 - 10 - int(0.5*self.bar_width)
        x1 = self.triangle_width*6
        x2 = self.triangle_width*6 + self.bar_width
        y1 = 0
        y2 = h
        #coords = [x1, y1, x1, y2, x2, y2, x2, y1]
        coords = ((x1,y1),(x2,y2))
        return coords 

    def create_separator(self,image):
        #w = int(self._canvas.cget('width'))
        #h = int(self._canvas.cget('height'))

        w = self.board_size[0]
        h = self.board_size[1]

        # calculate the coordinates of the rectangle
        #x1 = w / 2 - 10 - int(0.5*self.bar_width)
        x1 = self.triangle_width*6
        x2 = self.triangle_width*6 + self.bar_width
        y1 = 0
        y2 = h
        ((x1,y1),(x2,y2)) = self.GetBarRectangle()
        coords = [x1, y1, x1, y2, x2, y2, x2, y1]
        # draw the rectangle
        
        points = np.array([[x1,y1],[x1,y2],[x2,y2],[x2,y1]])
        cv2.fillPoly(image, pts=[points], color=(123,85,12))
        #self._canvas.create_polygon(coords, fill='#555555', outline='black')

    def __init__(self,data_model):
        
        self.data_model = data_model
        

    def InitGenBoard (self,screen):
        self.screen = screen
        cv2.setMouseCallback(self.screen.generated_board_window, self.mouse_callback)

    def GetMovement(self):
        return self.movement
    
    def ClearCommand(self):
        self.movement = []
        self.cur_movement = -1
        self.origin = -1
        state= self.STATE_SELECT_ORIGIN
    
    #25 for bar (regardless color)
    def IsColummnPopulated(self,col_num):

        bp_nodups = self.black.get_pieces() [:]
        bp_nodups = list(set(bp_nodups))
        if col_num+1 in bp_nodups:
            return True
        
        if col_num == 25:
            col_num = -1 #for white, bar is 0
        wp_nodups = self.white.get_pieces() [:]
        wp_nodups = list(set(wp_nodups))
        if col_num+1 in wp_nodups:
            return True
        return False


    def mouse_callback(self,event, x, y, flags, param):
        self.cur_x = x
        self.cur_y = y
        #print (event)
        self.mouse_column = self.GetClosestColumn((x,y))

        if event == cv2.EVENT_MOUSEMOVE:
            self.mouse_column = self.GetClosestColumn((x,y))

        if event == cv2.EVENT_LBUTTONDOWN:
            if self.state == self.STATE_SELECT_TARGET:
                #self.movement = (self.origin,self.mouse_column)
                self.movement[self.cur_movement][1] = self.mouse_column # + 1
                #self.movement[self.cur_movement][0] += 1
                self.state = self.STATE_SELECT_ORIGIN
                self.origin = -1
            elif self.state == self.STATE_SELECT_ORIGIN:

                if self.IsColummnPopulated(self.mouse_column):
                    self.cur_movement +=1
                    self.movement.append([self.mouse_column,-1])
                    self.origin = self.mouse_column
                    self.state = self.STATE_SELECT_TARGET

    def UpdateColumns(self):
        column_width = self.triangle_width
        column_height = self.triangle_height
        self.columns = []

        for column in range(12):
            bar_offset = 0
            if column > 5:
                bar_offset = self.bar_width
            column_pos_TL = ((column_width * 12+ self.bar_width - (column+1)*column_width - bar_offset),0)
            column_pos_BR = ((column_width * 12+ self.bar_width - (column+1)*column_width - bar_offset) + column_width,column_height)

            self.columns.append([column_pos_TL,column_pos_BR])

        for column in range(12):
            bar_offset = 0
            if column > 5:
                bar_offset = self.bar_width
            column_pos_TL = ((column_width * column + bar_offset),int(self.board_size[1]) - column_height)
            column_pos_BR = ((column_width * (column+1) + bar_offset),int(self.board_size[1]))
            self.columns.append([column_pos_TL,column_pos_BR])

    def GetClosestColumn(self,pos):
        if self.columns == 0 or self.columns == []:
            return -1
        for column in range(24):
            if self.columns[column][0][0] < pos[0] < self.columns[column][1][0] and self.columns[column][0][1] < pos[1] < self.columns[column][1][1]:
                return column
        
        bar_rect = self.GetBarRectangle()
        if bar_rect[0][0] < pos[0] < bar_rect[1][0] and bar_rect[0][1] < pos[1] < bar_rect[1][1]:
            return 25

        home_rect = self.GetHomeRectangle()
        if home_rect[0][0] < pos[0] < home_rect[1][0] and home_rect[0][1] < pos[1] < home_rect[1][1]:
            return 26


        return -1

    def DrawColumn(self,image,column,color):
        if column == -1:
            return
        if column == 25:
            rect = self.GetBarRectangle()
            cv2.rectangle(image, rect[0], rect[1], color, 2) 
        elif column == 26:
            rect = self.GetHomeRectangle()
            cv2.rectangle(image, rect[0], rect[1], color, 2) 
        else:   
            cv2.rectangle(image, self.columns[column][0], self.columns[column][1], color, 2)

    def DrawBoard(self,image):
        if image.shape[0] == 0 or image.shape[1] == 0:
            return
        for space in range(12):
            bar_offset = 0
            if space > 5:
                bar_offset = self.bar_width

            #triangle_color = '#C19A6B'
            triangle_color = self.color_yellow
            if space%2 == 0:
                #triangle_color = '#808080'
                triangle_color =self.color_blue
            
            p1 = [space * self.triangle_width +bar_offset, 0]
            p2 = [(space + 1) * self.triangle_width  + bar_offset, 0]
            p3 = [(space + .5) * self.triangle_width  + bar_offset, self.triangle_height]
            points = np.array([p1, p2,p3],dtype=np.int32)
            cv2.fillPoly(image, pts=[points], color=triangle_color)
            #self._canvas.create_polygon(space * self.triangle_width +bar_offset, 0, (space + 1) * self.triangle_width  + bar_offset, 0, (space + .5) * self.triangle_width  + bar_offset, self.triangle_height, fill = triangle_color)
        for s in range(12):
            bar_offset = 0
            if s > 5:
                bar_offset = self.bar_width

            #triangle_color = '#C19A6B'
            triangle_color = self.color_blue
            if s%2 == 0:
                #triangle_color = '#808080'
                triangle_color =self.color_yellow
            #Found .cget() function online at bytes.com
            p1 = [s * self.triangle_width + bar_offset, int(self.board_size[1])]
            p2 = [(s + 1) * self.triangle_width+ bar_offset, int(self.board_size[1])]
            p3 = [(s + .5) * self.triangle_width+ bar_offset, int(self.board_size[1])- self.triangle_height]
            points = np.array([p1,p2,p3],dtype=np.int32)
            cv2.fillPoly(image, pts=[points], color=triangle_color)

    def SetPieces(self,white_pieces,black_pieces):
        self.black.set_pieces(black_pieces)
        self.white.set_pieces(white_pieces)


    def InitBoardParams(self, window_size):
        self.board_size = window_size
        self.triangle_width = (int)(window_size[0]/13)
        self.triangle_height = (int)(window_size[1]/3)
        self.bar_width = (int)(0.025*window_size[0])
        
        self.black = Backgammon_Black()
        self.white = Backgammon_White()
        
       
        #black on the bar :
        self.black.set_pieces([2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 13, 25])
        self.white.set_pieces([12, 12, 12, 15, 19, 20, 20, 21, 22, 22, 22, 23, 23, 24, 24])
        #self.set_roll(2,4)

        """ 
        #white on the bar:
        self.black.set_pieces([1, 6, 6, 6, 6, 7, 8, 8, 8, 13, 13, 13, 13, 24, 24])
        self.white.set_pieces([0, 9, 12, 12, 12, 12, 16, 17, 17, 17, 19, 19, 19, 19, 23])
        self.set_roll(2,5)
        
        self.black.set_pieces([2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 10, 14])
        self.white.set_pieces([0, 1, 12, 19, 19, 20, 20, 22, 22, 22, 22, 23, 23, 24, 24])
        self.set_roll(1,2)"""

    def print_board(self):
        print ("black:")
        print(self.black)
        print ("white:")
        print(self.white)
        print ("dice:")
        #print(self.r)
    
    def SetPiecesFromData(self):
        self.black.set_pieces(self.data_model.black_pieces)
        self.white.set_pieces(self.data_model.white_pieces)
        

    def render(self):
        image = np.ones((self.board_size[0], self.board_size[1], 3), dtype=np.uint8) * 255
        if image.shape[0] == 0 or image.shape[1] == 0:
            return
        self.SetPiecesFromData()
        self.UpdateColumns()
        self.DrawBoard(image);  
        self.create_separator(image)      
        bp = self.black.get_pieces()
        bp_nodups = bp[:]
        bp_nodups = list(set(bp_nodups))
        rad = int(self.triangle_width / 2)
        for piece in bp_nodups:
            idx = [i for i,x in enumerate(bp) if x==piece]
            if piece <= 12:
                bar_offset = 0
                if piece <7:
                    bar_offset = self.bar_width
                for pos in range(len(idx)):
                    x_pos = int((12 - piece) * self.triangle_width + bar_offset + rad)
                    y_pos = int(pos * self.triangle_width +rad)
                    cv2.circle(image,(x_pos,y_pos),rad,self.color_black,-1)

            elif piece < 26:
                bar_offset = 0
                if piece >18:
                    bar_offset = self.bar_width
                for pos in range(len(idx)):

                    x_pos = int((piece - 12) * self.triangle_width+bar_offset - rad)
                    y_pos = int(int(self.board_size[1]) - ((pos + 1) * self.triangle_width) + rad)
                    cv2.circle(image,(x_pos,y_pos),rad,self.color_black,-1)
        wp = self.white.get_pieces()
        wp_nodups = wp[:]
        wp_nodups = list(set(wp_nodups))
        for piece in wp_nodups:
            #The following line was taken almost straight from stackoverflow (http://stackoverflow.com/questions/9542738/python-find-in-list)
            idx = [i for i,x in enumerate(wp) if x==piece]
            if piece <= 12:
                bar_offset = 0
                if piece <7:
                    bar_offset = self.bar_width
                for pos in range(len(idx)):
                    x_pos = (12 - piece) * self.triangle_width + bar_offset+ rad
                    y_pos = pos * self.triangle_width + rad
                    cv2.circle(image,(x_pos,y_pos),rad,self.color_black,-1)
                    cv2.circle(image,(x_pos,y_pos),rad-2,self.color_white,-1)
            elif piece < 26:
                bar_offset = 0
                if piece >18:
                    bar_offset = self.bar_width
                for pos in range(len(idx)):
                    x_pos = (piece - 12) * self.triangle_width+ bar_offset - rad
                    y_pos = int(self.board_size[1]) - ((pos + 1) * self.triangle_width) + rad
                    cv2.circle(image,(x_pos,y_pos),rad,self.color_black,-1)
                    cv2.circle(image,(x_pos,y_pos),rad-2,self.color_white,-1)
        
        self.DrawColumn(image,self.origin,(0,255,0))
        self.DrawColumn(image,self.mouse_column,(255,0,0))
            
        return image
        

    #red checkers - called black below:-/
    #black checkers - called white below:-/
    """ 31 tokens
	BlackBar, pos 1 - 24,                                                       WhiteBar, BlackHome,WhiteHome,turn,dice1,dice2
	"0          b2 0 0 0 0 w5 0 w3 0 0  0  b5 w5 0   0  0 b3 0  b5 0  0   0 0  w2 0         0           0      b   5      6" """
    "0           1 2 3 4 5 6  7 8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25        26          27     28  29    30"
    def create_game_string(self, dice1, dice2):

        #black bar - 25
        #white bar - 0
        bp = self.black.get_pieces()
        wp = self.white.get_pieces()
        board_string = ""

        #black bar
        board_string += "b" + str(wp.count(0)) + " "
        for i in range(1,25):
            if bp.count(i) > 0 :
                board_string += "w" + str(bp.count(i))
            elif wp.count(i) > 0:
                board_string += "b" + str(wp.count(i))
            else:    
                board_string += "0" 
            board_string += " "


        #white bar
        board_string += "w" + str(bp.count(25)) + " "

        #black home
        count = len([i for i in bp if i < 0])
        board_string += str(count) + " "

        #white home
        count = len([i for i in wp if i < 0])
        board_string += str(count) + " "


        #turn - black
        board_string += "w "

        #set dice
        board_string += (str)(dice1) + " "
        board_string += (str)(dice2) + " "
       
        board_string += str(count) + " "
        return board_string


