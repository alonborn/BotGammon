//#include <Wire.h>
#include <RGBmatrixPanel.h>
#include "bitmaps.h"
#include "DICE_1.h"

#define CLK 11
#define OE 9
#define LAT 10
#define A A0
#define B A1
#define C A2
#define D A3

RGBmatrixPanel matrix(A, B, C, D, CLK, LAT, OE, true, 64);



#define SLAVE_ADDRESS 0x10 // Change this to your slave address
#define MAX_STRING_LENGTH 7

#define num_balls 4
int8_t ball[num_balls][4] = {
  {  3,  0,  1,  1 },
  { 17, 15,  1, -1 },
  { 27,  4, -1,  1 },
  { 12,  9, -1,  -1 }
};

static const uint16_t PROGMEM ballcolor[num_balls] = 
{
  0x0080, // Green=1
  0x0002, // Blue=1
  0x1000,  // Red=1
  0x4444
};

static uint32_t previousTime = 0;
static float previousColorFactor = 0.0;
static bool colorDirection = true;
int16_t hue = 0;

const int MATRIX_WIDTH = 64;
const int MATRIX_HEIGHT = 32;

// Use a character array in RAM for dynamic text
char text[20] = "OK";
char text2[51] = "OK";

int16_t textX = 10; 
int16_t text2X = 10; 

int textMin =0;
int16_t text2Min =0;

unsigned long startTime;





#define STATE_RECT 1
#define STATE_ROTATE_RECT 2
#define STATE_ROLL_DICE 3
#define STATE_DICE_NUM 4
#define STATE_START 5
#define STATE_VICTORY 6
#define STATE_LOST 7
#define STATE_SCROLL_TEXT 8
#define STATE_JUST_TEXT 9
#define STATE_JUST_TEXT2 10
#define STATE_BOUNCING_BALL 11
#define STATE_RANDOM_DOTS 12
#define STATE_STARS 13
#define STATE_CHECKERS 14
#define STATE_SNAKE 15

#define STATE_START_GAME_DICE 16

int current_state = 0;

int16_t dice[4] = {(int16_t)0,(int16_t)0,(int16_t)0,(int16_t)0};
const uint16_t * dice_bmp[4] = {NULL,NULL,NULL,NULL};

void SetCurrentState (String cur_state_str)
{
  if (cur_state_str.startsWith("RECT")) 
  {
      current_state = STATE_RECT;
  } 
  else if (cur_state_str.startsWith("ROTATE_RECT"))
  {
    current_state = STATE_ROTATE_RECT;
  } 
  else if (cur_state_str == "ROLL_DICE") 
  {
    current_state = STATE_ROLL_DICE;
  } 
  else if (cur_state_str.startsWith("SCROLL_TEXT"))
  {
    current_state = STATE_SCROLL_TEXT;
  } 
  else if (cur_state_str.startsWith("JUST_TEXT"))
  {
    current_state = STATE_JUST_TEXT;
  }
  else if (cur_state_str.startsWith("VICTORY"))
  {
    current_state = STATE_VICTORY;
  } 
  else if (cur_state_str.startsWith("LOST"))
  {
    current_state = STATE_LOST;
  } 
  else if (cur_state_str.startsWith("BOUNCING"))
  {
    current_state = STATE_BOUNCING_BALL;
  }
  else if (cur_state_str.startsWith("RAND_DOTS"))
  {
    current_state = STATE_RANDOM_DOTS;
  }
  else if (cur_state_str.startsWith("STARS"))
  {
    current_state = STATE_STARS;    
  }
  else if (cur_state_str.startsWith("CHECKERS"))
  {
    current_state = STATE_CHECKERS;
    initCheckers();
  }
  else if (cur_state_str.startsWith("SNAKE"))
  {
    current_state = STATE_SNAKE;
    initSnake();
  }
  else if (cur_state_str.startsWith("START_DICE"))
  {
    current_state = STATE_START_GAME_DICE;
  }  
  Serial.println ("Current State = " + String(current_state));
}

