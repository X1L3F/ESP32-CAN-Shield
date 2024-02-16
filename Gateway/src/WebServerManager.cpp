#include "WebServerManager.h"

WebServerManager::WebServerManager(CanController &canCtrl, UdpCommunicator &udpComm)
    : server(80), canController(canCtrl), udpCommunicator(udpComm) {}

void WebServerManager::begin() {
    server.on("/", HTTP_GET, [this](AsyncWebServerRequest *request) {
        request->send(200, "text/html", getHtmlContent());
    });

    server.on("/update", HTTP_POST, [this](AsyncWebServerRequest *request) {
        this->handleUpdate(request);
    });

    server.on("/applyFilter", HTTP_POST, [this](AsyncWebServerRequest *request) {
        this->handleApplyFilter(request);
    });

    server.on("/restart", HTTP_GET, [this](AsyncWebServerRequest *request) {
        request->send(200, "text/html", "ESP Neugestartet!<br><a href='/'>Go Back</a>");
        delay(1000); // Kurze Verzögerung
        ESP.restart();
    });

    server.begin();
}

String WebServerManager::getHtmlContent() {
    return R"(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAN Configuration</title>
</head>
<body>
    <h1>CAN Configuration</h1>
    <form action="/update" method="post">
        <label for="remoteIp">Remote IP:</label>
        <input type="text" id="remoteIp" name="remoteIp" placeholder="192.168.4.1">
        <label for="canBitRate">CAN Bit Rate:</label>
        <select name="canBitRate" id="canBitRate">
            <option value="1MBITS">1 Mbit/s</option>
            <option value="800KBITS">800 Kbit/s</option>
            <option value="500KBITS" selected>500 Kbit/s</option>
            <option value="250KBITS">250 Kbit/s</option>
            <option value="125KBITS">125 Kbit/s</option>
            <option value="100KBITS">100 Kbit/s</option>
            <option value="50KBITS">50 Kbit/s</option>
            <option value="25KBITS">25 Kbit/s</option>
        </select>
        <input type="submit" value="Update Settings">
    </form>
    <br>
    <form action="/applyFilter" method="post">
        <label for="canIdFilter">CAN ID Filter:</label>
        <input type="text" id="canIdFilter" name="canIdFilter" placeholder="0x123">
        <input type="submit" name="filterAction" value="Enable Filter">
        <input type="submit" name="filterAction" value="Disable Filter">
    </form>
    <br>
    <form action="/restart" method="get">
        <input type="submit" value="Neustart">
    </form>
</body>
</html>
    )";
}

void WebServerManager::handleUpdate(AsyncWebServerRequest *request)
{
    if (request->hasParam("remoteIp", true) && request->hasParam("canBitRate", true))
    {
        String newIp = request->getParam("remoteIp", true)->value();
        IPAddress newRemoteIp;
        newRemoteIp.fromString(newIp);
        udpCommunicator.updateRemoteIp(newRemoteIp);

        String canBitRate = request->getParam("canBitRate", true)->value();
        twai_timing_config_t timingConfig;

        if (canBitRate == "1MBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_1MBITS();
        }
        else if (canBitRate == "800KBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_800KBITS();
        }
        else if (canBitRate == "500KBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_500KBITS();
        }
        else if (canBitRate == "250KBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_250KBITS();
        }
        else if (canBitRate == "125KBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_125KBITS();
        }
        else if (canBitRate == "100KBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_100KBITS();
        }
        else if (canBitRate == "50KBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_50KBITS();
        }
        else if (canBitRate == "25KBITS")
        {
            timingConfig = TWAI_TIMING_CONFIG_25KBITS();
        }
        else
        {
            request->send(400, "text/html", "Invalid CAN bit rate!<br><a href='/'>Try Again</a>");
            return;
        }

        // Stop and start the CAN controller with the new timing configuration
        canController.stop();
        canController.start(timingConfig);

        request->send(200, "text/html", "Settings updated!<br><a href='/'>Go Back</a>");
    }
    else
    {
        request->send(400, "text/html", "Missing information!<br><a href='/'>Try Again</a>");
    }
}

void WebServerManager::handleApplyFilter(AsyncWebServerRequest *request) {
    if (request->hasParam("canIdFilter", true)) {
        String canIdFilter = request->getParam("canIdFilter", true)->value();
        uint32_t canId = strtoul(canIdFilter.c_str(), nullptr, 16); // Umwandlung in eine Zahl
        udpCommunicator.updateFilterId(canId);
    }

    // Überprüfe, welche Aktion ausgeführt werden soll
    if (request->hasParam("filterAction", true)) {
        String action = request->getParam("filterAction", true)->value();
        if (action == "Enable Filter") {
            udpCommunicator.setFilterEnabled(true);
        } else if (action == "Disable Filter") {
            udpCommunicator.setFilterEnabled(false);
        }
    }

    request->send(200, "text/html", "Filter settings updated!<br><a href='/'>Go Back</a>");
}

