#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

Adafruit_BNO055 bno1 = Adafruit_BNO055(55);

// const char *ssid_Router = "eightbit";
// const char *password_Router = "12345678q";
// #define REMOTE_IP "192.168.1.37"
// #define REMOTE_PORT 8888
const char *ssid_Router = "ESP-MASTER";
const char *password_Router = "123456789";
#define REMOTE_IP "192.168.0.4"
#define REMOTE_PORT 8889

WiFiClient client;

const char* slaveID = "13"; // 각 슬레이브에 고유 ID 설정

void setup() {
  Serial.begin(115200);
  delay(10);

  Wire.begin(5, 6); //D5 D6 GPIO8,9

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
  // Serial.print("flag:");
  // Serial.println(flag);

  if (flag) {
    // 새로운 쿼터니안 데이터를 수집
    sensors_event_t event1; 
    bno1.getEvent(&event1);
    imu::Quaternion quat1 = bno1.getQuat();
    numbering+=1;
    String quat_data = String(quat1.w(), 4) + "," + String(quat1.x(), 4) + "," + String(quat1.y(), 4) + "," + String(quat1.z(), 4) + "!!!";
    
    // Serial.print("Prepared: ");
    // Serial.println(quat_data);

    // 쿼터니안 값을 지속적으로 전송
    if (quat_data != "") {
      
      client.print(quat_data);
      Serial.print(numbering);
      Serial.print("Sent: ");
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
