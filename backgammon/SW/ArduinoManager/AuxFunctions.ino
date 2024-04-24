
void SplitString(String inputString, char delimiter, String outputArray[], int outputSize) {
  int index = 0;
  int start = 0;
  int end = inputString.indexOf(delimiter);

  while (end >= 0 && index < outputSize - 1) {
    outputArray[index] = inputString.substring(start, end);
    start = end + 1;
    end = inputString.indexOf(delimiter, start);
    index++;
  }

  // Add the last section of the string
  outputArray[index] = inputString.substring(start);
}

String GetSectionByIndex(String inputString, int index, char delimiter) 
{
  String section = "";
  int currentIndex = 0;
  int sectionIndex = 0;

  for (int i = 0; i < inputString.length(); i++) {
    if (inputString[i] == delimiter) {
      sectionIndex++;
      if (sectionIndex == index) {
        // Found the desired section
        break;
      } else {
        // Move to the next section
        section = "";
      }
    } else {
      section += inputString[i];
    }
  }

  return section;
}


int ExtractNumber(String input) 
{
  // Find the position of the colon in the string
  int colonIndex = input.indexOf(':');

  // Extract the substring after the colon
  String numberString = input.substring(colonIndex + 1);

  // Convert the substring to an integer
  int extractedNumber = numberString.toInt();

  return extractedNumber;
}

int CountCharacterOccurrences(String inputString, char targetChar) 
{
  int occurrences = 0;

  // Iterate through the characters in the string
  for (int i = 0; i < inputString.length(); i++) {
    // Check if the current character is the target character
    if (inputString[i] == targetChar) {
      occurrences++;
    }
  }

  return occurrences;
}

String GetSectionBySubstring(String inputString, String subs, char delimiter) 
{
  int startPos = 0;
  int endPos = inputString.indexOf(delimiter);
  int first_occurance = inputString.indexOf(subs);

  if (first_occurance==-1)
    return "";
  while (endPos != -1) {
    String section = inputString.substring(startPos, endPos);
    
    // Check if the substring 'subs' is present in the current section
    if (section.indexOf(subs) != -1) {
      return section;
    }
    
    startPos = endPos + 1;
    endPos = inputString.indexOf(delimiter, startPos);
  }

  // Check the last section
  String lastSection = inputString.substring(startPos);
  if (lastSection.indexOf(subs) != -1) {
    return lastSection;
  }

  // Return an empty string if 'subs' is not found in any section
  return "";
}



Coordinates ExtractXYValues(String inputString) 
{
  Coordinates coordinates;

  // Find the index of 'X' and 'Y' in the input string
  int xIndex = inputString.indexOf('X');
  int yIndex = inputString.indexOf('Y');

  // Extract X value
  if (xIndex != -1) {
    String xSubstring = inputString.substring(xIndex + 1);
    int spaceIndex = xSubstring.indexOf(' ');
    if (spaceIndex != -1) {
      xSubstring = xSubstring.substring(0, spaceIndex);
    }
    coordinates.xValue = xSubstring.toFloat();
  } else {
    coordinates.xValue = 0.0;
  }

  // Extract Y value
  if (yIndex != -1) {
    String ySubstring = inputString.substring(yIndex + 1);
    int spaceIndex = ySubstring.indexOf(' ');
    if (spaceIndex != -1) {
      ySubstring = ySubstring.substring(0, spaceIndex);
    }
    coordinates.yValue = ySubstring.toFloat();
  } else {
    coordinates.yValue = 0.0;
  }

  return coordinates;
}


bool ParseMPosString(const char* input, float& x, float& y) 
{
  // Copy the input string to a modifiable buffer
  char buffer[strlen(input) + 1];
  strcpy(buffer, input);

  // Tokenize the string based on ":" and ","
  char* token = strtok(buffer, ":,");
  
  // Check if the first token is "MPos"
  if (token == NULL || strcmp(token, "MPos") != 0) {
    // Invalid format, return false
    return false;
  }

  // Get the next token (x value)
  token = strtok(NULL, ":,");
  if (token == NULL) {
    // Missing x value, return false
    return false;
  }
  x = atof(token);

  // Get the next token (y value)
  token = strtok(NULL, ":,");
  if (token == NULL) {
    // Missing y value, return false
    return false;
  }
  y = atof(token);

  // Extraction successful, return true
  return true;
}

String RemovePercent(const String &original) 
{
  // Find the start index after removing leading '%'
  int startIndex = 0;
  while (original.charAt(startIndex) == '%') {
    startIndex++;
  }

  // Find the end index before removing trailing '%'
  int endIndex = original.length() - 1;
  while (endIndex >= 0 && original.charAt(endIndex) == '%') {
    endIndex--;
  }

  // Extract the substring without '%' characters
  return original.substring(startIndex, endIndex + 1);
}