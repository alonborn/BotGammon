#include <Servo.h>

#include <WiFiS3.h>

//#include <ArduinoOTA.h>
#include "Arduino_LED_Matrix.h"
#include "Matrix.h"
#include <SoftwareSerial.h>
#include <Wire.h>

#define rstPin 4

struct Coordinates {
  float xValue;
  float yValue;
};

Servo dice_servo;  // create servo object to control a servo
Servo magnet_servo;
int magnet_servo_last_angle = 0;

int PIN_MAGNET_SERVO = 11;
int PIN_MAGNET_SIGNAL = 9;
int PIN_DICE = 12;
int PIN_RELAY_LIMITS = 4;

int PIN_BUTTON = 2;

int PIN_COLOR_RED = 3;
int PIN_COLOR_GREEN = 5;
int PIN_COLOR_BLUE = 6;


int magnet_servo_target_angle = 0;   //to which angle the servo needs to rotate to
int magnet_speed = 0; //1 --> slowly 2 --> rapidly
float magnet_servo_start_rotation = 0;  //from which x or y to start rotate the magnet servo
int start_rotate_X_or_Y = 0; //whether to start rotate the servo when X is higher/lower than magnet_servo_start_rotation or Y 0-->X, 1-->Y
int start_rotate_lower_or_higher= 0; //whether to start rotate when X/Y is lower or higher than magnet_servo_start_rotation 0-->lower, y-->higher
bool movement_started = false;


String current_command;
int num_of_sub_commands = 0;
int current_command_line = 0; //one based!!!!

enum CurrentStateEnum   { IDLE = 0,
                          MOVE = 1,
                          ROTATE = 2,
                          HOME = 4,
                          WAIT_FOR_PLAYER = 8
                         };

int current_state = IDLE;


String GetSectionByIndex(String inputString, int index, char delimiter);
void SplitString(String inputString, char delimiter, String outputArray[], int outputSize);
void EstablishWiFiConnection();
void CloseWiFiConnection();
void SendStringToTCPClient(String str);
bool ReceiveCommandFromTCPClient();
int ExtractNumber(String input);
void CheckIfClientConnected();
int CountCharacterOccurrences(String inputString, char targetChar);
String GetSectionBySubstring(String inputString, String subs, char delimiter = '^');
Coordinates ParseMPosString(const char* inputString);
String RemovePercent(const String &original);


int matrix_last_change = 0; //when was the last change
int matrix_icon_num = 0;
int matrix_index = 0;

void SetGreenColor()
{
  SetLedColor(0,50,0);
}

void SetBlueColor()
{
  SetLedColor(0,0,50);
}

void SetNoColor()
{
  SetLedColor(0,0,0);
}


void SetOrangeColor()
{
  SetLedColor(255,128,0);
}

void SetLedColor(int red,int green, int blue)
{
  analogWrite(PIN_COLOR_RED,red);
  analogWrite(PIN_COLOR_GREEN,green);
  analogWrite(PIN_COLOR_BLUE,blue);
}


//checks if it's a good time to start the rotation, during movement
bool ShouldPerformRotate()
{
  
  if (!(current_state & MOVE))
  {
    return true;
  }

  if (movement_started)
  {
    return true;
  }

  Coordinates coords = GetGRBLPosition();
  //SerialPrintln("X:"+String(coords.xValue)+"Y:"+String(coords.yValue));
  if (coords.xValue < 0)
    return false;
  //SerialPrintln("start_rotate_X_or_Y" + String(start_rotate_X_or_Y));
  if (start_rotate_X_or_Y==0) //X
  {
    if (start_rotate_lower_or_higher==0) //lower than
    {
        if (coords.xValue < magnet_servo_start_rotation)
        {
          movement_started = true;
          SerialPrintln("start!1");
          return true;
        }
    }
    else //higher
    {
        if (coords.xValue > magnet_servo_start_rotation)
        {
          movement_started = true;
          SerialPrintln("start!2");
          return true;
        }
    }
  }
  else
  { //Y
    if (start_rotate_lower_or_higher==0) //lower than
    {
        if (coords.yValue < magnet_servo_start_rotation)
        {
          movement_started = true;
          SerialPrintln("start!3");
          return true;
        }

    }
    else //higher
    {
        if (coords.yValue > magnet_servo_start_rotation)
        {
          movement_started = true;
          SerialPrintln("start!4");
          return true;
        }
    }
  }
  //SerialPrintln("not yet...");
  return false;
}

