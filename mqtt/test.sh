# 發送紅色
mosquitto_pub -h test.mosquitto.org -p 1883 -t river/wheel/color -m '{"hex":"#FF0000","rgb":[255,0,0]}'

# 發送綠色
mosquitto_pub -h test.mosquitto.org -p 1883 -t river/wheel/color -m '{"hex":"#00FF00","rgb":[0,255,0]}'

# 發送藍色
mosquitto_pub -h test.mosquitto.org -p 1883 -t river/wheel/color -m '{"hex":"#0000FF","rgb":[0,0,255]}'

# 發送完整結果（模擬你的 Python 腳本）
mosquitto_pub -h test.mosquitto.org -p 1883 -t river/wheel/result -m '{"led_position":{"position":10},"color":"#FF5733","sentiment":"happy","rgb":[255,87,51]}'

# 發送 LED 位置
mosquitto_pub -h test.mosquitto.org -p 1883 -t river/wheel/led_position -m '{"position":25}'

# 發送情緒
mosquitto_pub -h test.mosquitto.org -p 1883 -t river/wheel/sentiment -m '{"name":"joy","category":"positive"}'

#!/bin/bash
# MQTT 監聽腳本

# 監聽所有 river/wheel topics
mosquitto_sub -h test.mosquitto.org -p 1883 -t 'river/wheel/#' -v
