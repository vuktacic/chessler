// connect to laptop over serial port

#include <Arduino.h>

namespace relay {
    void connect() {
        Serial.begin(115200);

        Serial.println("esp_connect");

        while(true) {
            // until laptop_ack
            if(Serial.available()) {
                String line = Serial.readStringUntil('\n');
                if(line == "laptop_ack") {
                    Serial.println("esp_ack");
                    break;
                }
            }
        }
    }
}