# BotGammon
A solution for a robot that plays Backgammon.

The solution includes the following:
- Board detection (to detect checkers on board)
- Dice detection (NN that recognizes the dice)
- Interface with GNUBG CLI (for the auto player)
- Board Management - create movements on the board
- Some Arduino sketches:
  - Arduino Manager - that gets instructions from the main PC and send them over to GRBL or UI
  - I2C to Serial - a converter from I2C protocol to Serial (there're not enough Serial ports on the arduino)
  - RGB Led Matrix - for the UI
