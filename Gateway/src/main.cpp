#include "CanController.h"
#include "UdpCommunicator.h"
#include "WebServerManager.h"
#include "Secrets.h"

// CAN controller pins
#define RX_PIN 4
#define TX_PIN 5

// WiFi credentials and destination settings
const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;
IPAddress remoteIp(192, 168, 0, 5); // PC adress

#define POLLING_RATE_MS 100 // Reduced polling rate for more responsive handling

CanController canController(RX_PIN, TX_PIN);
UdpCommunicator udpCommunicator(remoteIp);
WebServerManager webServerManager(canController, udpCommunicator);

void setup()
{ 
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
  Serial.println(WiFi.localIP());

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
      Serial.println("Failed to forward UDP message to CAN");
      Serial.print("ESP IP4 Address: ");
      Serial.println(WiFi.localIP());
      Serial.print("\n");
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
