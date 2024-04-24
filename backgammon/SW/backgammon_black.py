'''Creates a class for black backgammon pieces
Created Spring 2017
@author: Nate Gamble (neg6)
'''
class Backgammon_Black:
    def __init__(self):
        self._pieces = [6, 6, 6, 6, 6,
                        8, 8, 8,
                        13, 13, 13, 13, 13,
                        24, 24]
    #black bar - 25
    #white bar - 0

    #white home - 25
    #black home - 0

    def get_pieces(self):
        return self._pieces
    
    def set_pieces(self, list_of_pieces):
        self._pieces = list_of_pieces
        self.order()
    
    def move_piece(self, distance, piece, other):
        if distance <= 0:
            raise ValueError('Distance must be greater than 0')
        if piece != 25 and self.capturedPiece():
            raise ValueError('You must move your captured piece first')
        if piece in self._pieces:
            idx = self._pieces.index(piece)
            if self.validMove(piece - distance, other):
                self._pieces[idx] = piece - distance
            else:
                raise ValueError('That is an invalid place to move your piece')
        else:
            raise ValueError('The chosen piece is not valid')
        self.capture(other)
        self.order()
        
    def order(self):
        self._pieces.sort()
    
    def __str__(self):
        return 'Your pieces are at: ' + str(self._pieces)
    
    def capturedPiece(self):
        if 25 in self._pieces:
            return True
        else:
            return False
        
    def capture(self, other):
        op = other.get_pieces()[:]
        for piece in self._pieces:
            if piece in op:
                op[op.index(piece)] = 0
        other.set_pieces(op)

    def validMove(self, position, other):
        res = 0
        #The following line was taken almost straight from stackoverflow (http://stackoverflow.com/questions/9542738/python-find-in-list)
        idx = [i for i,x in enumerate(other.get_pieces()) if x==position] 
        if len(idx) <= 1 or position == 0: #if there is only one piece at the position and it is not the white bar
            res += 1
        if position <= 0:
            if self._pieces[14] <= 6: #id all checkers are in the home board
                res += 1
        else:
            res += 1
        if res == 2:
            return True
        else:
            return False
    
    def win(self):
        return self._pieces == [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
    
    
if __name__ == '__main__':
    #No tests here because all tests are in backgammon_white.py and almost all of it is the same
    a = Backgammon_Black()