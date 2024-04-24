import cv2
import time
import random

from AuxFunctions import AuxFunctions
af = AuxFunctions ()

class DiceController:

    use_dice = True

    camera = 0
    arduino = 0
    data_model = 0
    screen = 0
    loaded_model = 0
    
    def __init__(self, camera,arduino,data_model,screen,use_dice):    
        self.camera = camera
        self.arduino = arduino
        self.data_model = data_model
        self.screen = screen
        self.use_dice = use_dice
        if use_dice:
            self.LoadModel()


    
    def WaitForStabilization(self):
        for i in range(20):
            self.camera.TakeDiceSnapshot()
            self.screen.ShowWindows()
            #print ("stabilizing" + str(i))
            cv2.waitKey(1)

    def LoadModel(self):
        import torchvision.models as models
        from DicePrediction import load_model
        model_path = 'dice_recognizer_model.pth'  # Path to your trained model

        # Load the model
        self.loaded_model = load_model(model_path)

    def SendRollDiceCommand(self):
        if self.use_dice == False:
           return
        
        self.arduino.RollDice()


    def RecognizeDice(self):
        if self.use_dice == False:
            time.sleep(3)
            return (random.randint(1, 6),random.randint(1, 6))
        
        from DicePrediction import predict_label
        #self.arduino.RollDice()
        #time.sleep(4)
        dice_image = self.camera.TakeDiceSnapshot()
        filename = "C:\\temp\dice_image.jpg"
        cv2.imwrite(filename, dice_image)

        filename2 = "C:\\dice\\" + str(af.FindMissingNumber("c:\\dice","jpg"))+".jpg"
        cv2.imwrite(filename2, dice_image)

        dice_predictions = predict_label(self.loaded_model,filename)
        existing_text = str(dice_predictions[0]) + ":" + str(dice_predictions[1])
        cv2.putText(dice_image, existing_text, (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        #cv2.imshow("predictions", dice_image) 
        cv2.waitKey(2)
        return dice_predictions
    
    """def RollDice(self):
        if self.use_dice == False:
            time.sleep(3)
            return (random.randint(1, 6),random.randint(1, 6))
        
        from DicePrediction import predict_label
        self.arduino.RollDice()
        time.sleep(4)
        dice_image = self.camera.TakeDiceSnapshot()
        filename = "C:\\temp\dice_image.jpg"
        cv2.imwrite(filename, dice_image)
        dice_predictions = predict_label(self.loaded_model,filename)
        existing_text = str(dice_predictions[0]) + ":" + str(dice_predictions[1])
        cv2.putText(dice_image, existing_text, (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow("predictions", dice_image) 
        cv2.waitKey(2)
            
        return dice_predictions"""

