#include "UdpCommunicator.h"
#include <algorithm>

UdpCommunicator::UdpCommunicator(const IPAddress &remoteIp) : _remoteIp(remoteIp) {}

void UdpCommunicator::begin()
{
  _udp.begin(4210);
}

//Updates the IP from the Webserver-Input
void UdpCommunicator::updateRemoteIp(const IPAddress &newRemoteIp)
{
  _remoteIp = newRemoteIp;
}

//Adds the ID input from the Webserver to the Whitelist
void UdpCommunicator::addToWhitelist(uint32_t id) {
    if (std::find(whitelist.begin(), whitelist.end(), id) == whitelist.end()) {
        whitelist.push_back(id);
    }
}

//Adds the ID input from the Webserver to the Blacklist
void UdpCommunicator::addToBlacklist(uint32_t id) {
    if (std::find(blacklist.begin(), blacklist.end(), id) == blacklist.end()) {
        blacklist.push_back(id);
    }
}

//Clears the Whitelist
void UdpCommunicator::clearWhitelist() {
  whitelist.clear(); // Lösche alle Einträge in der Whitelist
}

//Clears the Blacklist
void UdpCommunicator::clearBlacklist() {
  blacklist.clear(); // Lösche alle Einträge in der Blacklist
}

//Returns the Whitelist to show it on the Webserver
String UdpCommunicator::getWhitelistAsString() const {
    String listHtml = "<ul>";
    for (uint32_t id : whitelist) {
        listHtml += "<li>" + String("0x") + String(id, HEX) + "</li>";
    }
    listHtml += "</ul>";
    return listHtml;
}

//Returns the Blacklist to show it on the Webserver
String UdpCommunicator::getBlacklistAsString() const {
    String listHtml = "<ul>";
    for (uint32_t id : blacklist) {
        listHtml += "<li>" + String("0x") + String(id, HEX) + "</li>";
    }
    listHtml += "</ul>";
    return listHtml;
}

//Sets the variable allowAll
//allowAll = true: All messages are being forwarded
//allowAll = false: All messages are being blocked
void UdpCommunicator::setAllowAll(bool allow) {
    allowAll = allow;
}

//Returns allowAll
bool UdpCommunicator::isAllowAllEnabled() const {
    return allowAll;
}

//Checks if the ID from the message is in the White/Blacklist
bool UdpCommunicator::isAllowed(uint32_t id) {
  if (allowAll) {
    // Allow all messages, except the IDs on the Blacklist
    return std::find(blacklist.begin(), blacklist.end(), id) == blacklist.end();
  } else {
    // Block all messages, except the IDs on the Whitelist
    return std::find(whitelist.begin(), whitelist.end(), id) != whitelist.end();
  }
}

//Sends the UDP-Messages to the RemoteIP
void UdpCommunicator::send(uint32_t id, const uint8_t *data, uint8_t length, bool extFlag, bool rtrFlag)
{
  //Check if the ID is on the Black/Whitelist
  if (!isAllowed(id)) {
    return;
  }
  uint8_t buffer[25];
  int messageLength = encodeCanEthMessage(id, data, length, extFlag, rtrFlag, buffer);
  _udp.beginPacket(_remoteIp, 4210);
  _udp.write(buffer, messageLength);
  _udp.endPacket();
}

//Encode the UDP-Message to a CAN Message
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

//Receive the UDP-Messages
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

//Decode the CAN-Message to a UDP-Message
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

