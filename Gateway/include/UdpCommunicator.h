#ifndef UdpCommunicator_h
#define UdpCommunicator_h

#include "WiFi.h"
#include "WiFiUdp.h"
#include "Arduino.h"

class UdpCommunicator
{
public:
  UdpCommunicator(const IPAddress &remoteIp);
  void begin();
  void send(uint32_t id, const uint8_t *data, uint8_t length, bool extFlag, bool rtrFlag);
  bool receive(uint32_t &id, uint8_t *data, uint8_t &length, bool &extFlag, bool &rtrFlag);
  void updateRemoteIp(const IPAddress &newRemoteIp);
  void updateFilterId(uint32_t newFilterId); 
  void setFilterEnabled(bool enabled);
  bool shouldSendMessage(uint32_t id);

private:
  IPAddress _remoteIp;
  uint32_t _filterId; 
  bool _filterEnabled = false;
  WiFiUDP _udp;

  int encodeCanEthMessage(uint32_t id, const uint8_t *data, uint8_t length, bool extFlag, bool rtrFlag, uint8_t *buffer);
  bool decodeCanEthMessage(const uint8_t *buffer, int len, uint32_t &id, uint8_t *data, uint8_t &length, bool &extFlag, bool &rtrFlag);
};

#endif