void displayVictoryScreen() {
  Serial.println("showing vicotry");
  static int16_t offset = 0;      // Variable to control the scrolling offset
  static int16_t hueShift = 0;    // Variable to control the hue shift
  static int16_t textHueShift = 0;// Variable to control the hue shift for text color
  static int16_t textX = 0;       // Variable to control the position of the scrolling text

  // Fill the screen with pixels, each having a gradually changing color
  for (int16_t y = 0; y < matrix.height(); y++) {
    for (int16_t x = 0; x < matrix.width(); x++) {
      // Calculate hue based on pixel position, offset, and hue shift
      int16_t hue = map(x + y + offset + hueShift, 0, matrix.width() + matrix.height(), 0, 1536);
      matrix.drawPixel(x, y, matrix.ColorHSV(hue, 255, 255, true));
    }
  }

  matrix.setTextSize(1);

  // Calculate hue for text color based on time
  int16_t textHue = (textHueShift + millis() / 10) % 1536;

  matrix.setTextColor(matrix.ColorHSV(textHue, 0, 0, true)); // Set text color with changing hue
  matrix.setTextWrap(false);
  matrix.setCursor(7, 13); // Use matrix.height() / 2 to center the text vertically
  matrix.print("VICTORY!!");

  // Increment the offset, hue shift, and text hue shift with adjustable speeds
  offset += 10;               // Adjust the speed of rotation (higher increment = faster)
  hueShift += 10;             // Adjust the speed of hue change (higher increment = faster)
  textHueShift += 7;         // Adjust the speed of text hue change (higher increment = faster)

  // Increment the textX position for scrolling
  textX -= 1;                // Adjust the speed of scrolling (higher increment = faster)

  // Reset the offset, hue shifts, and textX when they reach the width of the matrix
  if (offset >= matrix.width()) {
    offset = 0;
  }
  if (hueShift >= 1536) {
    hueShift = 0;
  }
  if (textX < -matrix.width()) {
    //textX = matrix.width();  // Reset the textX to restart scrolling
    textX = 50;
  }

  matrix.swapBuffers(false);
}


#define MAX_MESSAGE_LENGTH 80
#define CHUNK_SIZE 30

char tmp_message[MAX_MESSAGE_LENGTH + 1]; // +1 for the null terminator

void ReadStringFromSerial()
{
  //Serial.println("trying to read from serial");
  if (Serial1.available())
  {
    Serial.println("serial1 is available!!");
    //int msg = Serial1.read();
    String msg = Serial1.readStringUntil('\n');
    strncpy(tmp_message,msg.c_str(),MAX_MESSAGE_LENGTH);
    Serial.println(String("read: ") + String(msg));
    ParseLine(tmp_message);
  }
}

/*void receiveEvent(int numBytes) {
  char isLastChunk = Wire.read(); // Read the flag indicating if this is the last chunk

  char chunk[CHUNK_SIZE];
  int chunkLength = 0;

  while (Wire.available() && chunkLength < CHUNK_SIZE) {
    chunk[chunkLength++] = Wire.read(); // Receive a byte as character
  }

  chunk[chunkLength] = '\0'; // Null-terminate the chunk

  strncat(tmp_message, chunk, MAX_MESSAGE_LENGTH - strlen(tmp_message)); // Concatenate chunk to tmp_message

  // If this is the last chunk or tmp_message is full, process the complete message
  if (isLastChunk == '1' || strlen(tmp_message) == MAX_MESSAGE_LENGTH) {
    Serial.print("Received *COMPLETE* message: ");
    Serial.println(tmp_message);
    ParseLine(tmp_message);
    tmp_message[0] = '\0'; // Reset the receivedMessage for the next message
  } else {
    Serial.print("Received PARTIAL message: ");
    Serial.println(tmp_message);
  }
}*/

void Add2Dice ()
{
  if (dice[0] != NULL)
    matrix.drawRGBBitmap(49,25, dice_bmp[0] , 7,7);
  if (dice[1] != NULL)
    matrix.drawRGBBitmap(57,25, dice_bmp[1] , 7,7);
}

// Define constants
const int NUM_CHECKERS = 5; // Number of checkers
const int CHECKER_SIZE = 2; // Size of each checker (in pixels)

