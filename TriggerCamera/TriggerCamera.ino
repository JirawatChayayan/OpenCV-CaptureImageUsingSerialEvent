#include <ArduinoJson.h>

#include "triggerstate.h"
String inputString = "";         // a String to hold incoming data
bool stringComplete = false;  // whether the string is complete

TriggerInput inputRun(11,20);
TriggerInput inputSetup(12,20);

bool SetupMode = true;

DynamicJsonDocument modeJson(1024);

void setup() {
  Serial.begin(115200);
  delay(10);
  Serial.println("###############################################################");
  Serial.println("# Command ChangeMode: {\"Mode\":\"Setup\"} and {\"Mode\":\"Process\"} #");
  Serial.println("###############################################################");
  inputString.reserve(200);
  modeJson["Mode"] = "Setup";
}

void loop() {
  if (stringComplete) {
    
    if(modeJson["Mode"] == "Setup")
    {
      SetupMode = true;
      String res = "{\"Mode\":\"Setup\"}";
      printMsg(true, res);
    }
    else if(modeJson["Mode"] == "Process")
    {
      SetupMode = false;
      String res = "{\"Mode\":\"Process\"}";
      printMsg(true,res);
    }
    else
    {
      printMsg(true,inputString + " Other");
    }
    inputString = "";
    stringComplete = false;
  }
  if(SetupMode)
  {
    bool a = inputSetup.getState();
    if(a)
    {
      String res = "{\"Mode\":\"Setup\"}";
      printMsg(false,res);
    }
  }
  else
  {
    bool b = inputRun.getState();
    if(b)
    {
      String res = "{\"Mode\":\"Process\"}";
      printMsg(false,res);
    }
  }
 
}

void printMsg(bool command,String val)
{
  if(command)
  {
    String s1 = "CommandInput >> ";
    String s3 = s1 + val;
    Serial.println(s3);
  }
  else
  {
    String s1 = "Trig;";
    String s3 = s1 + val;
    Serial.println(s3);
  }
}
void serialEvent() {
  while (Serial.available()) 
  {
    char inChar = (char)Serial.read();
    if (inChar == '\n') 
    {
      stringComplete = true;
      String str = inputString;
      int str_len = str.length() + 1; 
      char char_array[str_len];
      str.toCharArray(char_array, str_len);
      deserializeJson(modeJson, char_array);
    }
    else
    {
      inputString += inChar;
    }
  }
}
