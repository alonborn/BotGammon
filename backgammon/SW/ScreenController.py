from GeneratedBoard import GeneratedBoard
import cv2

class ScreenController:

    board_window = 'Board'
    dice1_window = 'Dice1'
    dice2_window = 'Dice2'
    generated_board_window = 'GenBoard'
    data_model = 0
    generated_board = 0


    board_image = 0
    generated_board_image = 0

    dice1_image = 0
    dice1_canny_edges_image = 0
    dice1_blurred_image = 0
    dice1_mask_image = 0

    def __init__(self,data_model) -> None:
        self.data_model = data_model
        self.generated_board = GeneratedBoard(data_model)
        cv2.namedWindow(self.board_window, cv2.WINDOW_NORMAL)

        cv2.moveWindow(self.board_window,0,0)
        cv2.resizeWindow(self.board_window, 720, 600)

        """cv2.namedWindow(self.dice1_window, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.dice1_window,0,550)
        cv2.resizeWindow(self.dice1_window, 100, 100)"""

        cv2.namedWindow(self.generated_board_window, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.generated_board_window,720,0)
        cv2.resizeWindow(self.generated_board_window, 600, 600)
    
    def PrepareWindows(self):
        window_size = cv2.getWindowImageRect(self.generated_board_window)
        self.generated_board.InitBoardParams((window_size[2],window_size[3]))
        self.generated_board.InitGenBoard(self)
        self.generated_board_image = self.generated_board.render()

    def InitWindows(self):
        self.generated_board.InitGenBoard(self)


    def ShowWindows(self):
       
        cv2.imshow(self.board_window, self.board_image) 
        #cv2.imshow(self.dice1_window, self.dice1_image) 
        cv2.imshow(self.generated_board_window, self.generated_board_image) 

        return cv2.waitKey(2)

    def ArrangeDiceWindows(self,dice_image):

        height, width, _ = dice_image.shape
        cropped1_image = dice_image[0:height, 0:int(width/2)]

        self.screen_controller.dice1_image = cropped1_image

    def ShowCalculatedBoard(self):
        pass
    def ShowBoard(self):
        pass

