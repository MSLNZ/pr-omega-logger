/*
  Uses an Arduino MKR Zero board, a MKR 485 shield and a MKR ETH Shield
  to communicate with a Vaisala HMP110-M00E5C3B0 sensor.

  According to the manual

    "RS-485 termination must not be used with HMP60/HMP110 series probes"
   
  therefore, DIP switches 1 and 3 are in the OFF (unterminated) position.
  DIP switch 2 is in the OFF (HALF duplex) position.

  Connecting the sensor to the shield:

      HMP110 Sensor       RS-485 Shield
    ------------------    -------------
    Pin 1, Vdc (brown) -> ISO Vcc
    Pin 2, -/B (white) -> Z
    Pin 3, GND (blue)  -> ISO GND
    Pin 4, +/A (black) -> Y

  The arduino Ethernet.h and Ethernet.cpp code has been modified to support
  hostname assignment in Ethernet.begin().
 */
#include <Ethernet.h>
#include <ArduinoModbus.h>

// IMPORTANT: set a network unique MAC address for the Ethernet Shield
uint8_t mac[6] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};

char json[256];
char hostname[16];
EthernetServer server(80);

union {
  uint32_t x;
  float f;
} u;

void setup() {
  // use the last two bytes of the MAC address to generate the hostname 
  sprintf(hostname, "pr-arduino-%02x%02x", mac[4], mac[5]);

  // connect to the network via DHCP
  while (Ethernet.begin(mac, hostname) == 0) {
    delay(1000);  // delay in ms
  }

  // start the web server
  server.begin();

  // connect to the HMP110 sensor
  ModbusRTUClient.begin(19200, SERIAL_8N2);
}

void loop() {
  EthernetClient client = server.available();
  if (client) {
    String request = "";
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        request += c;
        if (c == '\n') {
          if (request.startsWith("GET /vaisala ")) {
            readSensor();
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type: application/json");
            client.println("Connection: close");
            client.println();
            client.println(json);
          } else {
            client.println("HTTP/1.1 400 Bad Request");
          }
          break;
        }
      }
    }
    client.stop();
  }
  
  if (Ethernet.linkStatus() == LinkOFF) {
    // reconnect to the network via DHCP  
    while (Ethernet.begin(mac, hostname) == 0) {
      delay(1000);  // delay in ms
    }
  } else {
    // allows for the renewal of DHCP leases
    Ethernet.maintain();
  }

}

void readSensor() {
  // read the values from the sensor
  // see "Table 1. Modbus measurement data registers (read-only)" in "HMP60 and HMP110 Series User Guide"

  int nb = 28;  // number of register values to read
  uint16_t data[nb];

  // request data
  if (!ModbusRTUClient.requestFrom(240, HOLDING_REGISTERS, 0x00, nb)) {
    // there was an error
    sprintf(json, "{\"error\":true}");
  } else {
    // read data
    for (int i=0; i<nb; i++) {
      data[i] = ModbusRTUClient.read();
    }

    // get the register value at the specified register number
    float rh = registerNumber(data, 1);   // relative humidity
    float t = registerNumber(data, 3);    // temperature
    float dp = registerNumber(data, 9);   // dewpoint
    float ah = registerNumber(data, 15);  // absolute humidity
    float mr = registerNumber(data, 17);  // mixing ratio
    float wbt = registerNumber(data, 19); // web-bulb temperature
    float e = registerNumber(data, 27);   // enthalpy

    // jsonify the data
    sprintf(json, 
      "{\"temperature\":%10.6f,"
      "\"relative_humidity\":%10.6f,"
      "\"dewpoint\":%10.6f,"
      "\"absolute_humidity\":%10.6f,"
      "\"mixing_ratio\":%10.6f,"
      "\"wetbulb_temperature\":%10.6f,"
      "\"enthalpy\":%10.6f,"
      "\"error\":false}",
      t, rh, dp, ah, mr, wbt, e);
  }
}

float registerNumber(uint16_t* data, uint8_t index) {
  // convert two uint16 into one float
  u.x = (((unsigned long)data[index] << 16) | data[index-1]);
  return u.f;
}
