import re
import copy

from AuxFunctions import AuxFunctions
af = AuxFunctions ()

class DataModel:
    current_board_string = 0    #updated string of the board
    board_columns_count = []    #how many checkers in each column
    white_pieces = [] #one based
    black_pieces = [] #one based

    #CHECKER_RADIUS = 9.3    #9.3mm
    CHECKER_RADIUS = 0.325    
    #MAGNET_RADIUS = 10.1	#10.1mm 
    MAGNET_RADIUS = 0.33	#10.1mm 
    current_dice = 0
    
    num_of_strings = 20
    board_strings = 0
    cur_board_string_num = 0
    use_dice = True
    disable_robot = False
    board_left_rect = []
    board_right_rect = []

    dice = 0
    #current movement (from which column to which columns)
    movement = []
    #the current command to process
    command =""
    saved_state = 0

    max_subcommand = -1  #show only first subcommands
    
    current_image = 0 #for debug purposes

    #used to keep the position of the next checker to be picked from the column
    #last_checker = []   #screen coordinates

    all_checkers = []   #all checkers per column, used to calculate rectangle per column

    #this includes for each column, for a each number of checkers, their position
    all_checkers_cache = []


    bar_checkers = []   #2d array- [0] - white checkers, [1] - black checkers
    
    bar_checkers_black_cahce = []   #2d array- [0] - white checkers, [1] - black checkers
    bar_checkers_white_cahce = []   #2d array- [0] - white checkers, [1] - black checkers
    def __init__(self) -> None:
        self.board_strings = []
        self.current_dice = [1,3]
        for i in range(self.num_of_strings):
            self.board_strings.append("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        max_cols = 25
        max_rows = 15
        self.all_checkers_cache = [[None for _ in range(max_rows)] for _ in range(max_cols)]
        self.bar_checkers_black_cahce = [None,None,None,None,None,None,None,None,None,None,None,None,None]   #up to 12 checkers on bar are supported
        self.bar_checkers_white_cahce = [None,None,None,None,None,None,None,None,None,None,None,None,None]   #up to 12 checkers on bar are supported
        self.bar_checkers = [[],[]]

    def SaveState (self):
        all_checkers = self.all_checkers[:]
        self.saved_state = [copy.deepcopy(self.white_pieces),   #0
                            copy.deepcopy(self.black_pieces),   #1
                            self.current_board_string,          #2
                            copy.deepcopy(all_checkers),        #3
                            copy.deepcopy(self.bar_checkers),   #4
                            copy.deepcopy(self.black_pieces),   #5
                            copy.deepcopy(self.white_pieces),   #6
                            ]
        #print("saved state")
        #print (all_checkers)
        #print (self.all_checkers)
    def RestoreState(self):
        if self.saved_state == 0:
            print("cannot restore state")    
            return
        all_checkers = self.saved_state[3][:]
        self.white_pieces = copy.deepcopy(self.saved_state[0])
        self.black_pieces = copy.deepcopy(self.saved_state[1])
        self.current_board_string = self.saved_state[2]
        self.all_checkers = copy.deepcopy(all_checkers)
        self.bar_checkers = copy.deepcopy(self.saved_state[4])
        self.black_pieces = copy.deepcopy(self.saved_state[5])
        self.white_pieces = copy.deepcopy(self.saved_state[6])
        
        #print("restored state:")
        #print (self.all_checkers)
        
    
    def GetBarChecker(self,color):
        bar_idx = 0 if color == "w" else 1
        return self.bar_checkers[bar_idx][len(self.bar_checkers[bar_idx])-1]
    
    def GetColorForColumn(self,column):
        #white_pieces and black_pieces are one based, therefore, we need to add 1
        return 'w' if column+1 in self.white_pieces else 'b' if column+1 in self.black_pieces else '0'

    def RemoveBarChecker(self,color):
        bar_idx = 0 if color == "w" else 1
        self.bar_checkers[bar_idx].pop()

    def AddBoardString(self,string):
        self.board_strings[self.cur_board_string_num] = string
        self.cur_board_string_num = self.cur_board_string_num + 1
        if self.cur_board_string_num == self.num_of_strings:
            self.cur_board_string_num = 0

        self.current_board_string = self.ReduceNoise(self.board_strings)
        self.UpdateColumnsCount(self.current_board_string)

    def ReduceNoise(self,strings):
        # Split each string into sections
        sections = [s.split() for s in strings]

        # Get the length of each section
        section_lengths = [len(section) for section in sections]

        # Find the index of the longest section
        max_length_index = section_lengths.index(max(section_lengths))

        # Use the longest section as a reference
        reference_section = sections[max_length_index]

        # Initialize a list to store the most popular values for each section
        most_popular_values = []
        self.all_checkers = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        for i in range(len(reference_section)):
            values = [section[i] for section in sections]
            most_popular_value = max(set(values), key=values.count)
            most_popular_values.append(most_popular_value)
            #update all_checkers entry according to the most popular value



            if most_popular_value != '0':
                num_of_checkers = int(most_popular_value[1:]) # Convert the remaining string to an integer
                if i==0:    #black bar
                    self.bar_checkers[1] = self.bar_checkers_black_cahce[num_of_checkers]
                elif i==25:    #white bar
                    self.bar_checkers[0] = self.bar_checkers_white_cahce[num_of_checkers]
                else:
                    self.all_checkers[i-1] = self.all_checkers_cache[i-1][num_of_checkers]
                    #if i-1 == 18:
                    #    print ("set in 18:" + str(len(self.all_checkers[18])))

        # Join the most popular values to form the output string
        output_string = ' '.join(most_popular_values)
    
        return output_string

    #retruns the last checker for a given column
    def GetLastChecker(self,col):
        if self.all_checkers == []:
            return None
        if self.all_checkers[col] == None or self.all_checkers[col] == []:
            return None
        if col < 12:
            ret_val = max(self.all_checkers[col], key=lambda y: y[1])
        else:
            ret_val = min(self.all_checkers[col], key=lambda y: y[1])
        return ret_val
    
    def UpdateColumnsCount(self,board_str):
        # Define a regular expression pattern to match numbers
        pattern = r'\b\d+\b'

        pattern = re.compile(r'(b|w)?(\d+)')
        matches = pattern.findall(board_str)

        extracted_numbers = []
        for prefix, number in matches[1:-1]:  # Exclude the first and last sections
            if prefix == 'b' or prefix == 'w':
                extracted_numbers.append(int(number))
            else:
                extracted_numbers.append(0)


        self.board_columns_count = extracted_numbers

    def AddCheckerToBar(self,pos,color):
        self.bar_checkers[0 if color == 'w' else 1].append(pos)
        

    #during movement, it needs to upate the column from which it took, to calculate the movement to the target column
    #the reason is that in some cases (adjascent columns), there's a connection between the from_col and the position to go to put the checker in the target column
    def RemoveCheckerFromColumn(self,from_col):
        if from_col == 25 or from_col == 26:
            self.RemoveBarChecker('w' if from_col == 26 else 'b')
        else:
            color = self.GetColorForColumn(from_col)
            (self.white_pieces if color == 'w' else self.black_pieces).remove(from_col+1)
            self.all_checkers[from_col].remove(self.GetLastChecker(from_col))

        #print ("checker removed")

    def AddCheckerToTargetColumn(self,to_col,last_pos,color):
        if to_col in (26,27):    #home, no need to add
            return 
        self.all_checkers[to_col].append(last_pos)
        #color = self.GetColorForColumn(to_col)
        (self.white_pieces if color == 'w' else self.black_pieces).append(to_col+1)
        #self.last_checker[to_col] = last_pos
        

    def UpdateBoardFromCamera(self,input_string):
        if self.command != "" and self.command != 0:
            return
        # Initialize empty lists for white and black players
        self.white_pieces = []
        self.black_pieces = []
        self.AddBoardString(input_string)
        

        # Split the input string by spaces
        pieces = self.current_board_string.split()
        counter = 0
        for piece in pieces:
            # Separate the color (w or b) and the number (e.g., w3 -> color='w', number=3)
            color = piece[0]
            piece_num_str = piece[1:]
            number = 0
            if (len(piece_num_str) > 0):
                number = int(piece_num_str)
                for i in  range (number):
                    # Append the number to the corresponding list
                    if color == 'w':
                        self.white_pieces.append(counter)
                    elif color == 'b':
                        self.black_pieces.append(counter)
            counter = counter + 1
        #print ("white =" + str(self.white_pieces))
        #print ("black =" + str(self.black_pieces))

        
    def IsMovementAllowed(self,pos):
        return True

    def UpdateBoardRects(self,board_left_rect,board_right_rect):
        self.board_left_rect = board_left_rect
        self.board_right_rect = board_right_rect

    def CreateGameStringForGNUBG(self):
        bp = self.black_pieces
        wp = self.white_pieces

        board_string = "set board simple "
        board_string += str(wp.count(25)) + " "

        #for i in range(24,0,-1):
        for i in range(1,25):
            if bp.count(i) > 0 :
                board_string += "-" +str(bp.count(i))
            elif wp.count(i) > 0:
                board_string +=  str(wp.count(i))
            else:    
                board_string += "0" 
            board_string += " "

        board_string += str(bp.count(0)) + " "
        
        return board_string
        

    """ 31 tokens
        BlackBar, pos 1 - 24,                                                       WhiteBar, BlackHome,WhiteHome,turn,dice1,dice2
        "0          b2 0 0 0 0 w5 0 w3 0 0  0  b5 w5 0   0  0 b3 0  b5 0  0   0 0  w2 0         0           0      b   5      6" 
        "0           1 2 3 4 5 6  7 8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25        26          27     28  29    30"
    """
    #turn can be 'b' or 'w'
    def CreateGameStringForAI(self,dice,turn):
        #black bar - 25
        #white bar - 0
        #bp = self.data_model.black_pieces.get_pieces()
        #wp = self.data_model.white_pieces.get_pieces()
        bp = self.black_pieces
        wp = self.white_pieces

        board_string = ""

        #black bar
        board_string += "b" + str(bp.count(0)) + " "


        for i in range(1,25):
            if bp.count(i) > 0 :
                board_string += "b" + str(bp.count(i))
            elif wp.count(i) > 0:
                board_string += "w" + str(wp.count(i))
            else:    
                board_string += "0" 
            board_string += " "


        #white bar
        board_string += "w" + str(wp.count(25)) + " "

        #black home
        count = len([i for i in bp if i < 0])
        board_string += str(count) + " "

        #white home
        count = len([i for i in wp if i < 0])
        board_string += str(count) + " "


        #turn - white
        board_string += str(turn) + " "

        #set dice
        board_string += (str)(dice[0]) + " "
        board_string += (str)(dice[1]) + " "
       
        board_string += str(count) + " "
        return board_string

    def PrintBoard(self):
        print ("black:")
        print(self.black_pieces)
        print ("white:")
        print(self.white_pieces)
        print ("dice:")

