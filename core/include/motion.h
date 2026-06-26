#pragma once
#include <Arduino.h>
#include <TMCStepper.h>
#include "chess.h"

namespace motion {
    void init();
    void home();

    void moveTo(int32_t xi, int32_t yi, int32_t xf, int32_t yf, boolean threaded = false);
    void moveTo(const chess::Move &move, boolean threaded = false);
    void pickUp();
    void drop();
}