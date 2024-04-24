#include <Wire.h>

#define MAX_MESSAGE_LENGTH 80
#define CHUNK_SIZE 30
#define SLAVE_ADDRESS 0x10 // Change this to your slave address
//#define Serial1 Serial

char tmp_message[MAX_MESSAGE_LENGTH + 1]; // +1 for the null terminator

void receiveEvent(int numBytes) {
  Serial.println("Received event");
  /*String msg;
  while (Wire.available()) {
    msg+= (char)Wire.read(); // Receive a byte as character
  }
  Serial.println (String("Found:") + msg);
  Serial1.println(msg);
  return;*/

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
    //Serial.print("Received *COMPLETE* message: ");
    Serial.println (String("Found:") + tmp_message);
    Serial1.println(tmp_message);
    tmp_message[0] = '\0'; // Reset the receivedMessage for the next message
  } else {
    Serial.print("Received PARTIAL message: ");
    Serial.println(tmp_message);
  }
}

void setup()
{
  Serial.begin(9600);
  Serial1.begin(9600);
  Wire.begin(SLAVE_ADDRESS);
  //Wire.setClock(1000);
  Wire.onReceive(receiveEvent);
  Serial.println("Converter Initialized");
  //Wire.onRequest(requestEvent);
}

void loop()
{
  //Serial.println("check msg!");  //pins 0 and 1 on Micro
  while (Wire.available())
  {
    Serial.println("wire is available");
  }
  delay(100);
}