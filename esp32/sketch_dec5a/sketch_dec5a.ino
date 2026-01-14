#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

const char* ssid = "yillkid";
const char* password = "2ulidgoo";

const char* mqtt_server = "test.mosquitto.org";
const int mqtt_port = 1883;
char mqtt_client_id[32];
const char* mqtt_topic_prefix = "river/wheel";

#define LED_PIN   5
#define LED_COUNT 60

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
WiFiClient espClient;
PubSubClient client(espClient);

struct LEDState {
  uint8_t r = 0;
  uint8_t g = 0;
  uint8_t b = 0;
  int position = 0;
  bool hasNewData = false;
} ledState;

struct BreathingState {
  uint8_t currentR = 255;
  uint8_t currentG = 255;
  uint8_t currentB = 255;
  int brightness = 0;
  bool fadeIn = true;
  unsigned long lastUpdate = 0;
  int updateInterval = 3;
} breathState;

String lastColorMsg = "";
String lastPosMsg = "";
String lastResultMsg = "";
unsigned long lastReconnectAttempt = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  uint8_t mac[6];
  WiFi.macAddress(mac);
  snprintf(mqtt_client_id, sizeof(mqtt_client_id), "river-esp32-%02X%02X%02X", 
           mac[3], mac[4], mac[5]);
  Serial.print("MQTT Client ID: ");
  Serial.println(mqtt_client_id);
  
  strip.begin();
  strip.setBrightness(0);
  strip.show();
  
  setup_wifi();
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqtt_callback);
  client.setKeepAlive(60);
  client.setBufferSize(512);
  
  randomSeed(analogRead(0));
  Serial.println("Starting with white breathing...");
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  String topicStr = String(topic);
  
  if (topicStr.endsWith("/color")) {
    if (message == lastColorMsg) return;
    lastColorMsg = message;
  }
  else if (topicStr.endsWith("/led_position")) {
    if (message == lastPosMsg) return;
    lastPosMsg = message;
  }
  else if (topicStr.endsWith("/result")) {
    if (message == lastResultMsg) return;
    lastResultMsg = message;
  }
  
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (topicStr.endsWith("/color")) {
    JsonArray rgb = doc["rgb"];
    if (rgb.size() == 3) {
      ledState.r = rgb[0];
      ledState.g = rgb[1];
      ledState.b = rgb[2];
      ledState.hasNewData = true;
      Serial.printf("✓ Color updated: R%d G%d B%d\n", ledState.r, ledState.g, ledState.b);
    }
  }
  else if (topicStr.endsWith("/led_position")) {
    if (doc.containsKey("row") && doc.containsKey("col")) {
      int row = doc["row"];
      int col = doc["col"];
      ledState.position = row * 10 + col;
      Serial.printf("✓ Position: row=%d, col=%d\n", row, col);
    } else if (doc.containsKey("position")) {
      ledState.position = doc["position"];
      Serial.printf("✓ Position: %d\n", ledState.position);
    }
  }
  else if (topicStr.endsWith("/result")) {
    JsonArray rgb = doc["rgb"];
    if (rgb.size() == 3) {
      ledState.r = rgb[0];
      ledState.g = rgb[1];
      ledState.b = rgb[2];
      ledState.hasNewData = true;
    }
    
    JsonObject led_pos = doc["led_position"];
    if (led_pos.containsKey("row") && led_pos.containsKey("col")) {
      int row = led_pos["row"];
      int col = led_pos["col"];
      ledState.position = row * 10 + col;
    }
    
    String sentiment = doc["sentiment"] | "unknown";
    Serial.printf("✓ Full update - %s, RGB: %d,%d,%d\n", 
                  sentiment.c_str(), ledState.r, ledState.g, ledState.b);
  }
  else if (topicStr.endsWith("/sentiment")) {
    String sentiment = doc["name"] | "unknown";
    String category = doc["category"] | "unknown";
    Serial.printf("✓ Sentiment: %s (%s)\n", sentiment.c_str(), category.c_str());
  }
}

void reconnect() {
  unsigned long now = millis();
  if (now - lastReconnectAttempt < 5000) return;
  lastReconnectAttempt = now;
  
  if (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (client.connect(mqtt_client_id)) {
      Serial.println("connected");
      
      String baseTopic = String(mqtt_topic_prefix);
      client.subscribe((baseTopic + "/led_position").c_str());
      client.subscribe((baseTopic + "/color").c_str());
      client.subscribe((baseTopic + "/sentiment").c_str());
      client.subscribe((baseTopic + "/result").c_str());
      
      Serial.println("Subscribed");
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
    }
  }
}

void updateBreathing() {
  unsigned long now = millis();
  
  if (now - breathState.lastUpdate < breathState.updateInterval) {
    return;
  }
  breathState.lastUpdate = now;
  
  if (ledState.hasNewData) {
    uint8_t r = ledState.r;
    uint8_t g = ledState.g;
    uint8_t b = ledState.b;
    
    // 計算最小值
    uint8_t minVal = min(r, min(g, b));
    
    // 如果是淡色（最小值很高），降低亮度加強對比
    if (minVal > 100) {
      float factor = 0.5;  // 降低到 50%
      breathState.currentR = r * factor;
      breathState.currentG = g * factor;
      breathState.currentB = b * factor;
      
      Serial.printf("⚡ Enhanced pale color: (%d,%d,%d) -> (%d,%d,%d)\n", 
                    r, g, b,
                    breathState.currentR, breathState.currentG, breathState.currentB);
    } else {
      breathState.currentR = r;
      breathState.currentG = g;
      breathState.currentB = b;
      Serial.printf("⚡ Vivid color: (%d,%d,%d)\n", r, g, b);
    }
    
    ledState.hasNewData = false;
    breathState.brightness = 0;
    breathState.fadeIn = true;
  }
  
  if (breathState.fadeIn) {
    breathState.brightness++;
    if (breathState.brightness >= 255) {
      breathState.brightness = 255;
      breathState.fadeIn = false;
    }
  } else {
    breathState.brightness--;
    if (breathState.brightness <= 0) {
      breathState.brightness = 0;
      breathState.fadeIn = true;
    }
  }
  
  strip.setBrightness(breathState.brightness);
  for (int i = 0; i < LED_COUNT; i++) {
    strip.setPixelColor(i, strip.Color(
      breathState.currentR, 
      breathState.currentG, 
      breathState.currentB
    ));
  }
  strip.show();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ WiFi disconnected!");
    setup_wifi();
  }
  
  if (!client.connected()) {
    reconnect();
  }
  
  client.loop();
  updateBreathing();
  
  delay(1);
}