#include "CanController.h"

CanController::CanController(uint8_t rx_pin, uint8_t tx_pin) : _rx_pin(rx_pin), _tx_pin(tx_pin) {}

void CanController::start(const twai_timing_config_t &timingConfig)
{
  twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT((gpio_num_t)_tx_pin, (gpio_num_t)_rx_pin, TWAI_MODE_NORMAL);
  twai_timing_config_t t_config = timingConfig;
  twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK)
  {
    Serial.println("Failed to install driver");
    return;
  }

  if (twai_start() != ESP_OK)
  {
    Serial.println("Failed to start driver");
    return;
  }

  _driver_installed = true;
}

void CanController::stop()
{
  if (_driver_installed)
  {
    twai_stop();
    twai_driver_uninstall();
    _driver_installed = false;
  }
}

bool CanController::send(const twai_message_t &message)
{
  if (!_driver_installed)
    return false;

  return twai_transmit(&message, pdMS_TO_TICKS(1000)) == ESP_OK;
}

bool CanController::receive(twai_message_t &message)
{
  if (!_driver_installed)
    return false;

  return twai_receive(&message, 0) == ESP_OK;
}
