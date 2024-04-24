import DataModel as DataModel
import BackgammonBridge as BackgammonBridge

class AutoPlayer:
    data_model = 0
    def __init__(self,data_model) -> None:
        self.data_model = data_model
        BackgammonBridge.InitGame()

    #turn can be 'b' or 'w'
    def CalcNextMove(self,dice,turn):
    
        board_string = self.data_model.CreateGameStringForAI(dice,turn)
        #board_string = "b0 0 b1 0 0 0 w5 b1 w3 0 0 0 b5 w5 0 0 0 b3 0 b5 0 0 0 0 w2 w0 0 0 w 6 4 0 "

        print("board:" + board_string)
        BackgammonBridge.SetBoardForAI (board_string)
        self.data_model.PrintBoard()
        next_move = str(BackgammonBridge.GetNextMove (board_string).decode('utf-8').strip("\n"))
        if next_move == "":
            #no moves found (stay in bar), end turn
            print ("couldnt find a move for dice:")
            print(str(self.data_model.current_dice[0]) + ",", str(self.data_model.current_dice[1]))
            return None
        else:
            #print("found moves for dice:")
            #print(str(self.data_model.current_dice[0]) + ",", str(self.data_model.current_dice[1]))
            next_move = next_move.replace('b', '0' if turn == 'b' else '25')
            next_move = next_move.replace('o', '27')
            split_parts = next_move.split('X')
            # Process each part and create a list of lists
            result_list = [list(map(int, part.split('-'))) for part in split_parts]
            return result_list 
        


        

