import ctypes

my_dll = ctypes.CDLL(r'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\SW\\BackgammonGame\\BackgammonLib\\x64\\Debug\\BackgammonLib.dll')
#my_dll = ctypes.CDLL(r'C:\\temp\\BackgammonLib.dll')
                     
import ctypes


# Get a list of all the exported functions
exported_functions = [func for func in dir(my_dll) if callable(getattr(my_dll, func))]

#print(exported_functions)

"""RunGame = my_dll.RunGame
RunGame.argtypes = []
RunGame.restype = ctypes.c_void_p
RunGame()"""

# Print the result

def InitGame():
    InitGame = my_dll.InitGame
    InitGame.argtypes = []
    InitGame.restype = ctypes.c_void_p
    InitGame()

def SetBoardForAI(board):
    SetBoard = my_dll.SetBoard
    SetBoard.argtypes = [ctypes.c_char_p]
    SetBoard.restype = ctypes.c_void_p
    SetBoard(board.encode())

def GetNextMove(board):
    NextMove = my_dll.GetNextMove
    NextMove.argtypes = [ctypes.c_char_p]
    NextMove.restype = ctypes.c_char_p
    encodedBoard = board.encode()
    retVal = NextMove(encodedBoard )
    return retVal

# Free the memory allocated by the DLL
#my_dll.free(result)

            
