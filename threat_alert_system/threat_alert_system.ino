const int buzzerPin = 9;    // Pin connected to buzzer
const int ledPin = 8;       // Pin connected to external LED

char incomingByte = '0';
bool alertState = false;
unsigned long lastBlinkTime = 0;
unsigned long blinkInterval = 200;  // Blink every 200ms
bool ledState = false;
bool buzzerState = false;

void setup() {
  Serial.begin(9600);
  pinMode(buzzerPin, OUTPUT);
  pinMode(ledPin, OUTPUT);

  digitalWrite(buzzerPin, LOW);
  digitalWrite(ledPin, LOW);

  // Startup test
  for (int i = 0; i < 2; i++) {
    digitalWrite(ledPin, HIGH);
    tone(buzzerPin, 1000);
    delay(300);
    noTone(buzzerPin);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
  
  Serial.println("Arduino Ready - Threat Detection System");
}

void loop() {
  // Read serial input - check for new data
  if (Serial.available() > 0) {
    char signal = Serial.read();
    
    // Clear any remaining data in buffer
    while (Serial.available() > 0) {
      Serial.read();
    }
    
    if (signal == '1') {
      if (!alertState) {
        alertState = true;   // Enable blinking/beeping mode
        Serial.println("ALERT ON: Threat Detected!");
        // Reset timing for immediate response
        lastBlinkTime = 0;
      }
    } else if (signal == '0') {
      if (alertState) {
        alertState = false;  // Disable alert
        Serial.println("ALERT OFF: No threat");
        digitalWrite(ledPin, LOW);
        noTone(buzzerPin);
        ledState = false;
        buzzerState = false;
      }
    }
  }

  // Non-blocking alert system using millis()
  if (alertState) {
    unsigned long currentTime = millis();
    
    if (currentTime - lastBlinkTime >= blinkInterval) {
      // Toggle LED and buzzer
      ledState = !ledState;
      digitalWrite(ledPin, ledState ? HIGH : LOW);
      
      if (ledState) {
        tone(buzzerPin, 2000);  // High pitch
      } else {
        tone(buzzerPin, 4000);  // Higher pitch
        delay(50);  // Short delay for pitch change
        noTone(buzzerPin);
      }
      
      lastBlinkTime = currentTime;
    }
  }
}
