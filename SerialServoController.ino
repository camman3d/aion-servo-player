#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Create objects for the two PCA9685 boards
Adafruit_PWMServoDriver pwm1 = Adafruit_PWMServoDriver();  // Default address 0x40
Adafruit_PWMServoDriver pwm2 = Adafruit_PWMServoDriver(0x41);  // Address 0x41 (A0 soldered)

const int NUM_SERVOS = 20;  // Total number of servos (16 per board)

void setup() {
  Serial.begin(115200);
  
  pwm1.begin();
  pwm2.begin();
  
  pwm1.setPWMFreq(50);  // Analog servos run at ~50 Hz updates
  pwm2.setPWMFreq(50);

  delay(10);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    int spaceIndex = input.indexOf(' ');
    if (spaceIndex != -1) {
      int address = input.substring(0, spaceIndex).toInt();
      int value = input.substring(spaceIndex + 1).toInt();
      
      if (address >= 0 && address < NUM_SERVOS) {
        setServo(address, value);
      } else {
        Serial.print("Invalid address: ");
        Serial.println(address);
      }
    } else {
      Serial.println("Invalid input format. Use 'address value'");
    }
  }
}

void setServo(int address, int value) {
  
  if (address < 16) {
    pwm1.setPWM(address, 0, value);
  } else if (address < 32) {
    pwm2.setPWM(address - 16, 0, value);
  }
  
  Serial.print("Set servo ");
  Serial.print(address);
  Serial.print(" to value ");
  Serial.println(value);
}