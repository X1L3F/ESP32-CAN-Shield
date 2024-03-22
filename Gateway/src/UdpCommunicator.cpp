#include "UdpCommunicator.h"

UdpCommunicator::UdpCommunicator(const IPAddress &remoteIp) : _remoteIp(remoteIp) {}

void UdpCommunicator::begin()
{
  _udp.begin(4210);
}

void UdpCommunicator::updateRemoteIp(const IPAddress &newRemoteIp)
{
  _remoteIp = newRemoteIp;
}

void UdpCommunicator::updateFilterId(uint32_t newFilterId) {
    _filterId = newFilterId;
    Serial.print("Filtering for CAN ID: 0x");
    Serial.println(_filterId, HEX);
}

void UdpCommunicator::setFilterEnabled(bool enabled) {
    _filterEnabled = enabled;
    Serial.print("Filtering ");
    Serial.println(enabled ? "enabled" : "disabled");
}


bool UdpCommunicator::shouldSendMessage(uint32_t id) {
    // Wenn Filterung aktiv ist, prüfe die CAN-ID
    if (_filterEnabled) {
        return id == _filterId;
    }
    return true; // Wenn keine Filterung aktiv ist, sende alle Nachrichten
}

void UdpCommunicator::send(uint32_t id, const uint8_t *data, uint8_t length, bool extFlag, bool rtrFlag)
{
  if (!shouldSendMessage(id)) {
    return; // Nicht senden, wenn die ID gefiltert wird
  }
  uint8_t buffer[25];
  int messageLength = encodeCanEthMessage(id, data, length, extFlag, rtrFlag, buffer);
  _udp.beginPacket(_remoteIp, 4210);
  _udp.write(buffer, messageLength);
  _udp.endPacket();
}

int UdpCommunicator::encodeCanEthMessage(uint32_t id, const uint8_t *data, uint8_t length, bool extFlag, bool rtrFlag, uint8_t *buffer)
{
  const char *magicId = "ISO11898"; // CANETH protocol magic identifier
  memcpy(buffer, magicId, 8);       // Copy magic identifier to buffer

  buffer[8] = 1; // Protocol version
  buffer[9] = 1; // Frame count

  // Encode CAN ID (4 bytes)
  buffer[10] = id & 0xFF;
  buffer[11] = (id >> 8) & 0xFF;
  buffer[12] = (id >> 16) & 0xFF;
  buffer[13] = (id >> 24) & 0xFF;

  buffer[14] = length; // Data length code (DLC)

  // Copy CAN data
  for (int i = 0; i < 8; i++)
  {
    buffer[15 + i] = (i < length) ? data[i] : 0;
  }

  // Set flags for Extended ID and RTR
  buffer[23] = extFlag ? 1 : 0; // Extended ID flag
  buffer[24] = rtrFlag ? 1 : 0; // Remote Transmission Request flag

  return 25; // Total length of encoded message
}

bool UdpCommunicator::receive(uint32_t &id, uint8_t *data, uint8_t &length, bool &extFlag, bool &rtrFlag)
{
  int packetSize = _udp.parsePacket();
  if (packetSize)
  {
    uint8_t buffer[packetSize];
    int len = _udp.read(buffer, sizeof(buffer));
    return decodeCanEthMessage(buffer, len, id, data, length, extFlag, rtrFlag);
  }
  return false;
}

bool UdpCommunicator::decodeCanEthMessage(const uint8_t *buffer, int len, uint32_t &id, uint8_t *data, uint8_t &length, bool &extFlag, bool &rtrFlag)
{
  if (len >= 25 && strncmp((const char *)buffer, "ISO11898", 8) == 0)
  {
    id = buffer[10] | buffer[11] << 8 | buffer[12] << 16 | buffer[13] << 24;
    length = buffer[14];
    for (int i = 0; i < length; i++)
    {
      data[i] = buffer[15 + i];
    }
    extFlag = buffer[23] == 1;
    rtrFlag = buffer[24] == 1;
    return true;
  }
  return false;
}