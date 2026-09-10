#include <HID-Project.h> // Handles standard keys and multimedia natively
#include <EEPROM.h>

const int ROW_NUM    = 4; 
const int COLUMN_NUM = 4; 

int rowPins[ROW_NUM]    = {5, 6, 7, 8};    
int colPins[COLUMN_NUM] = {9, 10, 16, 14}; // Your Pro Micro layout pins

const int MACRO_SIZE = 32; 

void setup() {
  Serial.begin(115200); 
  Keyboard.begin();
  Consumer.begin();
  
  for(int r = 0; r < ROW_NUM; r++) {
    pinMode(rowPins[r], INPUT_PULLUP);
  }
  for(int c = 0; c < COLUMN_NUM; c++) {
    pinMode(colPins[c], OUTPUT);
    digitalWrite(colPins[c], HIGH);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();
    
    if (incoming.startsWith("SET:")) {
      int firstColon = incoming.indexOf(':', 4);
      String coord = incoming.substring(4, firstColon);
      String macroText = incoming.substring(firstColon + 1);
      
      int underScore = coord.indexOf('_');
      int r = coord.substring(0, underScore).toInt();
      int c = coord.substring(underScore + 1).toInt();
      
      int eepromAddress = (r * COLUMN_NUM + c) * MACRO_SIZE;
      
      for (int i = 0; i < MACRO_SIZE; i++) {
        char ch = (i < macroText.length()) ? macroText[i] : '\0';
        EEPROM.write(eepromAddress + i, ch);
      }
      Serial.println("ACK_OK");
    }
  }

  for (int c = 0; c < COLUMN_NUM; c++) {
    digitalWrite(colPins[c], LOW);
    for (int r = 0; r < ROW_NUM; r++) {
      if (digitalRead(rowPins[r]) == LOW) {
        executeOnboardMacro(r, c);
        delay(250); // Debounce delay
      }
    }
    digitalWrite(colPins[c], HIGH);
  }
}

// Helper function to dynamically parse and hold modifier strings
void holdSystemModifier(String keyName) {
  if (keyName == "ctrl")  Keyboard.press(KEY_LEFT_CTRL);
  else if (keyName == "shift") Keyboard.press(KEY_LEFT_SHIFT);
  else if (keyName == "alt")   Keyboard.press(KEY_LEFT_ALT);
  else if (keyName == "win")   Keyboard.press(KEY_LEFT_GUI);
  else if (keyName == "gui")   Keyboard.press(KEY_LEFT_GUI);
}

void executeOnboardMacro(int r, int c) {
  int eepromAddress = (r * COLUMN_NUM + c) * MACRO_SIZE;
  String macroCommand = "";
  
  for (int i = 0; i < MACRO_SIZE; i++) {
    char ch = EEPROM.read(eepromAddress + i);
    if (ch == '\0') break;
    macroCommand += ch;
  }
  
  macroCommand.trim();
  
  // Broadcast the button event to the Serial port for live console logging
  Serial.print("EXEC_KEY:");
  Serial.print(r + 1);
  Serial.print(",");
  Serial.print(c + 1);
  Serial.print("➔");
  Serial.println(macroCommand.length() > 0 ? macroCommand : "[Empty Slot]");

  if (macroCommand.length() == 0) return;

  // 1. Direct hardware terminal interception bypasses
  if (macroCommand == "run:cmd") {
    Keyboard.press(KEY_LEFT_GUI); Keyboard.press('r'); delay(100); Keyboard.releaseAll();
    delay(150); Keyboard.print("cmd"); delay(50); Keyboard.press(KEY_RETURN); delay(50); Keyboard.releaseAll();
  }
  else if (macroCommand == "run:admin_cmd" || macroCommand == "run:powershell -Command \"Start-Process cmd -Verb RunAs\"") {
    Keyboard.press(KEY_LEFT_GUI); Keyboard.press('r'); delay(100); Keyboard.releaseAll();
    delay(150); Keyboard.print("cmd"); delay(50); Keyboard.press(KEY_LEFT_CTRL); Keyboard.press(KEY_LEFT_SHIFT); Keyboard.press(KEY_RETURN); delay(100); Keyboard.releaseAll();
  }
  else if (macroCommand.startsWith("run:")) {
    Serial.print("RUN_CMD:");
    Serial.println(macroCommand);
  }
  // 2. Multimedia controls
  else if (macroCommand == "media:volup") { Consumer.write(MEDIA_VOLUME_UP); }
  else if (macroCommand == "media:voldown") { Consumer.write(MEDIA_VOLUME_DOWN); }
  else if (macroCommand == "media:mute") { Consumer.write(MEDIA_VOLUME_MUTE); } 
  else if (macroCommand == "media:play") { Consumer.write(MEDIA_PLAY_PAUSE); }
  else if (macroCommand == "media:skip") { Consumer.write(MEDIA_NEXT); }
  else if (macroCommand == "media:prev") { Consumer.write(MEDIA_PREVIOUS); }
  
  // 3. ⚡ DYNAMIC HOTKEY COMBINATION SPLITTER ENGINE
  else if (macroCommand.indexOf('+') != -1) {
    String remainder = macroCommand;
    String finalKey = "";
    
    // Loop through and press every system modifier split by a '+' flag sign
    while (remainder.indexOf('+') != -1) {
      int plusIdx = remainder.indexOf('+');
      String modKey = remainder.substring(0, plusIdx);
      modKey.trim();
      holdSystemModifier(modKey);
      remainder = remainder.substring(plusIdx + 1);
    }
    
    // Press the absolute final primary stroke key layout parameter character
    remainder.trim();
    if (remainder.length() > 0) {
      if (remainder == "tab") Keyboard.press(KEY_TAB);
      else if (remainder == "esc") Keyboard.press(KEY_ESC);
      else if (remainder == "enter") Keyboard.press(KEY_RETURN);
      else Keyboard.press(remainder[0]);
    }
    
    delay(50); // Hold combo pattern steady for OS capture execution window
    Keyboard.releaseAll();
  }
  // 4. Plain Text fallback
  else {
    Keyboard.print(macroCommand);
  }
}
