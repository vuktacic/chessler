#include <Arduino.h>
#include "chess.h"
#include <mcu-max.h>

namespace chess {
    void setBoard(String fen) {
        mcumax_set_fen_position(fen.c_str());
        mcumax_init();
    }
    
    Move bestMove() {
        Move move;
        mcumax_move best = mcumax_search_best_move(300000, 15);
        move.xi = best.from & 0x0F;
        move.yi = best.from >> 4;

        move.xf = best.to & 0x0F;
        move.yf = best.to >> 4;

        if (mcumax_get_piece(best.to) != MCUMAX_EMPTY) {
            move.isCapture = true;
        } else {
            move.isCapture = false;
        };

        return move;
    }
}