// Structure to represent a checker
struct Checker {
    uint8_t x;
    uint8_t y;
    uint8_t dx;
    uint8_t dy;
    uint8_t red;
    uint8_t green;
    uint8_t blue;
};
// Array to store checkers
Checker checkers[NUM_CHECKERS];

// Function to initialize checkers
void initCheckers() 
{
    for (int i = 0; i < NUM_CHECKERS; ++i) {
        checkers[i].x = random(MATRIX_WIDTH / CHECKER_SIZE); // Initialize within board bounds
        checkers[i].y = random(MATRIX_HEIGHT / CHECKER_SIZE); // Initialize within board bounds
        checkers[i].dx = random(3) - 1; // Random movement direction (-1, 0, 1)
        checkers[i].dy = random(3) - 1; // Random movement direction (-1, 0, 1)

        if (checkers[i].dx == 0 && checkers[i].dy == 0){
          checkers[i].dx = 2;
          checkers[i].dy = -2;
        }

        checkers[i].red = (uint8_t)(random(256)); // Random red component
        checkers[i].green = (uint8_t)(random(256)); // Random green component
        checkers[i].blue = (uint8_t)(random(256)); // Random blue component
    }
}

// Function to update checkers
void updateCheckers() {
    for (int i = 0; i < NUM_CHECKERS; ++i) {
        // Update checker position
        checkers[i].x += checkers[i].dx;
        checkers[i].y += checkers[i].dy;

        // Check for boundary collision and reverse direction if necessary
        if (checkers[i].x <= 0 || checkers[i].x >= MATRIX_WIDTH / CHECKER_SIZE - 1) {
            checkers[i].dx *= -1;
        }
        if (checkers[i].y <= 0 || checkers[i].y >= MATRIX_HEIGHT / CHECKER_SIZE - 1) {
            checkers[i].dy *= -1;
        }
    }
}

void drawCheckers() {
    // Clear the matrix
    matrix.fillScreen(0);

    // Draw each checker
    for (int i = 0; i < NUM_CHECKERS; ++i) {
        int checkerX = checkers[i].x * CHECKER_SIZE;
        int checkerY = checkers[i].y * CHECKER_SIZE;
        matrix.fillRect(checkerX, checkerY, CHECKER_SIZE, CHECKER_SIZE, matrix.Color888(checkers[i].red, checkers[i].green, checkers[i].blue));
    }
    AddText();
    // Swap buffers to display the drawing
    matrix.swapBuffers(false);
}


void AddText() 
{
    int textLength = strlen(text);
    int text2Length = strlen(text2);
    
    int16_t y =0;

    if (String(text2) == String(""))
    {
      y = 12; // Each character is 8 pixels tall
    }
    else
    {
      y = 5;
    }

    //if (String(text2) != "")
    //  y= 5;

    // Define the period for color change (in milliseconds)
    const int colorChangePeriod = 1000; // 2 seconds
    // Get the current time
    unsigned long currentTime = millis();
    // Calculate the time elapsed since the last call
    unsigned long elapsedTime = currentTime - previousTime;
    // Calculate the color interpolation factor based on time
    float colorFactor;
    if (colorDirection) {
        colorFactor = previousColorFactor + float(elapsedTime) / colorChangePeriod;
        if (colorFactor > 1.0) {
            colorFactor = 1.0;
            colorDirection = false;
        }
    } else {
        colorFactor = previousColorFactor - float(elapsedTime) / colorChangePeriod;
        if (colorFactor < 0.0) {
            colorFactor = 0.0;
            colorDirection = true;
        }
    }

    // Interpolate between black and white based on the color factor
    uint8_t red = (1 - colorFactor) * 0 + colorFactor * 7;
    uint8_t green = (1 - colorFactor) * 0 + colorFactor * 7;
    uint8_t blue = (1 - colorFactor) * 0 + colorFactor * 7;
    // Set text color
    matrix.setTextColor(matrix.Color333(red, green, blue));
    // Draw the text
    matrix.setCursor(textX, y);
    //Serial.println("X" + String(x) + "," + String(y) + "  " + String(text));
    matrix.print(text);

    if (String(text2) != "")
    {
      if (text2Length > 10)
      {
        matrix.setTextColor(matrix.Color333(100, 100, 100));
        text2Min -=1;
        if (text2Min <=(-text2Length) * 7 + 4) 
          text2Min = 50;

        matrix.setTextColor(matrix.ColorHSV(hue, 255, 255, true));
        hue += 7;
        if(hue >= 1536) hue -= 1536;

        matrix.setCursor(text2Min, y+16);
        //matrix.setCursor(0, y+16);
        //String text2_full = String (text2) + " " + String (text2);
        char* text2_full = text2;
        matrix.print(text2_full);
      }
      else
      {
        matrix.setCursor(text2X, y+16);
        matrix.print(text2);
      }
    }
    // Swap buffers to display the drawing
    
    // Update previous time and color factor
    previousTime = currentTime;
    previousColorFactor = colorFactor;
    UpdateDiceBMP();
    Add2Dice();
}



