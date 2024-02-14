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

    void handleUpdate(AsyncWebServerRequest *request);
    void handleApplyFilter(AsyncWebServerRequest *request);
    
    String getHtmlContent();
};

#endif // WEBSERVERMANAGER_H
