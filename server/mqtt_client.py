import os
import ssl
import json
import logging
import threading
import paho.mqtt.client as mqtt
from typing import Any

logger = logging.getLogger("uvicorn")

class MQTTClient:
    def __init__(self):
        self.client = None
        self.connected = threading.Event()
        self.queue = []  # 暫存未送出的訊息 (topic, msg, qos, retain)

        # 從環境變數讀取設定
        self.host = os.getenv("MQTT_HOST", "test.mosquitto.org").strip()
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.tls = os.getenv("MQTT_TLS", "false").lower() == "true"
        self.username = os.getenv("MQTT_USERNAME", "").strip()
        self.password = os.getenv("MQTT_PASSWORD", "").strip()
        self.client_id = os.getenv("MQTT_CLIENT_ID", "river-server").strip()
        self.topic_prefix = os.getenv("MQTT_TOPIC_PREFIX", "river/wheel").strip().rstrip("/")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected.set()
            logger.info(f"[MQTT] Connected to {self.host}:{self.port}")
            self._flush_queue()
        else:
            logger.error(f"[MQTT] Connect failed with code {rc}")

    def _flush_queue(self):
        """發送暫存的訊息"""
        if not self.client or not self.connected.is_set():
            return
        while self.queue:
            topic, msg, qos, retain = self.queue.pop(0)
            result = self.client.publish(topic, msg, qos=qos, retain=retain)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.warning(f"[MQTT] Flush failed for {topic}")
            else:
                logger.info(f"[MQTT] Published (flushed) {topic}")

    def connect(self):
        """初始化 MQTT 連接"""
        try:
            # 使用 paho-mqtt 1.x 相容的參數
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.on_connect = self._on_connect

            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            if self.tls:
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                self.client.tls_insecure_set(True)

            self.client.loop_start()
            self.client.connect(self.host, self.port, keepalive=60)

            # 等待連接（最多 5 秒）
            if not self.connected.wait(timeout=5):
                logger.warning("[MQTT] Connection timeout, will retry later")

            logger.info(f"[MQTT] Initialized: {self.host}:{self.port} (TLS={self.tls})")
        except Exception as e:
            logger.error(f"[MQTT] Initialization failed: {e}")

    def publish(self, topic_suffix: str, payload: Any, qos: int = 1, retain: bool = True):
        """
        發布訊息到 MQTT

        Args:
            topic_suffix: topic 後綴，例如 "led_position"
            payload: 可以是 dict 或 str
            qos: QoS 等級 (0, 1, 2)
            retain: 是否保留訊息
        """
        try:
            topic = f"{self.topic_prefix}/{topic_suffix.lstrip('/')}"
            msg = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)

            if not self.client or not self.connected.is_set():
                self.queue.append((topic, msg, qos, retain))
                logger.warning(f"[MQTT] Not connected, queued: {topic}")
                return

            result = self.client.publish(topic, msg, qos=qos, retain=retain)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.warning(f"[MQTT] Publish failed for {topic}")
            else:
                logger.info(f"[MQTT] Published: {topic} -> {msg[:100]}")
        except Exception as e:
            logger.error(f"[MQTT] Publish error: {e}")

    def disconnect(self):
        """斷開連接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("[MQTT] Disconnected")

# 全域實例
mqtt_client = MQTTClient()