//-------------------------------------------------------------
//<mode>:<str1>:<x1>:<str2>:<x2>:<dice1>:<dice2>
//"STARS:ALON:13:BOREN:50:3:1"
void ParseLine(const char* line) {
  Serial.print("parsing line:");
  Serial.print(line);
  
  // Find the first colon
  const char* firstColonPtr = strchr(line, ':');
  if (firstColonPtr == NULL) {
    // No colon found, return
    Serial.println("no colon found");
    return;
  }
  
  // Extract the first section
  char string1[12]; // Assuming maximum length of 50 characters
  int length = firstColonPtr - line;
  strncpy(string1, line, length);
  string1[length] = '\0'; // Null-terminate the string
  
  // Find the second colon
  const char* secondColonPtr = strchr(firstColonPtr + 1, ':');
  if (secondColonPtr == NULL) {
    // No second colon found, return
    return;
  }
  
  // Extract the second section
  char string2[20]; // Assuming maximum length of 50 characters
  length = secondColonPtr - firstColonPtr - 1;
  strncpy(string2, firstColonPtr + 1, length);
  string2[length] = '\0'; // Null-terminate the string
  
  // Extract the first number
  int num1 = atoi(secondColonPtr + 1);
  
  // Find the third colon
  const char* thirdColonPtr = strchr(secondColonPtr + 1, ':');
  if (thirdColonPtr == NULL) {
    // No third colon found, return
    return;
  }
  
  const char* fourthColonPtr = strchr(thirdColonPtr + 1, ':');
  if (thirdColonPtr == NULL) {
    // No third colon found, return
    return;
  }

  // Extract the third section
  char string3[55]; // Assuming maximum length of 50 characters
  length = fourthColonPtr - thirdColonPtr - 1;
  strncpy(string3, thirdColonPtr + 1, length);
  string3[length] = '\0'; // Null-terminate the string
  
  // Extract the second number
  int num2 = atoi(fourthColonPtr + 1);

  // Extract the third number
  int num3 = atoi(strchr(fourthColonPtr + 1, ':') + 1);

  // Extract the fourth number
  int num4 = atoi(strchr(strchr(fourthColonPtr + 1, ':') + 1, ':') + 1);

  SetCurrentState(string1);
  Serial.print("string1:");
  Serial.print(string1);
  Serial.print("|string2:");
  Serial.print(string2);
  Serial.print("|string3:");
  Serial.print(string3);
  Serial.print("|num1:");
  Serial.print(num1);
  Serial.print("|num2:");
  Serial.print(num2);
  Serial.print("|num3:");
  Serial.print(num3);
  Serial.print("|num4:");
  Serial.println(num4);

  if (current_state == STATE_START_GAME_DICE) {
    dice[0] = atoi(string2);
    dice[1] = num1;
    dice[2] = atoi(string3);
    dice[3] = num2;

    Serial.print("dice1 = ");
    Serial.print(dice[0]);
    Serial.print(" dice2 = ");
    Serial.print(dice[1]);
    Serial.print(" dice3 = ");
    Serial.print(dice[2]);
    Serial.print(" dice4 = ");
    Serial.println(dice[3]);
  } else {
    if (strcmp(string2, "NONE") == 0)
      string2[0] = '\0';
    if (strcmp(string3, "NONE") == 0)
      string3[0] = '\0';
    
    strncpy(text, string2, sizeof(text));
    strncpy(text2, string3, sizeof(text2));
    if (num1 == 0 && string2[0] != '\0')
      textX = 32 - (strlen(string2) * 6) / 2;
    else    
      textX = num1;
    
    if (num2 == 0 && string3[0] != '\0')
    {
      if (strlen(string3) > 13)
      {
        text2X = 50;
      }
      else
      {
        text2X = 32 - (strlen(string3) * 6) / 2;
      }
    }
    else    
      text2X = num2;
    
    dice[0] = num3;
    dice[1] = num4;
  }
  int free_mem = freeMemory();
  if (free_mem < 100)
  {
    char buffer[20]; // Assuming the maximum size needed for the integer to string conversion
    itoa(free_mem, buffer, 10); // Convert integer to string

    Serial.print("Low Memory!!! ");
    Serial.print(buffer);
  }
}