long last_rotated_time = 0;
void RotateMagnetServo()
{
  int magnet_servo_delay = 5;

  if (millis() < last_rotated_time + magnet_servo_delay)
    return; //not enough time has passed, nothing to do
  else
  { //do one small servo step 

    //Have we reached the target angle?
    if (magnet_servo_target_angle == magnet_servo_last_angle)
    {
      current_state &= ~ROTATE;
      SerialPrintln("rotate completed");
      SerialPrintln(String(magnet_servo_target_angle));
    }
    else
    {

      if (ShouldPerformRotate())
      {
        magnet_servo.write(magnet_servo_target_angle);
        SerialPrintln("rotated   "+String(magnet_servo_last_angle));
        magnet_servo_last_angle = magnet_servo_target_angle;
        last_rotated_time = millis();
        delay(1000);
      }
    }
  }
   
}

/*
  supported commands:

  Roll - roll the dices
  MagnetOff - turn off the magnet
  MagnetOn - turn on the magnet

*/

void SerialPrintln(String line)
{
  Serial.println(line);
}

void SerialPrint(String line)
{
  Serial.print(line);
}

#define CHUNK_SIZE 10      // Define the chunk size
#define SLAVE_ADDRESS 0x10 // Change this to your slave address
#define MAX_STRING_LENGTH 50
char receivedMessage[MAX_STRING_LENGTH] = "";

void SendLineToRGB(String message) 
{
  // Calculate the number of chunks
  SerialPrintln("Sending:" + message);
  int numChunks = message.length() / CHUNK_SIZE + (message.length() % CHUNK_SIZE != 0);
  for (int i = 0; i < numChunks; i++) 
  {
    int startIdx = i * CHUNK_SIZE;
    int endIdx = min((i + 1) * CHUNK_SIZE, message.length());
    String chunk = message.substring(startIdx, endIdx);
    
    // Determine if this is the last chunk
    char isLastChunk = (i == numChunks - 1) ? '1' : '0';

    Wire.beginTransmission(SLAVE_ADDRESS);
    Wire.write(isLastChunk); // Write a flag indicating if this is the last chunk
    Wire.write(chunk.c_str());
    Wire.endTransmission();

    // Request string from slave
    Wire.requestFrom(SLAVE_ADDRESS, MAX_STRING_LENGTH);
    delay(100);
    

    // Read response
    int j = 0;
    while (Wire.available() && j < MAX_STRING_LENGTH - 1) {
      receivedMessage[j++] = Wire.read(); // Read characters into receivedMessage
    }
    receivedMessage[j] = '\0'; // Null-terminate the string

    //Serial.println("Received from slave: " + String(receivedMessage));
  }
}

void setup() 
{
    Serial.begin(9600);
  Serial1.begin(115200);
  digitalWrite(rstPin, HIGH);
    

  //Wire.setClock(1000);
  Wire.begin();                // join i2c bus with address #8
  
  SendLineToRGB("JUST_TEXT:HELLO!:0:NONE:0:0:0");

  
  magnet_servo.attach(PIN_MAGNET_SERVO);
  pinMode(PIN_MAGNET_SIGNAL, OUTPUT);
  
  pinMode(PIN_BUTTON,INPUT);
  pinMode(PIN_DICE, OUTPUT);
  pinMode(PIN_RELAY_LIMITS,OUTPUT);
  SetOrangeColor();
  dice_servo.write(90);                  // sets the servo position according to the scaled value
  magnet_servo.write(10);                  // sets the servo position according to the scaled value
  magnet_servo_last_angle = 10;

  digitalWrite(PIN_MAGNET_SIGNAL,LOW);
  SerialPrintln("Setup ended");
  SetNoColor();
  
  SendLineToRGB("JUST_TEXT:CONNECTING:0:NONE:0:0:0");
  
  EstablishWiFiConnection();

  SendLineToRGB("STARS:CONNECTED!:0:NONE:0:0:0");
}

void WaitForPlayer()
{
  current_state = WAIT_FOR_PLAYER;
  matrix_index = PLAYER_TURN;
  SetGreenColor();
}

void RollDice()
{
  SerialPrintln("start roll dice");
  digitalWrite(PIN_DICE,HIGH);
  delay(1100);
  digitalWrite(PIN_DICE,LOW);
  delay(500);
  SerialPrintln("end roll dice");
}


