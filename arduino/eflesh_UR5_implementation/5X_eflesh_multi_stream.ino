#include <Wire.h>
#include <MLX90393.h>

#ifndef SERIAL_PORT_USBVIRTUAL
#define SERIAL_PORT_USBVIRTUAL Serial
#endif

#define Serial SERIAL_PORT_USBVIRTUAL


static const uint32_t SERIAL_BAUD = 115200;
static const uint32_t I2C_CLOCK_HZ = 400000UL;

//Adafruit PCA9546A default address 0x70.
static const uint8_t MUX_ADDR = 0x70;

// mux channels 0, 1 and 2.
static const uint8_t NUM_MODULES = 3;
static const uint8_t MUX_CHANNELS[NUM_MODULES] = {0, 1, 2};

// Each module  5 MLX90393 sensors.
static const uint8_t NUM_SENSORS = 5;
static const uint16_t MUX_SETTLE_US = 250;
static const uint16_t LOOP_DELAY_US = 0;

const uint8_t TARGETS_ALL_CONSEC[NUM_SENSORS] = {0x0C, 0x0D, 0x0E, 0x0F, 0x10};
const uint8_t TARGETS_WHITE_SET[NUM_SENSORS] = {0x0C, 0x10, 0x11, 0x12, 0x13};



MLX90393 mlx[NUM_MODULES][NUM_SENSORS];
MLX90393::txyz dataBuf[NUM_MODULES][NUM_SENSORS];

uint8_t sensorAddress[NUM_MODULES][NUM_SENSORS];
bool sensorOK[NUM_MODULES][NUM_SENSORS];
uint8_t sensorCount[NUM_MODULES];


bool selectMuxChannel(uint8_t channel);
void disableMuxChannels();

void scanI2C(uint8_t* found, uint8_t& count);
void chooseOrderedAddresses(const uint8_t* found, uint8_t count, uint8_t* ordered, uint8_t& orderedCount);
bool hasExactSet(const uint8_t* found, uint8_t count, const uint8_t* pattern);
void sortAscending(uint8_t* arr, uint8_t n);

void initialiseModule(uint8_t moduleIndex);
void readModule(uint8_t moduleIndex);
void sendModuleAscii(uint8_t moduleIndex);
void zeroModuleData(uint8_t moduleIndex);


void setup() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial) {
    delay(5);
  }

  Wire.begin();
  Wire.setClock(I2C_CLOCK_HZ);
  delay(50);

  Serial.println(F("# stream starting"));
  Serial.print(F("# Baud: "));
  Serial.println(SERIAL_BAUD);
  Serial.print(F("# MUX address: 0x"));
  Serial.println(MUX_ADDR, HEX);

  // Confirm mux exists.
  Wire.beginTransmission(MUX_ADDR);
  uint8_t muxErr = Wire.endTransmission();
  if (muxErr != 0) {
    Serial.print(F("# [ERROR] Mux not found at 0x"));
    Serial.print(MUX_ADDR, HEX);
    Serial.print(F(". I2C error code: "));
    Serial.println(muxErr);
    Serial.println(F("# Check STEMMA QT wiring, mux address jumpers, and power."));
  } else {
    Serial.println(F("# Mux found."));
  }

  // Initialise each module separately by selecting mux channel.
  for (uint8_t moduleIndex = 0; moduleIndex < NUM_MODULES; ++moduleIndex) {
    initialiseModule(moduleIndex);
  }

  Serial.println(F("#streaming M0/M1/M2 packets now."));
}



void loop() {
  for (uint8_t moduleIndex = 0; moduleIndex < NUM_MODULES; ++moduleIndex) {
    readModule(moduleIndex);
    sendModuleAscii(moduleIndex);
  }

  if (LOOP_DELAY_US > 0) {
    delayMicroseconds(LOOP_DELAY_US);
  }
}


bool selectMuxChannel(uint8_t channel) {
  if (channel > 3) {
    return false;
  }

  Wire.beginTransmission(MUX_ADDR);
  Wire.write(1 << channel);
  uint8_t err = Wire.endTransmission();

  delayMicroseconds(MUX_SETTLE_US);

  return (err == 0);
}

void disableMuxChannels() {
  Wire.beginTransmission(MUX_ADDR);
  Wire.write(0x00);
  Wire.endTransmission();
  delayMicroseconds(MUX_SETTLE_US);
}

