-- Địa chỉ công khai qua Cloudflare Tunnel (robot ở bất kỳ đâu đều kết nối được)
UPDATE sys_params SET param_value = 'wss://xiaozhi-ws.minizjp.com/xiaozhi/v1/' WHERE param_code = 'server.websocket';
UPDATE sys_params SET param_value = 'https://xiaozhi.minizjp.com/xiaozhi/ota/' WHERE param_code = 'server.ota';
UPDATE sys_params SET param_value = 'https://xiaozhi.minizjp.com' WHERE param_code = 'server.fronted_url';
SELECT param_code, param_value FROM sys_params WHERE param_code IN ('server.websocket','server.ota','server.fronted_url');