String ReadLineFromGRBL(bool handle_alarm = true)
{
  String received_data;
  if (Serial1.available()) 
  {
    received_data = Serial1.readStringUntil('\n'); // Read a line of text until a newline character
    // Check if any data was received
    if (received_data.length() > 0) 
    {
      SerialPrintln(received_data);
      if (handle_alarm && (received_data.indexOf("Alarm") >=0) || (received_data.indexOf("ALARM") >=0))
      {
        
        HandleAlarm(received_data);
        return "ALARM";
      }
      return received_data;
    }
  }
  return String();
}

long last_pos_check = 0;
// ?<Alarm|MPos:0.000,0.000,0.000|FS:0,0|Pn:P>
Coordinates GetGRBLPosition()
{
  //SerialPrintln("Checking GRBL Position");
  int interval = 200;  //check every 200ms
  Coordinates coords;
  coords.xValue = -1;
  coords.yValue = -1;
  
  if (millis() < last_pos_check + interval)
    return coords;

  Serial1.write("?\n");
  if (Serial1.available())
  {
    String pos_str = ReadLineFromGRBL(false);
    //SerialPrintln(pos_str);
    String pos_section = GetSectionBySubstring(pos_str,"MPos:",'|');
    if (CountCharacterOccurrences(pos_section,',') == 2) //if it seems the line is complete
    {
      float x,y;
      if(ParseMPosString(pos_section.c_str(),x,y))
      {
        coords.xValue = x;
        coords.yValue = y;
      }
      return coords;
    }
  }
  

  return coords;
}

/*
void RotateMagnetServoTo(int new_angle)
{
  int delta = 1;
  int delay_ms = 4;
  if (new_angle < magnet_servo_last_angle)
  {
   for (int cur_angle = magnet_servo_last_angle ;  cur_angle >= new_angle;cur_angle -=delta)
    {
      magnet_servo.write(cur_angle);
      delay (delay_ms);
    }   
  }
  else
  {
   for (int cur_angle = magnet_servo_last_angle ; cur_angle <= new_angle;cur_angle +=delta)
    {
      magnet_servo.write(cur_angle);
      delay (delay_ms);
    }  
  }
  magnet_servo_last_angle = new_angle;
}*/

/*
void RotateMagnetServo(String str)
{
  SerialPrintln("about to rotate the magnet servo");
  int pos = ExtractNumber(str);
  SerialPrintln("about to rotate the magnet servo to: " + String(pos));
  SerialPrintln("Magnet rotate to:" + String(pos));
  RotateMagnetServoTo(pos);  
  SerialPrintln("Magnet rotated");
}*/

void WaitForOKFromGRBL()
{
    bool keep_checking = true;
    while (keep_checking)
    {
      String ret_val = ReadLineFromGRBL(false);
      if (ret_val != "")
        SerialPrintln(ret_val);
      if (ret_val.startsWith("ok"))
        return;
    }
}

int UpdateGRBLState(bool handle_alarm = true)
{
  bool completed = false;

  //while (!completed)
  if (current_state & (MOVE|HOME) )
  {
    Serial1.write("?\n");

    /*while (Serial1.available() == 0) 
    {
      UpdateGRBLWaitingSign();
      delay (100);
      // Do nothing until data is available
    }*/
    if (Serial1.available())
    {
      String ret_val = ReadLineFromGRBL(handle_alarm);
      if (ret_val.startsWith("<Idle"))
      {        
        SerialPrintln ("got idle from GRBL");
        completed = true;
        CleanupGRBLBuffer();

        if (current_state &= HOME)
        {
         SerialPrintln("Turning off homing");
         Serial1.println("$22=0");
         delay(100);
         Serial1.println("$21=0");         
         delay(100);
         /*Serial1.println ("$$22");
         for (int i = 0 ; i <10 ; i++)
         {
            String ret_val2 = ReadLineFromGRBL(handle_alarm);
            SerialPrintln(ret_val2);
         }*/
         

        }

        if (current_state & ~ROTATE)  //dont turn off move until rotate is done, to make sure rotate is fully done
        {
          SerialPrintln("clearing current state");
          current_state &= ~(MOVE|HOME);
          SerialPrintln("Current state = " + String(current_state));
        }

      }
      if (ret_val == "ALARM")
      {
        SerialPrint ("Encountered Alarm while waiting for GRBL");
        return -1;
      }
      //SerialPrintln("while waiting for Idle:" + ret_val);
      //UpdateGRBLWaitingSign();
    }
  }
 
  //need to cleanup the rest of the messages, before the next call:
  
  //CleanupGRBLBuffer();
  //SerialPrintln("GRBL is Idle");
  return 0;
}

