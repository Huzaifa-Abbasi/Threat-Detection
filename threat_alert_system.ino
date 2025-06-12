// Threat Alert System - Arduino Code

const int buzzerPin = 9;    // Pin connected to the buzzer
const int ledPin = 13;      // Pin connected to the LED (built-in LED on pin 13)

char incomingByte = '0';    // For incoming serial data

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  Serial.println("Arduino Threat Alert System Ready");
  
  // Initialize output pins
  pinMode(buzzerPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  
  // Initially turn off the buzzer and LED
  digitalWrite(buzzerPin, LOW);
  digitalWrite(ledPin, LOW);
  
  // Startup sequence to confirm hardware is working
  digitalWrite(ledPin, HIGH);
  tone(buzzerPin, 1000);
  delay(300);
  noTone(buzzerPin);
  digitalWrite(ledPin, LOW);
  delay(200);
  digitalWrite(ledPin, HIGH);
  tone(buzzerPin, 1000);
  delay(300);
  noTone(buzzerPin);
  digitalWrite(ledPin, LOW);
}

void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    // Read the incoming byte
    incomingByte = Serial.read();
    
    // If '1' is received (threat detected)
    if (incomingByte == '1') {
      digitalWrite(ledPin, HIGH);    // Turn on LED
      tone(buzzerPin, 1000);         // Turn on buzzer with 1kHz tone
      Serial.println("ALERT ON: Threat Detected!");
    }
    // If '0' is received (no threat)
    else if (incomingByte == '0') {
      digitalWrite(ledPin, LOW);     // Turn off LED
      noTone(buzzerPin);             // Turn off buzzer
      Serial.println("Alert OFF: No threat");
    }
  }
} 