void JustText()
{
  matrix.fillScreen(0);
  AddText();
  matrix.swapBuffers(false);
}


const int NUM_STARS = 30;
struct Star {
    uint8_t x;
    uint8_t y;
    uint8_t red;
    uint8_t green;
    uint8_t blue;
};
Star stars[NUM_STARS];

void updateStars() {
    for (uint8_t i = 0; i < NUM_STARS; ++i) {
        // Randomly change the color of each star
        if (random(10) == 0) { // Adjust this probability to control the frequency of twinkling
            // Randomly adjust the RGB components by a small amount
            stars[i].x = random(64);
            stars[i].y = random(32);            
            stars[i].red = random(256);
            stars[i].green = random(256);
            stars[i].blue = random(256);
        }
    }
}

void displayRandomDots() {
    matrix.fillScreen(0);

    // Draw 50 random dots
    for (uint8_t i = 0; i < 100; i++) 
    {
        // Generate random coordinates within the LED matrix boundaries
        int x = random(matrix.width());
        int y = random(matrix.height());

        // Generate random color values
        uint8_t red = random(8);    // 0 to 7
        uint8_t green = random(8);  // 0 to 7
        uint8_t blue = random(8);   // 0 to 7

        // Draw a dot at the generated coordinates with the random color
        matrix.drawPixel(x, y, matrix.Color333(red, green, blue));
    }
    AddText();
    // Swap buffers to display the drawing
    matrix.swapBuffers(false);
}

const uint8_t SNAKE_SIZE = 6;
struct Snake {
    int x[SNAKE_SIZE];
    int y[SNAKE_SIZE];
    uint8_t length;
    int dx;
    int dy;
};

const uint8_t NUM_SNAKES = 7;
// Global variables
Snake snakes[NUM_SNAKES];

// Initialize the snake
void initSnake() {
  for (int j = 0 ; j < NUM_SNAKES ; j++)
  {
    snakes[j].length = SNAKE_SIZE;
    snakes[j].dx = -1 + ((j%2)*2) ;
    //Serial.println(String (j%2) + " " + String(snakes[j].dx));

    snakes[j].dy = 0;
    // Initialize snake's initial position
    for (int i = 0; i < SNAKE_SIZE; ++i) 
    {
        snakes[j].x[i] = 32 - SNAKE_SIZE / 2 + i;
        snakes[j].y[i] = 16;
    }
  }
}

