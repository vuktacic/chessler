#include "Arduino.h"
#include "config.h"

namespace sensors {
    void init() {
        pinMode(Y_ENDSTOP, INPUT);
        pinMode(X_ENDSTOP, INPUT);
    }

    boolean getYEndstop() {
        return digitalRead(Y_ENDSTOP) == LOW;
    }

    boolean getXEndstop() {
        return digitalRead(X_ENDSTOP) == LOW;
    }
}