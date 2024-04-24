import subprocess
import re

#                 Bar(b) 23 22  21  20  19  18  17  16  15  14  13  12  11  10  9  8  7  6  5  4  3  2  1  Bar (w)
#set board simple   1    0  1   3   -4  -1   0   1  2   0   0    0   0   1   -1 0  0  2  2  0  0  0  0  0    3
# +  Human
# -  GNUBG

class GNUBG:

    gnubg_process = 0
    data_model = 0
    def __init__(self,data_model) -> None:
        self.InitNewGame()
        self.data_model = data_model
    
    def InitNewGame(self):
        self.gnubg_process = subprocess.Popen(['C:\\Program Files (x86)\\gnubg\\gnubg-cli'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.gnubg_process.stdout.flush()
        self.gnubg_process.stdin.write("new game\n")
        self.gnubg_process.stdin.flush()
        
        self.read_board(self.gnubg_process)
        self.read_board(self.gnubg_process)  #there are two boards

    def remove_asterix(self,input_str):
        moves = []
        last_dest = ""
        for move in input_str.split('*'):
            if len(move) > 0 and move[0] != ".":    #second section in : gnubg moves 24/18*.\n
                # Split move into source and destination
                source, dest = move.split('/')
                if source == "":
                    source = last_dest
                moves.append(f"{source}/{dest}")
                last_dest = dest
        return ' '.join(moves)

    def extract_double_movement(self,sections):
        retval = []
        for section in sections:
            if section.find('(') > -1:
                matches = section.split("(")
                # Find all matches in the input string
                #matches = re.findall(pattern, section)
                
                count = int(matches[1][0])
                for i in range(count):
                    retval.append(matches[0])
            else:
                retval.append(section)
        return retval

    def extract_moves(self,line):
        moves = []
        print (line)
        sections = line.split(" ")
        # Regular expression pattern to match moves
        sections = sections[2:]
        #pattern = re.compile(r'(\d+)/(\d+)(?:\((\d+)\))?(?:\s|$)')
        #pattern = re.compile(r'(\d+)/(\d+)(?:\((\d+)\))?')
        pattern = re.compile(r'(bar|\d+)/(b|off|\d+)(?:\((\d+)\))?')

        sections = self.extract_double_movement(sections)
     
        # Iterate through each section
        for section in sections:
            section = self.remove_asterix(section)
            # Find all matches in the section
            
            inner_sections = section.split(" ")    #in case of asterix, there might be inner sections, like 'gnubg moves 9/7*/5*/3 6/4.\n' turns to two sections, and the first section is '9/7 7/5 5/3' after removing the asterix

            for inner_section in inner_sections:
                if inner_section not in ("gnubg","moves"):
                    matches = re.findall(pattern, inner_section)
                    # Process each match
                    for match in matches:
                        source = 25 if match[0] == "bar" else int(match[0]) #26 is white bar
                        destination = 26 if match[1] == 'off' else int(match[1])    #27 is home
                        count = 1
                        if len(match) > 2:
                            count = int(match[2]) if match[2] else 1
                        
                        # Append each move to the list
                        for _ in range(count):
                            moves.append([source, destination])
        
        return moves

    def read_board(self,gnu_prc):
        read_more_lines = True
        while read_more_lines == True:
            line = self.read_gnu_line()
           
            if line.find("+12-11-10--9--8--7-") != -1:    #last line of board
                read_more_lines = False

    def read_movement(self,gnu_prc):
        read_more_lines = True
        line = 0
        while read_more_lines == True:
            line = self.read_gnu_line()
            
            if line.find("gnubg moves") != -1:
                read_more_lines = False
            if line.find("gnubg cannot") != -1:
                return None
        return self.extract_moves(line)
    
    def read_gnu_line(self):
        line = self.gnubg_process.stdout.readline()
        #print(line)
        return line

    def CalcNextMove(self,dice):
        board_string = self.data_model.CreateGameStringForGNUBG()
        # Initialize a new game

        print (board_string)        
        self.gnubg_process.stdin.write("set turn gnubg\n")
        self.gnubg_process.stdin.flush()
        line  = self.read_gnu_line()
        line  = self.read_gnu_line()
        assert line.find("now on roll") != -1

        self.gnubg_process.stdin.write(f"set dice {dice[0]} {dice[1]}\n")
        self.gnubg_process.stdin.flush()
        assert self.read_gnu_line().find("The dice have been set") != -1

        self.gnubg_process.stdin.write(board_string + "\n")
        self.gnubg_process.stdin.flush()
        line = self.read_gnu_line()
        assert line.find("GNU Backgammon") != -1
        self.read_board(self.gnubg_process)

        self.gnubg_process.stdin.write(f"play\n")
        self.gnubg_process.stdin.flush()

        #self.read_board(self.gnubg_process)
        movement = self.read_movement(self.gnubg_process)
        self.read_board(self.gnubg_process)
        return movement


