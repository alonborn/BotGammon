char ssid[] = "borenshtein";        // your network SSID (name)
char pass[] = "p428003a";    // your network password (use for WPA, or use as key for WEP)
const int serverPort = 2390;  // Choose a port for your server

WiFiServer server(serverPort);
WiFiClient client;

void EstablishWiFiConnection()
{
  SerialPrintln("StartEstablishconnection");
  matrix_index = 12;
  // Connect to Wi-Fi
  //loadNumToMatrix(1);
  SerialPrint("\nConnecting to ");
  SerialPrintln(ssid);

  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    SerialPrint(".");
  }
  SerialPrintln("\nWiFi connected");

  IPAddress ip = WiFi.localIP();
  Serial.print("Local IP:");
  Serial.println(ip);

  // Start the server
  server.begin();
  SerialPrintln("Server started");

  // Check if a client has connected
  client = server.available();
  int count = 0;
  while (!client) 
  {
    client = server.available();
    //SerialPrint("?");
    //UpdateWIFIWaiting();
    delay(100);
    count+=1;
    if (count== 100)
    {
      SerialPrintln("");
      count = 0;
    }
  }
  // Wait until the client sends some data
  SerialPrintln("New client connected");
  //loadNumToMatrix(2);
}

void CloseWiFiConnection()
{
  // Disconnect from Wi-Fi
  WiFi.disconnect();
  SerialPrintln("WiFi disconnected");

  // Stop the server
  server.end();
  SerialPrintln("Server stopped");
  delay(100);
}

void SendStringToTCPClient(String str)
{
  CheckIfClientConnected();
  client.print(str);
  delay(10);
  SerialPrintln("Response sent");
}

void CheckIfClientConnected()
{
  if (!client.connected())
  {
    SerialPrintln("client got disconnected, resetting...");
    NVIC_SystemReset();
    SerialPrintln("Reset failed");
    CloseWiFiConnection();
    EstablishWiFiConnection();
  }
}

bool ReceiveCommandFromTCPClient()
{
  CheckIfClientConnected();
  delay (10);
  if (client.available())
  { 
    SerialPrintln("a new line from TCP was identified!");
    // Read the first line of the request
    String str = client.readStringUntil('\r');
    SerialPrintln(str);
    client.flush(); 
    current_command = str;
    num_of_sub_commands = CountCharacterOccurrences(current_command,'^')+1;
    return true;
  }
  return false;
}