void moveSnake() {
  static uint8_t steps = 0; // Counter to keep track of steps taken
  const uint8_t changeDirectionInterval = 5; // Change direction every 5 steps

  for (uint8_t i = 0 ; i < NUM_SNAKES ; i++)
  {
    // Move the body of the snake
    for (uint8_t j = snakes[i].length - 1; j > 0; --j) {
        snakes[i].x[j] = snakes[i].x[j - 1];
        snakes[i].y[j] = snakes[i].y[j - 1];
    }

    // Move the head of the snake
    snakes[i].x[0] += snakes[i].dx;
    snakes[i].y[0] += snakes[i].dy;

    // Check if the snake's head has reached the boundary of the matrix
    if (snakes[i].x[0] < 0) {
        snakes[i].x[0] = MATRIX_WIDTH - 1; // Wrap around to the right edge
    } else if (snakes[i].x[0] >= MATRIX_WIDTH) {
        snakes[i].x[0] = 0; // Wrap around to the left edge
    }
    if (snakes[i].y[0] < 0) {
        snakes[i].y[0] = MATRIX_HEIGHT - 1; // Wrap around to the bottom edge
    } else if (snakes[i].y[0] >= MATRIX_HEIGHT) {
        snakes[i].y[0] = 0; // Wrap around to the top edge
    }

    // Increment the steps counter
    steps++;

    // Check if it's time to change direction
    if (steps >= changeDirectionInterval) {
        // Change direction randomly
        int direction;
        if (snakes[i].dx == 0) {
            // If the snake is moving vertically (up or down), change to horizontal (left or right)
            direction = random(2)  + 2; // Randomly select 2 (left) or 3 (right)
        } else {
            // If the snake is moving horizontally (left or right), change to vertical (up or down)
            direction = random(2); // Randomly select 0 (up) or 1 (down)
        }
        switch (direction) {
            case 0: // Up
                snakes[i].dx = 0;
                snakes[i].dy = -1;
                break;
            case 1: // Down
                snakes[i].dx = 0;
                snakes[i].dy = 1;
                break;
            case 2: // Left
                snakes[i].dx = -1;
                snakes[i].dy = 0;
                break;
            case 3: // Right
                snakes[i].dx = 1;
                snakes[i].dy = 0;
                break;
        }
        // Reset the steps counter
        steps = 0;
    }
  }
}


// Draw the snake on the LED matrix
void drawSnake() {
    // Clear the matrix
    matrix.fillScreen(0);
    // Draw snake's body
    uint8_t red = random(8);    // 0 to 7
    uint8_t green = random(8);  // 0 to 7
    uint8_t blue = random(8);   // 0 to 7
    for (int j = 0 ; j < NUM_SNAKES ; j++)
    {
      for (uint8_t i = 0; i < snakes[j].length; ++i) {
          matrix.drawPixel(snakes[j].x[i], snakes[j].y[i], matrix.Color333(red, green, blue)); // Red snake
      }
    }
    // Swap buffers to display the drawing
    AddText();
    Add2Dice();
    matrix.swapBuffers(false);
}

// Main function for the snake game
void snakeGame() {
    static unsigned long lastUpdateTime = 0; // Variable to track the last update time

    if (millis() - lastUpdateTime >= 100) { // Update every 100 milliseconds
        lastUpdateTime = millis();
        // Move the snake
        moveSnake();
        // Draw the snake
        drawSnake();
    }
}

void displayLostScreen() {
  //matrix.fillScreen(0); // Black screen
  matrix.fillScreen(matrix.Color333(0,255, 0)); 
  matrix.setTextSize(1);

  // Set white color for text and smiley
  matrix.setTextColor(matrix.Color333(255, 255, 255));
  
  // Display "I Lost" text
  matrix.setCursor(5, 12); // Center the text
  matrix.print("I Lost :(");



  matrix.swapBuffers(false);
}

void displayBouncingBall() {
    matrix.fillScreen(0);

    // Define ball properties
    const uint8_t radius = 4; // Radius of the ball
    static uint8_t xPos = 32; // Initial x position of the ball
    static uint8_t yPos = 16; // Initial y position of the ball
    static uint8_t xVel = 2;  // Initial velocity of the ball in the x-direction
    static uint8_t yVel = 2;  // Initial velocity of the ball in the y-direction

    // Update ball position
    xPos += xVel;
    yPos += yVel;

    // Check for collision with walls
    if (xPos - radius < 0 || xPos + radius >= matrix.width()) {
        xVel = -xVel; // Reverse x velocity on collision with left or right wall
    }
    if (yPos - radius < 0 || yPos + radius >= matrix.height()) {
        yVel = -yVel; // Reverse y velocity on collision with top or bottom wall
    }

    // Calculate color based on a sine wave that varies over time
    float colorFactor = 0.5 * (1.0 + sin(0.01 * millis())); // Adjust frequency as needed
    uint8_t red = 7 * colorFactor;
    uint8_t green = 0;
    uint8_t blue = 7 * (1 - colorFactor);

    // Draw the ball with the calculated color
    matrix.fillCircle(xPos, yPos, radius, matrix.Color333(red, green, blue));
    AddText();
    // Swap buffers to display the drawing
    matrix.swapBuffers(false);

    // Add optional delay to control the animation speed
    //delay(50);
}