void Home()
{
  SerialPrintln("Home is starting!!!!");
  digitalWrite(PIN_RELAY_LIMITS,HIGH);
  delay (100);
  char myChar = 24; // ASCII value of 24

  SerialPrintln("Turnning on Homing");
  Serial1.println ("$21=1");
  delay(100);
  Serial1.println ("$22=1");
  delay(100);
  /*for (int i = 0 ; i <10 ; i++)
  {
    String ret_val2 = ReadLineFromGRBL(false);
    SerialPrintln(ret_val2);
  }*/
  
  //WaitForOKFromGRBL();

  SerialPrintln("Sending Soft Reset");
  Serial1.write(myChar);
  delay(100);
  SerialPrintln("Sending $X");
  Serial1.println ("$X");
  delay(100);
  SerialPrintln("Sending $H");
  Serial1.println ("$H");
  //WaitUntilGRBLIdle(false);
  delay(10);
  current_state = HOME;
  matrix_index = ICON_HOME;  //show home icon
}

void MagnetOff()
{
  SerialPrintln("turning magnet off");
  digitalWrite(PIN_MAGNET_SIGNAL,LOW);
  delay(100);
}

void MagnetOn()
{
  SerialPrintln("turning magnet on");
  digitalWrite(PIN_MAGNET_SIGNAL,HIGH);
  delay(300);
}

/*
String GetGRBLCommand(String str)
{
  int colonPosition = str.indexOf(':');

  // Check if "GRBL" is found at the beginning of the string
  if (colonPosition != -1 && str.startsWith("GRBL")) 
  {
    // Use substring to get the part of the original string after ":"
    String substring = str.substring(colonPosition + 1);
    SerialPrintln("extracted: " + substring);
    return substring;
  }
  else
    return String();
}*/

bool CleanupGRBLBuffer()
{
  bool ret_val = true;
  while (Serial1.available()) 
  {
    String received_data = Serial1.readStringUntil('\n');
    //SerialPrintln(received_data);
    if (ret_val && (received_data.indexOf("Alarm") >=0) || (received_data.indexOf("ALARM") >=0))
    {
      SerialPrintln("Encountered alarm during buffer cleanup");
      HandleAlarm(received_data);
      ret_val = false;
    }
    //SerialPrintln("in loop, from GRBL" + received_data);
  }
  return ret_val;
}

void HandleAlarm(String received_data)
{
  //matrix.loadFrame(alarm[0]);
  SerialPrintln("ALARM: " + received_data);
  delay (100);
  //digitalWrite(rstPin, LOW);  //if a reset is required - use this one:
  //Home();
}


int ExecuteGRBLCommand(String GRBLCommand)
{
  int ret_val;

  Serial1.println(GRBLCommand);
  SerialPrintln("Sent command to GRBL:" + GRBLCommand);
  matrix_index = ICON_WIFI;
  //ret_val = WaitUntilGRBLIdle();
  return ret_val;
}


bool CheckAlarm()
{
  Serial1.write("?\n");
  delay(40);
  return CleanupGRBLBuffer();
}



bool in_alarm = false;

void CheckAlarmRequest()
{
  if (in_alarm)
  {
      SendStringToTCPClient("ALARM");
  }
  else
  {
    SendStringToTCPClient("OK");
  }
}



//%Magnet:30:X:150%
void GetMoveAndRotateParams(String move_command, String magnet_line)
{
  Coordinates coords = ExtractXYValues(move_command);
  String section_5 = GetSectionByIndex(magnet_line,5,':');

  SerialPrint("section_5 = ");
  Serial.println(section_5);

  magnet_servo_start_rotation = section_5.toFloat();  
  start_rotate_X_or_Y = GetSectionByIndex(magnet_line,4,':') == "X" ? 0:1;

  if (start_rotate_X_or_Y == 0)
  {
    start_rotate_lower_or_higher = coords.xValue > magnet_servo_start_rotation ? 1:0;
  }
  else
  {
    start_rotate_lower_or_higher = coords.yValue > magnet_servo_start_rotation ? 1:0;
  }
  
  SerialPrint("coords.xValue = ");
  Serial.println(coords.xValue);

  SerialPrint("magnet_servo_start_rotation2 = ");
  Serial.println(magnet_servo_start_rotation);

  SerialPrint("start_rotate_X_or_Y = ");
  Serial.println(start_rotate_X_or_Y);

  SerialPrint("start_rotate_lower_or_higher = ");
  Serial.println(start_rotate_lower_or_higher);
}

