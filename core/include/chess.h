#pragma once
#include <Arduino.h>

namespace chess {
    struct Move {
        uint8_t xi;
        uint8_t yi;
        uint8_t xf;
        uint8_t yf;
        boolean isCapture;
        boolean isPromotion;
        boolean isCastle;
    };

    void setBoard(String fen);

    Move bestMove();
}