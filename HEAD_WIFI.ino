#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <Adafruit_BME680.h>

// BNO055 객체 생성
Adafruit_BNO055 bno1 = Adafruit_BNO055(55);

// BME680 객체 생성
Adafruit_BME680 bme;

const char *ssid_Router = "KMU-DSP";
const char *password_Router = "kookmin705";
#define REMOTE_IP "192.168.1.25"
#define REMOTE_PORT 8888

WiFiClient client;

const char* slaveID = "01"; // 각 슬레이브에 고유 ID 설정

void setup() {
  Serial.begin(115200);
  delay(10);

  connectToWiFi();
  connectToServer();

  if (!bno1.begin()) {
    Serial.println("Ooops, no BNO055 detected at 0x28 ... Check your wiring or I2C ADDR!");
    while (1);
  }
  Serial.println("BNO1 begin complete");
  
  delay(1000);
  
  bno1.setExtCrystalUse(true);
  
  // Set hardcoded calibration offsets
  adafruit_bno055_offsets_t calibData;
  calibData.accel_offset_x = -2;
  calibData.accel_offset_y = -49;
  calibData.accel_offset_z = -36;
  calibData.gyro_offset_x = 0;
  calibData.gyro_offset_y = 0;
  calibData.gyro_offset_z = 1;
  calibData.mag_offset_x = 87;
  calibData.mag_offset_y = 934;
  calibData.mag_offset_z = 76;
  calibData.accel_radius = 1000;
  calibData.mag_radius = 565;

  bno1.setMode(OPERATION_MODE_CONFIG);
  delay(25);

  bno1.setSensorOffsets(calibData);
  Serial.println("Sensor offsets set successfully");

  bno1.setMode(OPERATION_MODE_NDOF);
  delay(20);

    // BME680 센서 초기화
  if (!bme.begin()) {
    Serial.println("Could not find a valid BME680 sensor, check wiring!");
    while(1);
  }
  Serial.println("BME begin complete");
    // BME680 센서 구성 (온도, 압력, 습도, 고도 등)
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320, 150); // 320°C for 150 ms

  // 슬레이브 ID 전송
  client.print(slaveID);

  if (!client.connected()) {
    Serial.println("Client disconnected. Reconnecting...");
    connectToServer();
  }
}

bool flag = false;
int numbering = 0;
void loop() {
  // Check client connection
  if (!client.connected()) {
    Serial.println("Client disconnected.");
    // connectToServer();
  }

  if (client.available()) {
    String message = client.readStringUntil('\n');
    Serial.println(message);
    if(message.startsWith("START")){
      Serial.println("Operation started");
      flag = true;
    }
  }

  if (flag) {
    // 새로운 쿼터니안 데이터를 수집
    sensors_event_t event1; 
    bno1.getEvent(&event1);
    imu::Quaternion quat1 = bno1.getQuat();
    numbering += 1;

    // 슬레이브 ID가 1인 경우 고도 값 추가
    String quat_data;
    if (String(slaveID) == "1") {
      if (!bme.performReading()) {
        Serial.println("Failed to perform reading from BME680 sensor");
        return;
      }
      // 고도 계산 (압력 기반)
      float altitude = bme.readAltitude(1013.25); // 해수면 기준 압력 설정
      quat_data = String(altitude, 2) + "," + String(quat1.w(), 4) + "," + String(quat1.x(), 4) + "," + String(quat1.y(), 4) + "," + String(quat1.z(), 4) + "!!!";
    } else {
      quat_data = String(quat1.w(), 4) + "," + String(quat1.x(), 4) + "," + String(quat1.y(), 4) + "," + String(quat1.z(), 4) + "!!!";
    }
    Serial.print(quat_data);
    // 쿼터니안 값을 지속적으로 전송
    if (quat_data != "") {
      client.print(quat_data);
      Serial.print(numbering);
      Serial.print(" Sent: ");
      Serial.println(quat_data);
      delay(20); // 데이터 전송 간격 조절 (필요에 따라 조정)
      numbering++;
    }
  }  
}

