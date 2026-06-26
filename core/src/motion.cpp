#include <Arduino.h>
#include "motion.h"
#include "config.h"
#include <TMCStepper.h>
#include <FastAccelStepper.h>
#include "sensors.h"
#include "chess.h"

namespace motion {
    class Electromagnet {
    private:
        uint8_t pin;

    public:
        Electromagnet(uint8_t pin) {
            this->pin = pin;
            ledcSetup(0, 5000, 10);
            ledcAttachPin(pin, 0);
        }

        void setPower(uint8_t power) {
            ledcWrite(0, (power * 1023) / 100);
        }

    };

    // ms1 ms2 -> gnd & gnd then 3v3 & gnd for uart ids
    TMC2209Stepper xstepConfig(&Serial1, 0.11f, 0x00);
    TMC2209Stepper ystepConfig(&Serial1, 0.11f, 0x01);
    FastAccelStepperEngine engine = FastAccelStepperEngine();
    FastAccelStepper* xstepper = NULL;
    FastAccelStepper* ystepper = NULL;

    Electromagnet electromagnet(EM_PIN);

    int32_t mmToSteps(float mm) {
        // calculate based off of gt2 pulley with 20 teeth and 2mm pitch
        return (int32_t)(mm * 200 * 16 / (20 * 2));
    }

    void init() {
        pinMode(TMC_EN, OUTPUT);
        pinMode(X_STEP, OUTPUT);
        pinMode(X_DIR, OUTPUT);
        pinMode(Y_STEP, OUTPUT);
        pinMode(Y_DIR, OUTPUT);
        digitalWrite(TMC_EN, LOW);

        xstepConfig.begin();
        ystepConfig.begin();

        xstepConfig.toff(5);
        ystepConfig.toff(5);

        xstepConfig.rms_current(600);
        ystepConfig.rms_current(600);

        xstepConfig.microsteps(16);
        ystepConfig.microsteps(16);

        xstepConfig.pwm_autoscale(true);

        engine.init();
        xstepper = engine.stepperConnectToPin(X_STEP);
        ystepper = engine.stepperConnectToPin(Y_STEP);

        if(xstepper && ystepper) {
            xstepper->setDirectionPin(X_DIR);
            xstepper->setEnablePin(TMC_EN);
            xstepper->setAutoEnable(true);

            ystepper->setDirectionPin(Y_DIR);
            ystepper->setEnablePin(TMC_EN);
            ystepper->setAutoEnable(true);

            xstepper->setSpeedInHz(1000);
            ystepper->setSpeedInHz(1000);

            xstepper->setAcceleration(100);
            ystepper->setAcceleration(100);
        }
    }

    void home() {
        xstepper->runForward();

        while(!sensors::getXEndstop()) {}

        xstepper->stopMove();
        xstepper->setCurrentPosition(0);



        ystepper->runForward();

        while(!sensors::getYEndstop()) {}

        ystepper->stopMove();
        ystepper->setCurrentPosition(0);
    }

    void moveTo(int32_t xi, int32_t yi, int32_t xf, int32_t yf, boolean threaded) {
        // xstepper->moveTo(x);
        // ystepper->moveTo(yf);

        if(!threaded) {
            xstepper->moveTo(mmToSteps(22.5f + (45.0f * xf)));
            ystepper->moveTo(mmToSteps(22.5f + (45.0f * yf)));

            while(xstepper->isRunning() || ystepper->isRunning()) {}
        }
        else {
            // xstepper->moveTo(mmToSteps(22.5f + (45.0f * x)));
            // ystepper->moveTo(mmToSteps(22.5f + (45.0f * yf)));
            float xadj = 22.5f;
            float yadj = 22.5f;
            if(xf > 4) xadj = -xadj;
            if(yf > 4) yadj = -yadj;

            // thread between ranks & files
            xstepper->moveTo(mmToSteps(22.5f + (45.0f * xi) + xadj));
            while(xstepper->isRunning()) {}
            ystepper->moveTo(mmToSteps(22.5f + (45.0f * yi) + yadj));
            while(ystepper->isRunning()) {}

            xstepper->moveTo(mmToSteps(22.5f + (45.0f * xf) - xadj));
            while(xstepper->isRunning()) {}
            ystepper->moveTo(mmToSteps(22.5f + (45.0f * yf) - yadj));
            while(ystepper->isRunning()) {}

            xstepper->moveTo(mmToSteps(22.5f + (45.0f * xf)));
            while(xstepper->isRunning()) {}
            ystepper->moveTo(mmToSteps(22.5f + (45.0f * yf)));
            while(ystepper->isRunning()) {}
        }
    }

    void moveTo(const chess::Move& move, boolean threaded) {
        moveTo(move.xi, move.yi, move.xf, move.yf, threaded);
    }

    void pickUp() {
        electromagnet.setPower(100);
        delay(250);
        electromagnet.setPower(50);
    }

    void drop() {
        electromagnet.setPower(0);
    }
}