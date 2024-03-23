#include "CanController.h"
#include "UdpCommunicator.h"
#include "WebServerManager.h"
#include "Secrets.h"

// CAN controller pins
#define RX_PIN 4
#define TX_PIN 5

// WiFi and Hotspot settings
//Make sure you adjust the ssid and password in your Secrets.h to your WIFI
//mode = 1: connection with a predefined WIFI
//mode = 2: ESP32 as a WLAN-Access-Point
int mode = 1;
const char *wifi_ssid = WIFI_SSID;
const char *wifi_password = WIFI_PASSWORD;

const char *hotspot_ssid = Hotspot_SSID;
const char *hotspot_password = Hotspot_PASSWORD;
IPAddress remoteIp(192, 168, 42, 182);

#define POLLING_RATE_MS 100 // Reduced polling rate for more responsive handling

CanController canController(RX_PIN, TX_PIN);
UdpCommunicator udpCommunicator(remoteIp);
WebServerManager webServerManager(canController, udpCommunicator);

void setup()
{
  Serial.begin(115200);

  //
  //Connection with a predefined WIFI
  if(mode == 1)
  {
    WiFi.begin(wifi_ssid, wifi_password);
    while (WiFi.status() != WL_CONNECTED)
    {
      delay(500);
      Serial.print(".");
    }
    Serial.println("Connected to WiFi");
    Serial.println(WiFi.localIP());
  }

  //Using the 
  if(mode == 2)
  {
    WiFi.softAP(hotspot_ssid, hotspot_password);
    IPAddress local_IP(192,168,4,1);
    IPAddress gateway(192,168,4,1);
    IPAddress subnet(255,255,255,0);
    WiFi.softAPConfig(local_IP, gateway, subnet);
    Serial.println("Access Point gestartet");
    Serial.print("IP-Adresse: ");
    Serial.println(WiFi.softAPIP());
  }

  canController.start(TWAI_TIMING_CONFIG_500KBITS());
  udpCommunicator.begin();
  webServerManager.begin();
}

void loop()
{
  // Handle incoming UDP messages
  uint32_t id;
  uint8_t data[8];
  uint8_t length;
  bool extFlag, rtrFlag;

  if (udpCommunicator.receive(id, data, length, extFlag, rtrFlag))
  {
    twai_message_t canMessage;
    canMessage.identifier = id;
    canMessage.data_length_code = length;
    memcpy(canMessage.data, data, length);
    canMessage.flags = (extFlag ? TWAI_MSG_FLAG_EXTD : TWAI_MSG_FLAG_NONE) | (rtrFlag ? TWAI_MSG_FLAG_RTR : TWAI_MSG_FLAG_NONE);

    if (canController.send(canMessage))
    {
      Serial.println("UDP message forwarded to CAN\n");
    }
    else
    {
      Serial.println("Failed to forward UDP message to CAN\n");
    }
  }

  // Handle incoming CAN messages
  twai_message_t message;
  while (canController.receive(message))
  {
    Serial.print("CAN message forwarded to UDP");
    udpCommunicator.send(message.identifier, message.data, message.data_length_code, message.flags & TWAI_MSG_FLAG_EXTD, message.flags & TWAI_MSG_FLAG_RTR);
  }

  delay(POLLING_RATE_MS);
}