void connectToWiFi() {
  WiFi.begin(ssid_Router, password_Router);
  Serial.print("\nWaiting for WiFi... ");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void connectToServer() {
  Serial.print("Connecting to ");
  Serial.println(REMOTE_IP);

  while (!client.connect(REMOTE_IP, REMOTE_PORT)) {
    Serial.println("Connection failed.");
    Serial.println("Waiting a moment before retrying...");
    delay(1000);
  }
  Serial.println("Connected");
  
  // 서버 연결 시 초기 메시지를 슬레이브 ID로 전송
  client.print(String(slaveID) + "\n");
}

// #include <WiFi.h>
// #include <vector>
// #include <Wire.h>
// #include <Adafruit_Sensor.h>
// #include <Adafruit_BNO055.h>
// #include <Adafruit_Sensor.h>
// #include "Adafruit_BME680.h"
// #include <utility/imumaths.h>
// #define SEALEVELPRESSURE_HPA (1013.25)
// Adafruit_BNO055 bno1 = Adafruit_BNO055(55);
// Adafruit_BME680 bme;

// int  SLAVEID = 1;

// const char *ssid = "KMU-DSP";
// const char *password = "kookmin705";

// WiFiClient client;

// std::vector<String> qq;

// #define SerialDebug   false  // Set to true to get Serial output for debugging
// #define I2Cclock      400000

// float test_var = 0;

// void setup() {
//   Serial.begin(115200);
//   delay(1000);

//   WiFi.begin(ssid, password);


//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.println("Connecting to WiFi...");
//   }

//   Serial.println("Connected to WiFi");

//   while (!client.connect("192.168.1.9", 8888)) {
//     delay(100);
//     Serial.println("Connecting to Server...");
//   }
//   Serial.println("Connected to Server");
//   client.print(SLAVEID);

//   if (!bno1.begin()) {
//     Serial.println("Ooops, no BNO055 detected at 0x28 ... Check your wiring or I2C ADDR!");
//     while (1);
//   }
//   Serial.println("BNO1 begin complete");

//   delay(1000);

//   bno1.setExtCrystalUse(true);

//   // Set hardcoded calibration offsets
//   adafruit_bno055_offsets_t calibData;
//   calibData.accel_offset_x = -2; // Replace these values with your specific offsets
//   calibData.accel_offset_y = -49;
//   calibData.accel_offset_z = -36;
//   calibData.gyro_offset_x = 0;
//   calibData.gyro_offset_y = 0;
//   calibData.gyro_offset_z = 1;
//   calibData.mag_offset_x = 87;
//   calibData.mag_offset_y = 934;
//   calibData.mag_offset_z = 76;
//   calibData.accel_radius = 1000;
//   calibData.mag_radius = 565;

//   bno1.setMode(OPERATION_MODE_CONFIG);
//   delay(25);

//   bno1.setSensorOffsets(calibData);
//   Serial.println("Sensor offsets set successfully");

//   bno1.setMode(OPERATION_MODE_NDOF);
//   delay(20);

//   if (!bme.begin()) {
//     Serial.println("Could not find a valid BME680 sensor, check wiring!");
//     while (1);
//   }
//   bme.setTemperatureOversampling(BME680_OS_8X);
//   bme.setHumidityOversampling(BME680_OS_2X);
//   bme.setPressureOversampling(BME680_OS_4X);
//   bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
//   bme.setGasHeater(320, 150);

// }

// bool golf_operate = false;
// int past;
// float altitude = -1;
// int now;

// void loop() {
//   past = millis();

//   if (client.connected()) {

//     while (client.available()) {      // Process data received from the client
//       if (! bme.performReading()) {
//         Serial.println("Failed to perform reading :(");
//         return;
//       }
      
//       String command = client.readStringUntil('\n');
//       if (command.startsWith("START")) {
//         Serial.println("Operation started");
//         golf_operate = true;
//         qq.clear();  // Clear the quaternion vector
//       }
//       if (command.startsWith("STOP")) { // Handle stop signal
//         golf_operate = false;
//         Serial.println("Operation stopped");
        
//         Serial.println("Send Signal");
//         client.write("Slave ID : ");
//         client.print(SLAVEID); client.write("  ");

//         String dataToSend;
//         for (int i = 0; i < qq.size(); i++) {
//           dataToSend += qq[i] + ",";
//         }
//         // Remove the trailing ","
//         if (dataToSend.length() > 0) {
//           dataToSend = dataToSend.substring(0, dataToSend.length() - 1);
//         }
//         client.print(dataToSend);
//         client.println("END!!!");
//         qq.clear();
//       }
//     }

//     if (golf_operate) {
//       bno_operate();

//       now = millis();
//       while (now - past <= 20) {
//         now = millis();
//       }
//       Serial.print("\t"); Serial.println(now - past);
//     }
//   } else {
//     Serial.println("Disconnected from server");
//     while (!client.connect("192.168.1.9", 8888)) {
//       delay(1000);
//       Serial.println("Reconnecting to Server...");
//     }
//     Serial.println("Reconnected to Server");
//   }
// }

// void bno_operate() {
//   sensors_event_t event1;
//   bno1.getEvent(&event1);
//   imu::Quaternion quat1 = bno1.getQuat();
//   altitude = bme.readAltitude(SEALEVELPRESSURE_HPA);
//   // Print data from the first sensor with 8 decimal places of precision
//   Serial.print(quat1.w(), 8);
//   Serial.print(",");
//   Serial.print(quat1.x(), 8);
//   Serial.print(",");
//   Serial.print(quat1.y(), 8);
//   Serial.print(",");
//   Serial.println(quat1.z(), 8);

//   // Store quaternion values as strings with 8 decimal places of precision
//   qq.push_back(String(quat1.w(), 8));
//   qq.push_back(String(quat1.x(), 8));
//   qq.push_back(String(quat1.y(), 8));
//   qq.push_back(String(quat1.z(), 8));
//   qq.push_back(String(altitude, 4));

//   delay(100); // Adjust delay as needed
// }
