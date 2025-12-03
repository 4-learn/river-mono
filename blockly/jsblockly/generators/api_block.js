// Blockly v10+ 使用新的 API
// 需要使用 javascriptGenerator 而不是 Blockly.JavaScript
const javascriptGenerator = Blockly.JavaScript || window.Blockly.JavaScript;

// 積木 A: 呼叫 API (statement block)
javascriptGenerator.forBlock['call_api'] = function(block, generator) {
  var text = generator.valueToCode(block, 'TEXT', generator.ORDER_ATOMIC) || "''";
  var x = generator.valueToCode(block, 'X', generator.ORDER_ATOMIC) || '0';
  var y = generator.valueToCode(block, 'Y', generator.ORDER_ATOMIC) || '0';

  var code = 'fetch("https://river.4impact.cc/wheel", {\n' +
    '  method: "POST",\n' +
    '  headers: { "Content-Type": "application/json" },\n' +
    '  body: JSON.stringify({\n' +
    '    text: ' + text + ',\n' +
    '    position: [' + x + ', ' + y + ']\n' +
    '  })\n' +
    '})\n' +
    '.then(res => res.json())\n' +
    '.then(data => {\n' +
    '  console.log("API 回傳:", data);\n' +
    '  window.apiResponse = data;\n' +
    '})\n' +
    '.catch(error => {\n' +
    '  console.error("API 錯誤:", error);\n' +
    '});\n';

  return code;
};

// 積木 B: 取得 API 回應物件 (value block - 回傳整個 object)
javascriptGenerator.forBlock['get_api_response'] = function(block, generator) {
  var code = 'window.apiResponse || {}';
  return [code, generator.ORDER_MEMBER];
};

// 積木 C: 從 API 回應取得欄位 (value block - 回傳特定欄位的值)
javascriptGenerator.forBlock['get_api_field'] = function(block, generator) {
  var field = block.getFieldValue('FIELD');

  // 處理巢狀屬性，例如 "led_position.row"
  var accessPath = field.split('.').map(function(part) {
    return '["' + part + '"]';
  }).join('');

  // 使用 !== undefined 來正確處理 0、false、空字串等 falsy 值
  var code = '(window.apiResponse' + accessPath + ' !== undefined ? window.apiResponse' + accessPath + ' : null)';
  return [code, generator.ORDER_CONDITIONAL];
};

// 積木 D: 呼叫 API 並執行 (statement block with callback)
javascriptGenerator.forBlock['call_api_and_do'] = function(block, generator) {
  var text = generator.valueToCode(block, 'TEXT', generator.ORDER_ATOMIC) || "''";
  var x = generator.valueToCode(block, 'X', generator.ORDER_ATOMIC) || '0';
  var y = generator.valueToCode(block, 'Y', generator.ORDER_ATOMIC) || '0';
  var statements = generator.statementToCode(block, 'DO');

  var code = 'fetch("https://river.4impact.cc/wheel", {\n' +
    '  method: "POST",\n' +
    '  headers: { "Content-Type": "application/json" },\n' +
    '  body: JSON.stringify({\n' +
    '    text: ' + text + ',\n' +
    '    position: [' + x + ', ' + y + ']\n' +
    '  })\n' +
    '})\n' +
    '.then(res => res.json())\n' +
    '.then(data => {\n' +
    '  console.log("API 回傳:", data);\n' +
    '  window.apiResponse = data;\n' +
    statements +
    '})\n' +
    '.catch(error => {\n' +
    '  console.error("API 錯誤:", error);\n' +
    '});\n';

  return code;
};

