// 積木 A: 呼叫 API
Blockly.Blocks['call_api'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("呼叫 API");
    this.appendValueInput("TEXT")
        .setCheck("String")
        .appendField("文字");
    this.appendValueInput("X")
        .setCheck("Number")
        .appendField("位置 X");
    this.appendValueInput("Y")
        .setCheck("Number")
        .appendField("位置 Y");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(230);
    this.setTooltip("呼叫 API 並將回應存到全域變數");
  }
};

// 積木 B: 取得 API 回應物件
Blockly.Blocks['get_api_response'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("取得 API 回應");
    this.setOutput(true, null);
    this.setColour(230);
    this.setTooltip("取得完整的 API 回應物件");
  }
};

// 積木 C: 從 API 回應取得欄位
Blockly.Blocks['get_api_field'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("從 API 回應取得")
        .appendField(new Blockly.FieldDropdown([
          ["LED 列", "led_position.row"],
          ["LED 欄", "led_position.col"],
          ["顏色", "color"],
          ["情緒", "sentiment"],
          ["文字", "text"]
        ]), "FIELD");
    this.setOutput(true, null);
    this.setColour(230);
    this.setTooltip("從 API 回應中取得特定欄位的值");
  }
};

// 積木 D: 呼叫 API 並執行 (statement block with callback)
Blockly.Blocks['call_api_and_do'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("呼叫 API 並執行");
    this.appendValueInput("TEXT")
        .setCheck("String")
        .appendField("文字");
    this.appendValueInput("X")
        .setCheck("Number")
        .appendField("位置 X");
    this.appendValueInput("Y")
        .setCheck("Number")
        .appendField("位置 Y");
    this.appendStatementInput("DO")
        .appendField("執行");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(230);
    this.setTooltip("呼叫 API，等待回應後執行內部程式碼");
  }
};