void initialiseModule(uint8_t moduleIndex) {
  uint8_t channel = MUX_CHANNELS[moduleIndex];

  for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
    sensorAddress[moduleIndex][i] = 0;
    sensorOK[moduleIndex][i] = false;
    dataBuf[moduleIndex][i] = {0, 0, 0, 0};
  }
  sensorCount[moduleIndex] = 0;

  if (!selectMuxChannel(channel)) {
    Serial.print(F("# [ERROR] Could not select mux channel "));
    Serial.println(channel);
    zeroModuleData(moduleIndex);
    return;
  }

  uint8_t found[16] = {0};
  uint8_t foundCount = 0;
  scanI2C(found, foundCount);

  Serial.print(F("# M"));
  Serial.print(moduleIndex);
  Serial.print(F(" found I2C candidates: "));
  for (uint8_t i = 0; i < foundCount; ++i) {
    Serial.print(F("0x"));
    Serial.print(found[i], HEX);
    Serial.print(F(" "));
  }
  Serial.println();

  uint8_t ordered[NUM_SENSORS] = {0};
  uint8_t orderedCount = 0;
  chooseOrderedAddresses(found, foundCount, ordered, orderedCount);

  sensorCount[moduleIndex] = orderedCount;

  if (orderedCount != NUM_SENSORS) {
    Serial.print(F("# [WARN] M"));
    Serial.print(moduleIndex);
    Serial.print(F(" expected 5 MLX90393 sensors but found "));
    Serial.println(orderedCount);
  }

  for (uint8_t i = 0; i < orderedCount; ++i) {
    sensorAddress[moduleIndex][i] = ordered[i];

    byte status = mlx[moduleIndex][i].begin(ordered[i], -1, Wire);

    Serial.print(F("# Init M"));
    Serial.print(moduleIndex);
    Serial.print(F(" MLX["));
    Serial.print(i);
    Serial.print(F("] @0x"));
    Serial.print(ordered[i], HEX);
    Serial.print(F(" status=0x"));
    Serial.println(status, HEX);

    
    mlx[moduleIndex][i].setGainSel(0x1);
    mlx[moduleIndex][i].setResolution(0x2, 0x2, 0x2);
    mlx[moduleIndex][i].setDigitalFiltering(0x4);
    mlx[moduleIndex][i].startBurst(0xF);
    sensorOK[moduleIndex][i] = true;
  }

  for (uint8_t i = orderedCount; i < NUM_SENSORS; ++i) {
    dataBuf[moduleIndex][i] = {0, 0, 0, 0};
    sensorOK[moduleIndex][i] = false;
  }

  Serial.print(F("# M"));
  Serial.print(moduleIndex);
  Serial.print(F(" streaming order: "));
  for (uint8_t i = 0; i < orderedCount; ++i) {
    Serial.print(F("0x"));
    Serial.print(sensorAddress[moduleIndex][i], HEX);
    Serial.print(F(" "));
  }
  Serial.println();
}

void readModule(uint8_t moduleIndex) {
  uint8_t channel = MUX_CHANNELS[moduleIndex];

  if (!selectMuxChannel(channel)) {
    zeroModuleData(moduleIndex);
    return;
  }

  for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
    if (sensorOK[moduleIndex][i]) {
      mlx[moduleIndex][i].readBurstData(dataBuf[moduleIndex][i]);
    } else {
      dataBuf[moduleIndex][i] = {0, 0, 0, 0};
    }
  }
}

void zeroModuleData(uint8_t moduleIndex) {
  for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
    dataBuf[moduleIndex][i] = {0, 0, 0, 0};
  }
}


void sendModuleAscii(uint8_t moduleIndex) {
  Serial.print(F("M"));
  Serial.print(moduleIndex);

  for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
    Serial.print(F(","));
    Serial.print(dataBuf[moduleIndex][i].x, 3);

    Serial.print(F(","));
    Serial.print(dataBuf[moduleIndex][i].y, 3);

    Serial.print(F(","));
    Serial.print(dataBuf[moduleIndex][i].z, 3);
  }

  Serial.println();
}


void scanI2C(uint8_t* found, uint8_t& count) {
  count = 0;

  for (uint8_t addr = 0x08; addr <= 0x77; addr++) {
    if (addr == MUX_ADDR) {
      continue;
    }

    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();

    if (err == 0) {
      found[count++] = addr;
      if (count >= 16) {
        break;
      }
    }
  }
}

void chooseOrderedAddresses(const uint8_t* found, uint8_t count, uint8_t* ordered, uint8_t& orderedCount) {
  orderedCount = 0;

  if (count >= NUM_SENSORS) {
    if (hasExactSet(found, count, TARGETS_ALL_CONSEC)) {
      for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        ordered[i] = TARGETS_ALL_CONSEC[i];
      }
      orderedCount = NUM_SENSORS;
      return;
    }

    if (hasExactSet(found, count, TARGETS_WHITE_SET)) {
      // Custom order for eFlesh boards -  C, 11, 12, 13, 10.
      ordered[0] = 0x0C;
      ordered[1] = 0x11;
      ordered[2] = 0x12;
      ordered[3] = 0x13;
      ordered[4] = 0x10;
      orderedCount = NUM_SENSORS;
      return;
    }
  }

  uint8_t tmp[16];
  uint8_t n = count;
  if (n > 16) {
    n = 16;
  }

  for (uint8_t i = 0; i < n; ++i) {
    tmp[i] = found[i];
  }

  sortAscending(tmp, n);

  orderedCount = (n >= NUM_SENSORS) ? NUM_SENSORS : n;
  for (uint8_t i = 0; i < orderedCount; ++i) {
    ordered[i] = tmp[i];
  }
}

bool hasExactSet(const uint8_t* found, uint8_t count, const uint8_t* pattern) {
  uint8_t hits = 0;

  for (uint8_t p = 0; p < NUM_SENSORS; ++p) {
    bool present = false;

    for (uint8_t i = 0; i < count; ++i) {
      if (found[i] == pattern[p]) {
        present = true;
        break;
      }
    }

    if (present) {
      ++hits;
    }
  }

  return (hits == NUM_SENSORS);
}

void sortAscending(uint8_t* arr, uint8_t n) {
  for (uint8_t i = 0; i < n; ++i) {
    for (uint8_t j = i + 1; j < n; ++j) {
      if (arr[j] < arr[i]) {
        uint8_t t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
      }
    }
  }
}
