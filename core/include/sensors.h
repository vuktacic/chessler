#pragma once
#include <Arduino.h>

namespace sensors {
    void init();
    boolean getYEndstop();
    boolean getXEndstop();
}