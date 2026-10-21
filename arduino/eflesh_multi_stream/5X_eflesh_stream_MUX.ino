/*
  eFlesh Board Code
  By: Venkatesh P
  Date: August 1, 2025
  License: This code is public domain but you buy me a beer if you use this and we meet someday (Beerware license).

  Credits: Adapted from (ReSkin (https://reskin.dev) and AnySkin (https://any-skin.github.io) repos) - maintained by Raunaq Bhirangi, Tess Hellebrekers
  Library: Heavily based on original MLX90393 library from Theodore Yapo (https://github.com/tedyapo/arduino-MLX90393)
  Library: https://github.com/tesshellebrekers/arduino-MLX90393  (required)
*/

#include <Wire.h>
#include <MLX90393.h>

#define Serial SERIAL_PORT_USBVIRTUAL  // use default Serial if your board doesn't define this

// MLX90393 objects and data buffers
static const uint8_t NUM_SENSORS = 5;

// Added multiplexer/module settings and expanded MLX/data arrays from 1 module to multiple modules.
static const uint8_t NUM_MODULES = 3;
static const uint8_t MUX_ADDR = 0x70;
const uint8_t MUX_CHANNELS[NUM_MODULES] = {0, 1, 2};

MLX90393 mlx[NUM_MODULES][NUM_SENSORS];
MLX90393::txyz dataBuf[NUM_MODULES][NUM_SENSORS];
uint8_t orderedAddr[NUM_MODULES][NUM_SENSORS];
uint8_t orderedCount[NUM_MODULES] = {0};


// Known sequences
const uint8_t TARGETS_ALL_CONSEC[NUM_SENSORS] = {0x0C, 0x0D, 0x0E, 0x0F, 0x10};
const uint8_t TARGETS_WHITE_SET[NUM_SENSORS]   = {0x0C, 0x10, 0x11, 0x12, 0x13};

// Forward decls

// Added mux channel
void selectMux(uint8_t channel);
void scanI2C(uint8_t* found, uint8_t& count);
void chooseOrderedAddresses(const uint8_t* found, uint8_t count, uint8_t* ordered, uint8_t& orderedCount);
bool hasExactSet(const uint8_t* found, uint8_t count, const uint8_t* pattern);
void sortAscending(uint8_t* arr, uint8_t n);

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(5); }

  Wire.begin();
  Wire.setClock(400000);
  delay(10);

  // Repeat I2C scan per MUX channel
  for (uint8_t m = 0; m < NUM_MODULES; ++m) {
    selectMux(MUX_CHANNELS[m]);
    delay(10);

    uint8_t found[16] = {0};
    uint8_t foundCount = 0;
    scanI2C(found, foundCount);

    Serial.print(F("MUX channel "));
    Serial.print(MUX_CHANNELS[m]);
    Serial.println(F(" I2C scan complete."));

    Serial.print(F("Found MLX candidates: "));
    for (uint8_t i = 0; i < foundCount; ++i) {
      Serial.print("0x"); Serial.print(found[i], HEX); Serial.print(" ");
    }
    Serial.println();

    chooseOrderedAddresses(found, foundCount, orderedAddr[m], orderedCount[m]);


    // Initialize sensors in the chosen order
    for (uint8_t i = 0; i < orderedCount[m]; ++i) {
      byte status = mlx[m][i].begin(orderedAddr[m][i], -1, Wire);
      Serial.print(F("Init MUX["));
      Serial.print(MUX_CHANNELS[m]);
      Serial.print(F("] MLX["));
      Serial.print(i);
      Serial.print(F("] @0x"));
      Serial.print(orderedAddr[m][i], HEX);
      Serial.print(F(" status=")); Serial.println(status, HEX);

      // Configs
      mlx[m][i].setGainSel(0x1);
      mlx[m][i].setResolution(0x2, 0x2, 0x2);
      mlx[m][i].setDigitalFiltering(0x4);

      // Start burst mode (Temp + X + Y + Z) = 0xF
      mlx[m][i].startBurst(0xF);
    }

  
    for (uint8_t i = orderedCount[m]; i < NUM_SENSORS; ++i) {
      dataBuf[m][i] = {0, 0, 0, 0};
    }

    Serial.print(F("Streaming order: "));
    for (uint8_t i = 0; i < orderedCount[m]; ++i) {
      Serial.print("0x"); Serial.print(orderedAddr[m][i], HEX); Serial.print(" ");
    }
    Serial.println();
  }

}

void loop() {
  // Read each module by selecting its mux channel before reading its 5 sensors
  // Read in the same order
  for (uint8_t m = 0; m < NUM_MODULES; ++m) {
    selectMux(MUX_CHANNELS[m]);

    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
      mlx[m][i].readBurstData(dataBuf[m][i]);  // if that index wasn't initialized (no device), the buffer remains whatever it was
    }
  }
  for (uint8_t m = 0; m < NUM_MODULES; ++m) {
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
      Serial.write((uint8_t*)&dataBuf[m][i], sizeof(dataBuf[m][i]));
    }
  }

  Serial.println();

  // adjust for desired sample rate
  delayMicroseconds(500);
}

// Added helper function to select the active I2C multiplexer channel
void selectMux(uint8_t channel) {
  if (channel > 7) return;

  Wire.beginTransmission(MUX_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}


// Scan all I2C addresses to find MLX90393 sensors
void scanI2C(uint8_t* found, uint8_t& count) {
  count = 0;
  for (uint8_t addr = 0x08; addr <= 0x77; addr++) {
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();
    if (err == 0) {
      found[count++] = addr;
      if (count >= 16) break;
    }
  }
}

void chooseOrderedAddresses(const uint8_t* found, uint8_t count, uint8_t* ordered, uint8_t& orderedCount) {
  orderedCount = 0;

 
  if (count >= NUM_SENSORS) {
    if (hasExactSet(found, count, TARGETS_ALL_CONSEC)) {
      for (uint8_t i = 0; i < NUM_SENSORS; ++i) ordered[i] = TARGETS_ALL_CONSEC[i];
      orderedCount = NUM_SENSORS;
      return;
    }
    if (hasExactSet(found, count, TARGETS_WHITE_SET)) {
      // custom order: C,11,12,13,10
      ordered[0] = 0x0C; ordered[1] = 0x11; ordered[2] = 0x12; ordered[3] = 0x13; ordered[4] = 0x10;
      orderedCount = NUM_SENSORS;
      return;
    }
  }

  uint8_t tmp[16];
  uint8_t n = count;
  if (n > 16) n = 16;
  for (uint8_t i = 0; i < n; ++i) tmp[i] = found[i];
  sortAscending(tmp, n);

  orderedCount = (n >= NUM_SENSORS) ? NUM_SENSORS : n;
  for (uint8_t i = 0; i < orderedCount; ++i) ordered[i] = tmp[i];
}

bool hasExactSet(const uint8_t* found, uint8_t count, const uint8_t* pattern) {
  uint8_t hits = 0;
  for (uint8_t p = 0; p < NUM_SENSORS; ++p) {
    bool present = false;
    for (uint8_t i = 0; i < count; ++i) {
      if (found[i] == pattern[p]) { present = true; break; }
    }
    if (present) ++hits;
  }
  return (hits == NUM_SENSORS);
}

void sortAscending(uint8_t* arr, uint8_t n) {
  for (uint8_t i = 0; i < n; ++i) {
    for (uint8_t j = i + 1; j < n; ++j) {
      if (arr[j] < arr[i]) {
        uint8_t t = arr[i]; arr[i] = arr[j]; arr[j] = t;
      }
    }
  }
}