void UpdateDiceBMP()
{
  for (uint8_t i = 0 ; i<4 ; i++)
  {
    if (dice[i] != 0)
    {
      switch (dice[i])
      {
        case 0:
          dice_bmp[i] = NULL;
          break;
        case 1:
          dice_bmp[i] = (const uint16_t *)DICE_1;
          break;
        case 2:
          dice_bmp[i] = (const uint16_t *)DICE_2;
          break;
        case 3:
          dice_bmp[i] = (const uint16_t *)DICE_3;
          break;
        case 4:
          dice_bmp[i] = (const uint16_t *)DICE_4;
          break;
        case 5:
          dice_bmp[i] = (const uint16_t *)DICE_5;
          break;
        case 6:
          dice_bmp[i] = (const uint16_t *)DICE_6;
          break;
        case 7:
          dice_bmp[i] = (const uint16_t *)QM;
          break;
      }
    }
  }
}

void StartGameDice()
{
  matrix.fillScreen(0);
  matrix.setTextColor(matrix.Color333(255, 255, 255));
  matrix.setCursor(11,6);
  matrix.setTextSize(1);
  matrix.print("You   Me");

  // Corrected array initialization syntax
  int dice_pos[8] = { 10, 16, 
                      20, 16, 
                      45, 16, 
                      55, 16 };

  for (int i = 0; i < 4; i++)
  {
    int y_size = 7;
    if (dice[i] == 7)
      y_size = 9;

    if (dice[i] != 0)
      // Corrected index usage in drawRGBBitmap
      matrix.drawRGBBitmap(dice_pos[i*2], dice_pos[i*2+1], dice_bmp[i], 7, y_size);
  }
  matrix.swapBuffers(false);
}

/*
void StartGameDice()
{
  matrix.fillScreen(0);
  matrix.setTextColor(matrix.Color333(255, 255, 255));
  matrix.setCursor(11,6);
  matrix.setTextSize(1);
  matrix.print("You   Me");



  if (dice[0] != 0)
  {
    
    matrix.drawRGBBitmap(10,16, dice_bmp[0], 7,7);
  }
  if (dice[1] != 0)
  {
    matrix.drawRGBBitmap(20,16, dice_bmp[1], 7,7);
  }
  if (dice[2] != 0)
  {
    matrix.drawRGBBitmap(45,16, dice_bmp[2], 7,7);
  }
  if (dice[3] != 0)
  {
    matrix.drawRGBBitmap(55,16, dice_bmp[3], 7,7);
  }
  
  matrix.swapBuffers(false);
}*/

void ScrollText() {
  byte i;
  // Clear background
  matrix.fillScreen(0);

  // Bounce three balls around
  for(i=0; i<num_balls; i++) {
    // Draw 'ball'
    matrix.fillCircle(ball[i][0], ball[i][1], 5, pgm_read_word(&ballcolor[i]));
    // Update X, Y position
    ball[i][0] += ball[i][2];
    ball[i][1] += ball[i][3];
    // Bounce off edges
    if((ball[i][0] == 0) || (ball[i][0] == (matrix.width() - 1)))
      ball[i][2] *= -1;
    if((ball[i][1] == 0) || (ball[i][1] == (matrix.height() - 1)))
      ball[i][3] *= -1;
  }

  // Draw big scrolly text on top
  matrix.setTextColor(matrix.ColorHSV(hue, 255, 255, true));
  matrix.setCursor(textX, 10);
  matrix.print(text);
  textMin = -(6*strlen(text));
  // Move text left (w/wrap), increase hue
  if((--textX) < textMin) 
  {
    textX = matrix.width();
  }
  hue += 7;
  if(hue >= 1536) hue -= 1536;
  Add2Dice();
  // Update display
  matrix.swapBuffers(false);
}

