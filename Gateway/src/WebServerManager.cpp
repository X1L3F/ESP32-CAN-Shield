#include "WebServerManager.h"

WebServerManager::WebServerManager(CanController &canCtrl, UdpCommunicator &udpComm)
    : server(80), canController(canCtrl), udpCommunicator(udpComm) {}

//Handles the User-Inputs from the Webserver
//and calls the corresponding functions to update the lists/variables from the UPD communicator.
void WebServerManager::begin() {
    server.on("/", HTTP_GET, [this](AsyncWebServerRequest *request) {
        request->send(200, "text/html", getHtmlContent());
    });

    //Update the Settings
    server.on("/update", HTTP_POST, [this](AsyncWebServerRequest *request) {
        this->handleUpdate(request);
    });

    //Restart the ESP32
    server.on("/restart", HTTP_GET, [this](AsyncWebServerRequest *request) {
        request->send(200, "text/html", "ESP Restarted!<br><a href='/'>Go Back</a>");
        delay(1000); // Kurze Verzögerung
        ESP.restart();
    });

    //Allow all messages
    server.on("/allowAll", HTTP_GET, [this](AsyncWebServerRequest *request) {
        udpCommunicator.setAllowAll(true);
        request->send(200, "text/html", "All messages are allowed, except Blacklist.<br><a href='/'>Go Back</a>");
    });

    //Block all messages
    server.on("/blockAll", HTTP_GET, [this](AsyncWebServerRequest *request) {
        udpCommunicator.setAllowAll(false);
        request->send(200, "text/html", "Block all messages, except Whitelist.<br><a href='/'>Go Back</a>");
    });

    //Update the Black/Whitelist
    server.on("/updateList", HTTP_POST, [this](AsyncWebServerRequest *request) {
        if (request->hasParam("canId", true) && request->hasParam("listAction", true)) {
            String canIdStr = request->getParam("canId", true)->value();
            uint32_t canId = strtoul(canIdStr.c_str(), nullptr, 16); // CAN-ID von String zu uint32_t konvertieren
            String action = request->getParam("listAction", true)->value();
            
            if (action == "Add to Whitelist") {
                udpCommunicator.addToWhitelist(canId);
            } else if (action == "Add to Blacklist") {
                udpCommunicator.addToBlacklist(canId);
            }
            
            request->send(200, "text/html", "List updated!<br><a href='/'>Go Back</a>");
        } else {
            request->send(400, "text/html", "Missing information!<br><a href='/'>Go Back</a>");
        }
    });

    //Clears the Black/Whitelist
    server.on("/clearList", HTTP_POST, [this](AsyncWebServerRequest *request) {
        if (request->hasParam("listAction", true)) {
            String action = request->getParam("listAction", true)->value();
            
            if (action == "Delete Whitelist") {
                udpCommunicator.clearWhitelist();
            } else if (action == "Delete Blacklist") {
                udpCommunicator.clearBlacklist();
            }
            
            request->send(200, "text/html", "Deleted List!<br><a href='/'>Go Back</a>");
        } else {
            request->send(400, "text/html", "Missing Information!<br><a href='/'>Go Back</a>");
        }
    });

    server.begin();
}

//HTML-Code of the Webserver
String WebServerManager::getHtmlContent() {
    bool allowAll = udpCommunicator.isAllowAllEnabled();
    String allowAllButtonClass = allowAll ? "button-active" : "button-inactive";
    String blockAllButtonClass = !allowAll ? "button-active" : "button-inactive";
    String bitrateOptions[8] = {"1MBITS", "800KBITS", "500KBITS", "250KBITS", "125KBITS", "100KBITS", "50KBITS", "25KBITS"};
    String optionsHtml = "";
    for (const String &option : bitrateOptions) {
        optionsHtml += "<option value=\"" + option + "\"" + (option == currentBitRate ? " selected" : "") + ">" + option + "</option>\n";
    }
    String whitelistHtml = udpCommunicator.getWhitelistAsString();
    String blacklistHtml = udpCommunicator.getBlacklistAsString();

    return R"(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAN Configuration</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 0;
            background-color: #f4f4f4;
        }
        h1 {
            color: #333;
        }
        form, .container {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .container {
            display: flex;
            justify-content: space-between;
        }
        .column {
            width: 48%;
        }
        label {
            margin-top: 10px;
            display: block;
            color: #666;
        }
        input[type="text"], select, button {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: 1px solid #ddd;
            box-sizing: border-box;
        }
        button {
            background-color: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            opacity: 0.8;
        }
        .button-inactive {
            background-color: #6c757d;
        }
    </style>
</head>
<body>
    <h1>CAN Configuration</h1>
    <form action="/update" method="post">
        <label for="remoteIp">Remote IP:</label>
        <input type="text" id="remoteIp" name="remoteIp" placeholder="192.168.4.1" value=")" + storedRemoteIp + R"(">
        <label for="canBitRate">CAN Bit Rate:</label>
        <select name="canBitRate" id="canBitRate">)" + optionsHtml + R"(</select>
        <button type="submit">Update Settings</button>
    </form>

    <h1>Filter Settings</h1>
    <div class="container">
        <div class="column">
            <form action="/allowAll" method="get">
                <button type="submit" class=")" + allowAllButtonClass + R"(">Allow all messages</button>
            </form>
            <form action="/updateList" method="post">
                <label for="canId">CAN ID:</label>
                <input type="text" id="canId" name="canId" placeholder="e.g. 0x123">
                <button type="submit" name="listAction" value="Add to Blacklist">Add to Blacklist</button>
            </form>
            <form action="/clearList" method="post">
                <button type="submit" name="listAction" value="Delete Blacklist">Delete Blacklist</button>
            </form>
            <h2>Blacklist</h2>
            )" + blacklistHtml + R"(
        </div>
        <div class="column">
            <form action="/blockAll" method="get">
                <button type="submit" class=")" + blockAllButtonClass + R"(">Block all messages</button>
            </form>
            <form action="/updateList" method="post">
                <label for="canId">CAN ID:</label>
                <input type="text" id="canId" name="canId" placeholder="e.g. 0x123">
                <button type="submit" name="listAction" value="Add to Whitelist">Add to Whitelist</button>
            </form>
            <form action="/clearList" method="post">
                <button type="submit" name="listAction" value="Delete Whitelist">Delete Whitelist</button>
            </form>
            <h2>Whitelist</h2>
            )" + whitelistHtml + R"(
        </div>
    </div>

    <form action="/restart" method="get">
        <input type="submit" value="Restart">
    </form>
</body>
</html>
    )";
}

//Calls the corresponding functions from the UdpCommunicator to update the settings
void WebServerManager::handleUpdate(AsyncWebServerRequest *request)
{
    if (request->hasParam("remoteIp", true) && request->hasParam("canBitRate", true))
    {
        String newIp = request->getParam("remoteIp", true)->value();
        storedRemoteIp = newIp; // Speichere die neue IP-Adresse
        IPAddress newRemoteIp;
        currentBitRate = request->getParam("canBitRate", true)->value();
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


