#ifndef UdpCommunicator_h
#define UdpCommunicator_h

#include "WiFi.h"
#include "WiFiUdp.h"
#include "Arduino.h"
#include <vector>


class UdpCommunicator {
public:
    UdpCommunicator(const IPAddress &remoteIp);
    void begin();
    void send(uint32_t id, const uint8_t *data, uint8_t length, bool extFlag, bool rtrFlag);
    bool receive(uint32_t &id, uint8_t *data, uint8_t &length, bool &extFlag, bool &rtrFlag);
    void updateRemoteIp(const IPAddress &newRemoteIp);
    void setAllowAll(bool allow);
    void addToWhitelist(uint32_t id);
    void addToBlacklist(uint32_t id);
    void clearWhitelist();
    void clearBlacklist();
    bool isAllowAllEnabled() const;
    String getWhitelistAsString() const;
    String getBlacklistAsString() const;

private:
    IPAddress _remoteIp;
    WiFiUDP _udp;
    std::vector<uint32_t> whitelist;
    std::vector<uint32_t> blacklist;
    bool allowAll = true;

    int encodeCanEthMessage(uint32_t id, const uint8_t *data, uint8_t length, bool extFlag, bool rtrFlag, uint8_t *buffer);
    bool decodeCanEthMessage(const uint8_t *buffer, int len, uint32_t &id, uint8_t *data, uint8_t &length, bool &extFlag, bool &rtrFlag);
    bool isAllowed(uint32_t id);
};

#endif