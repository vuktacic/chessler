#include <Arduino.h>
#include "sensors.h"
#include "relay.h"
#include "motion.h"
#include "chess.h"

void setup() {
    sensors::init();
    relay::connect();
    motion::init();
    motion::home();
    
    // wait for pc message
    while(true) {
        if(Serial.available()) {
            String line = Serial.readStringUntil('\n');
            if(line == "pc_start") {
                Serial.println("esp_ack");
                break;
            }
        }
    }
}

void loop() {
    // wait until next move from pc serial
    while(true) {
        String instruction = "";

        if(Serial.available()) {
            instruction = Serial.readStringUntil('\n');
        }

        if(instruction.startsWith("FEN")) {
            Serial.println("esp_ack fen");
            chess::setBoard(instruction.substring(4));
            chess::Move move = chess::bestMove();

            // if capture, move piece out of way first
            if(move.isCapture) {
                motion::moveTo(move.xf, move.yf, 0, 0, false);
                motion::pickUp();
                motion::moveTo(move.xf, move.yf, 0, 0, true);
                motion::drop();
            }

            motion::moveTo(move.xi, move.yi, 0, 0, false);
            motion::pickUp();
            motion::moveTo(move, true);
            motion::drop();
            // verify new state
        }
    }
}