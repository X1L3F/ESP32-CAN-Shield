#ifndef CanController_h
#define CanController_h

#include "driver/twai.h"
#include <Arduino.h>

class CanController
{
public:
  CanController(uint8_t rx_pin, uint8_t tx_pin);
  void start(const twai_timing_config_t &timingConfig);
  void stop();
  bool send(const twai_message_t &message);
  bool receive(twai_message_t &message);

private:
  uint8_t _rx_pin, _tx_pin;
  bool _driver_installed = false;
};

#endif