void ReadCommandLine(int command_line)
{
  String sub_command = GetSectionByIndex(current_command,command_line,'^');
  sub_command = RemovePercent (sub_command);

  String move_command;
  SerialPrintln ("subcommand("+String(command_line)+"):" + sub_command);

  String move_line = GetSectionBySubstring(sub_command, "Move:",'%');
  if (move_line != "")
  {
    current_state = MOVE;
    matrix_index = ICON_MOVE;
    move_command = GetSectionByIndex(move_line,2,':');
    ExecuteGRBLCommand(move_command);
  }

  String magnet_line = GetSectionBySubstring(sub_command, "Magnet:",'%');
  
  if (magnet_line != "")
  {
    String magnet_speed_str = GetSectionByIndex(magnet_line,2,':');
    String target_angle_str = GetSectionByIndex(magnet_line,3,':');
    
    magnet_speed = magnet_speed_str.toInt();
    SerialPrintln("magnet speed!!!!!!!!!!!!!!!!!!!!!!" + String (magnet_speed));

    magnet_servo_target_angle = target_angle_str.toInt();
  
    current_state |= ROTATE;
    
    movement_started = false;

    if (CountCharacterOccurrences(magnet_line,':') > 1)
    {
        GetMoveAndRotateParams(move_command, magnet_line);
    }
  }
  if (sub_command.indexOf("MagnetOn") >= 0)
    MagnetOn();
  if (sub_command.indexOf("MagnetOff") >= 0)
    MagnetOff();
  if (sub_command.indexOf("Home") == 0)
    Home();
  if (sub_command.indexOf("Roll") == 0)
    RollDice();
  if (sub_command.indexOf("RGB") >= 0)
  {
    int colonIndex = sub_command.indexOf(':');
    String rgb_command = sub_command.substring(colonIndex + 1);
    SendLineToRGB(rgb_command);
  }
  if (sub_command.indexOf("WaitForPlayer") >= 0)
    WaitForPlayer();
}

void HandleWaitForPlayer()
{
  //SerialPrintln("Handle wait for player");
  int buttonState = digitalRead(PIN_BUTTON);
  if (buttonState == HIGH) 
  {
    SerialPrintln("Button Pressed");
    current_state = IDLE;
    current_command = "";
    current_command_line = 0;
    SetNoColor();
    SendStringToTCPClient("OK");
    SerialPrintln("sent OK");
    matrix_index = ICON_IDLE;  //show home icon
  }
  else
  {
    //SerialPrintln("button is low");
  }
}


void loop() 
{
  CheckIfClientConnected();

  if (current_state == WAIT_FOR_PLAYER)
  {
    HandleWaitForPlayer();
  }

  if (current_command == "" && current_state == IDLE)   //in idle, check if new command arrived 
  {   
    if (ReceiveCommandFromTCPClient())
    { //if a new line received
        current_command_line =0;
        magnet_servo_start_rotation = 0;
    }
  }

  if (current_command != "" && current_state == IDLE && current_command_line == num_of_sub_commands)  //reached the end of the command
  { //once the command is done - send that everything is ok, ready for next command
    SendStringToTCPClient("OK");
    digitalWrite(PIN_RELAY_LIMITS,LOW); //in any case - disconnect limits
    current_command = "";
    current_command_line = 0;
    SerialPrintln("sent OK");
    matrix_index = ICON_IDLE;  //show home icon

  }

  if (current_command != "" && (current_state == IDLE) && current_command_line < num_of_sub_commands)  //if there are still lines to execute
  {
      SerialPrintln("read next line");
      current_command_line +=1;
      ReadCommandLine(current_command_line);
      delay(7);
      return;
  }
  
  //continue to handle current line
  if (current_state & ROTATE)
  {
    RotateMagnetServo();
  }
  if (current_state & (MOVE|HOME))
  {
    //SerialPrintln("Current State = " + String (current_state));
    UpdateGRBLState();
  }
  delay(7);
}


