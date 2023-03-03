String Comm;

int output = DAC0;
int input;
int val;
int gain;                 // neue Variable
int16_t val_ic;           // neue Variable
// String inData;
// String tempValue;
String channel;           // neue Variable
String gain_string;       // neue Variable
// int sensorPin = A0;    // select the input pin for the potentiometer
// int sensorValue;
bool isData = false;
int i = 0;
int ledPin = 53;
  
#include "ADS1X15.h"      // Einbinden der Bibliothek zur Verbindung mit einem ADS1115, A/D Wandler  
    
ADS1115 ADS(0x48);        // Adresse des A/D Wandlers im I2C-Bus festlegen und ADS1115 Objekt anlegen  
   
void setup() {  
  Serial.begin(9600);  
  while (!Serial);  
  analogWriteResolution(12);
  analogWrite(DAC0, 0);
  analogWrite(DAC1, 0);
  pinMode(ledPin, OUTPUT);
  ADS.begin();            // Kommunikation mit A/D-Wandler Beginnt
}
  
void loop() {
  while (Serial.available() > 0 ) {
    char value = Serial.read();
    Comm += value;
    if (value == '\n') {
      isData = true;
    }
  }
  if (isData) {
    isData = false;
    if (Comm.startsWith("IDN")) {
      Serial.print("General DAQ Device built by Uetke. v.1.2019");
      Serial.print("\n");
    }
/*    else if (Comm.startsWith("OUT")) {  // Auskommentieren der nicht genutzten Funktionen
      channel = Comm[6];
      if (channel.toInt() == 1) {
        output = DAC1;
      }
      else if (channel.toInt() == 0) {
        output = DAC0;
      }
      tempValue = "";
      for (i = 8; i < Comm.length(); i++) {
        tempValue += Comm[i];
      }
      val = tempValue.toInt();
      analogWrite(output, val);
      Serial.print(tempValue);
    }
    else if (Comm.startsWith("IN")) {
      channel = Comm[5];
      input = channel.toInt();
      val = analogRead(input);
      Serial.print(val);
      Serial.print("\n");
    }
*/
    else if (Comm.startsWith("I2C")) {    // Prüfen, ob Nachricht auf das ADS-Objekt zielt
      gain_string = Comm[6];              // 6. Position der Nachricht, setzt den Gain für die Anfrage, dieser muss vor der Abfrage gesetzt werden
      gain = gain_string.toInt();         // umformen String in Integer, Forderung der folgenden Funktion
      ADS.setGain(gain);                  // Setzen des Gains
      channel = Comm[4];                  // 4. Position der Nachricht, bestimmt den Eingang der ausgewertet werden soll 
      input = channel.toInt();            // umformen String in Integer
      val_ic = ADS.readADC(input);        // Auslesen der Spannung am Eingang als Bit-Wert
      Serial.print(val_ic);               // Rückgabe des Wertes
      Serial.print("\n");
    }
/*    
    else if (Comm.startsWith("DI")){     // Nicht genutzte Funktion
      Serial.println("Digital");
      channel = Comm[3]+Comm[4];
      tempValue = Comm[6];
      if (tempValue.toInt() == 0){
        digitalWrite(ledPin, LOW);
        Serial.println("OFF");
        Serial.println(ledPin);
        }
        else{
          digitalWrite(ledPin, HIGH);
          Serial.println("ON");
          Serial.println(channel.toInt());
          }
    }
*/    
    else {
      Serial.print("Command not known\n");
    }
    Comm = "";
  }
  delay(20);
}
