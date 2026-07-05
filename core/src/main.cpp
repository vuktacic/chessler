#include <Arduino.h>
#include "sensors.h"
#include "relay.h"
#include "motion.h"
#include "chess.h"
#include <mcu-max.h>

static char pieceToFenChar(uint8_t piece) {
    switch (piece) {
        case 1:
        case 2:
            return 'P';
        case 3:
            return 'N';
        case 4:
            return 'K';
        case 5:
            return 'B';
        case 6:
            return 'R';
        case 7:
            return 'Q';
        case 9:
        case 10:
            return 'p';
        case 11:
            return 'n';
        case 12:
            return 'k';
        case 13:
            return 'b';
        case 14:
            return 'r';
        case 15:
            return 'q';
        default:
            return 0;
    }
}

static String boardToFen() {
    String fen;

    for (uint8_t row = 0; row < 8; row++) {
        uint8_t emptySquares = 0;

        for (uint8_t col = 0; col < 8; col++) {
            uint8_t piece = mcumax_get_piece(0x10 * row + col);
            char fenChar = pieceToFenChar(piece);

            if (!fenChar) {
                emptySquares++;
                continue;
            }

            if (emptySquares > 0) {
                fen += String(emptySquares);
                emptySquares = 0;
            }

            fen += fenChar;
        }

        if (emptySquares > 0) {
            fen += String(emptySquares);
        }

        if (row < 7) {
            fen += '/';
        }
    }

    fen += ' ';
    fen += (mcumax_get_current_side() == 0x8) ? 'w' : 'b';
    fen += " - - 0 1";

    return fen;
}

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
    static bool waitingForVerification = false;
    static String expectedFen;

    // wait until next move from pc serial
    while(true) {
        String instruction = "";

        if(Serial.available()) {
            instruction = Serial.readStringUntil('\n');
        }

        if(instruction.startsWith("FEN")) {
            String fen = instruction.substring(4);
            fen.trim();

            if (waitingForVerification) {
                if (expectedFen == fen) {
                    Serial.println("esp_verify_ok");
                } else {
                    Serial.println("esp_verify_mismatch");
                    chess::setBoard(fen);
                    expectedFen = fen;
                }

                waitingForVerification = false;
                continue;
            }

            Serial.println("esp_ack fen");
            chess::setBoard(fen);
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

            expectedFen = boardToFen();
            waitingForVerification = true;
        }
    }
}