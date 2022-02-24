#include "triggerstate.h"
String inputString = "";         // a String to hold incoming data
bool stringComplete = false;  // whether the string is complete

TriggerInput inputRun(D1,10);
TriggerInput inputSetup(D2,10);

bool SetupMode = true;

void setup() {
  Serial.begin(115200);
  delay(10);
  Serial.println("");
  Serial.println("###############################################################");
  Serial.println("# Command ChangeMode: {\"Mode\":\"Setup\"} and {\"Mode\":\"Process\"} #");
  Serial.println("###############################################################\r\n\r\n");
  inputString.reserve(200);
}

void loop() {
  if (stringComplete) {
    if(inputString == "{\"Mode\":\"Setup\"}")
    {
      SetupMode = true;
    }
    else if(inputString == "{\"Mode\":\"Process\"}")
    {
      SetupMode = false;
    }
    printMsg(true,inputString);
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
    }
    else
    {
      inputString += inChar;
    }
  }
}