void drawStars() {
    matrix.fillScreen(0); // Clear the screen
    for (int i = 0; i < NUM_STARS; ++i) {
        // Draw a pixel for each star with its respective color
        matrix.drawPixel(stars[i].x, stars[i].y, matrix.Color888(stars[i].red, stars[i].green, stars[i].blue));
    }
    AddText();
    matrix.swapBuffers(false); // Display the drawing
}

void ProcessLoop()
{
  if (current_state == STATE_STARS)
  {
    updateStars();
    drawStars();
  }
  if (current_state == STATE_JUST_TEXT)
  {
    JustText();
  }
  if (current_state ==  STATE_VICTORY)
  {
    displayVictoryScreen();
  }
  if (current_state == STATE_SCROLL_TEXT)
  {
    ScrollText();
  }
  if (current_state == STATE_CHECKERS)
  {
    updateCheckers();
    drawCheckers();
  }
  
  if (current_state == STATE_SNAKE)
  {
    snakeGame();
  }
  if (current_state == STATE_RECT)
  {
    //MovingRect(); 
  }
  if (current_state == STATE_JUST_TEXT)
  {
    JustText();
  }
  if (current_state == STATE_BOUNCING_BALL)
  {
    displayBouncingBall();
  }

  if (current_state == STATE_LOST)
  {
    displayLostScreen();
  }
  if (current_state == STATE_RANDOM_DOTS)
  {
    displayRandomDots();
  }
  if (current_state == STATE_START_GAME_DICE)
  {
    UpdateDiceBMP();
    StartGameDice();
  }
  if (current_state == STATE_START)
  {
    //ShowBMP();
  }
}


char message[MAX_STRING_LENGTH] = "Ready";

extern unsigned int __heap_start;
extern void *__brkval;

int freeMemory() {
  int free_memory;
  if((int)__brkval == 0)
    free_memory = ((int)&free_memory) - ((int)&__heap_start);
  else
    free_memory = ((int)&free_memory) - ((int)__brkval);
  return free_memory;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial1.begin(9600);  //pins 18 and 19 
  Serial.println ("starting RGB Led Matrix...");
  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setTextSize(1);
  //ParseLine("STARS:Are You Ready?:0:Ready:0:0:0");
  ParseLine("SCROLL_TEXT:Are You Ready?!?:0:NONE:0:0:0");
}
/*
void setup() {
  Serial.begin(9600); // Initialize serial communication

  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setTextSize(1);


  //Wire.begin(SLAVE_ADDRESS);
  //Wire.setClock(1000);
  //Wire.onReceive(receiveEvent);
  //Wire.onRequest(requestEvent);


  Serial.println("Slave initialized.");
  current_state = STATE_STARS;
  //ParseLine("STARS:Your Turn:0:Go G Them:0:3:1");

  //String ee = "SCROLL_TEXT:abcdfefghijklmno";
  //strcat(ee,"qrstuvwxyz:0:abcdfefghijklm");
  //strcat(ee,"nopqrstuvwxyz:0:4:3");
  //String fg= ee;
  ///Serial.println(fg);
  //ParseLine(ee);
}
*/

void loop() {
  //Serial.println("checking serial1");
  if (Serial1.available())
  {

    Serial.println("serial1 is available!!");
    //int msg = Serial1.read();
    String msg = Serial1.readStringUntil('\n');
    Serial.println(msg);
    ParseLine(msg.c_str());
  }
  ProcessLoop();
  // put your main code here, to run repeatedly:

}
/*
void loop() {
  ReadStringFromSerial();
  return;

  int free_mem = freeMemory();
  if (free_mem < 100)
  {
    Serial.print("Low Memory!!!");
  }
  ReadStringFromSerial();
  ProcessLoop();
  // Additional operations can be added here if needed
  delay(100);
}
*/

void requestEvent() {
  char message[] = "OK";
  Serial.print("Request received from master. Sending message: ");
  Serial.println(message);
  Wire.write((uint8_t*)message, strlen(message)); // Send the string back to the master
}
