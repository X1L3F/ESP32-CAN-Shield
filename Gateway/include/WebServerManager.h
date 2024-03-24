#ifndef WEBSERVERMANAGER_H
#define WEBSERVERMANAGER_H

#include <ESPAsyncWebServer.h>
#include "CanController.h"
#include "UdpCommunicator.h"

class WebServerManager
{
public:
    WebServerManager(CanController &canController, UdpCommunicator &udpCommunicator);
    void begin();

private:
    AsyncWebServer server;
    CanController &canController;
    UdpCommunicator &udpCommunicator;
    String storedRemoteIp = "192.168.4.1";
    String currentBitRate = "500KBITS"; // Standardwert für die Bitrate

    void handleUpdate(AsyncWebServerRequest *request);  
    String getHtmlContent();

};

#endif // WEBSERVERMANAGER_H