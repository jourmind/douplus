# 导出功能问题排查指南

## 问题：点击导出按钮没有反应

### 快速排查步骤

#### 1. 打开浏览器开发者工具
- 按 `F12` 或 `Ctrl+Shift+I`
- 切换到 **Console** 标签

#### 2. 刷新页面并点击导出按钮
观察Console中是否有以下错误信息：

**常见错误类型：**

##### A. Token相关错误
```
Error: Token不存在
```
**解决方案：** 重新登录系统

##### B. 网络请求错误
```
GET http://xxx/api/douplus/task/export 401 (Unauthorized)
```
**解决方案：** Token过期，重新登录

```
GET http://xxx/api/douplus/task/export 500 (Internal Server Error)
```
**解决方案：** 检查后端日志

##### C. CORS跨域错误
```
Access-Control-Allow-Origin
```
**解决方案：** 检查后端CORS配置

##### D. 函数未定义错误
```
exportTaskData is not defined
```
**解决方案：** 前端代码未正确导入

#### 3. 切换到 **Network** 标签
- 刷新页面
- 点击导出按钮
- 查看是否有请求发出

**如果没有任何请求：**
- 检查按钮的事件绑定
- 检查控制台是否有JavaScript错误
- 确认前端代码已部署

**如果有请求但失败：**
- 查看请求的Status Code
- 查看响应的Response内容
- 查看请求的Headers（特别是Authorization）

#### 4. 使用调试脚本测试

复制以下代码到浏览器Console执行：

```javascript
// 简单测试
(async () => {
    const token = localStorage.getItem('token');
    console.log('Token:', token ? '存在' : '不存在');
    
    if (!token) {
        console.error('请先登录！');
        return;
    }
    
    const url = '/api/douplus/task/export';
    console.log('请求URL:', url);
    
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        console.log('状态码:', response.status);
        
        if (response.ok) {
            const blob = await response.blob();
            console.log('✓ 导出成功！文件大小:', blob.size, '字节');
            
            // 下载文件
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '测试导出.xlsx';
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            const text = await response.text();
            console.error('✗ 导出失败:', text);
        }
    } catch (error) {
        console.error('✗ 请求异常:', error);
    }
})();
```

### 详细调试方法

#### 方法1：使用完整调试脚本

文件位置：`/opt/douplus/debug_export_frontend.js`

将该文件内容复制到浏览器Console执行，会显示详细的调试信息。

#### 方法2：检查后端日志

```bash
# 查看最新日志
tail -f /opt/douplus/douplus-sync-python/logs/api_server.log

# 过滤导出相关日志
tail -100 /opt/douplus/douplus-sync-python/logs/api_server.log | grep export
```

#### 方法3：使用Python脚本测试后端API

```bash
cd /opt/douplus
python3 test_frontend_export.py
```

这会模拟前端调用，验证后端API是否正常工作。

### 常见问题及解决方案

#### 问题1：点击按钮完全没反应

**可能原因：**
1. 前端代码未部署
2. 事件绑定错误
3. JavaScript错误

**解决步骤：**
```bash
# 重新构建前端
cd /opt/douplus/douplus-web
npm run build

# 重启Nginx（如果使用）
sudo nginx -s reload
```

#### 问题2：显示"正在导出..."但没有下载

**可能原因：**
1. 后端返回错误但前端未正确处理
2. 文件下载被浏览器拦截
3. Blob转换失败

**解决步骤：**
1. 查看浏览器Console错误
2. 查看Network标签中的响应内容
3. 检查浏览器下载设置（是否拦截弹窗）

#### 问题3：导出失败显示401错误

**原因：** Token无效或过期

**解决：** 重新登录系统

#### 问题4：导出失败显示500错误

**原因：** 后端处理异常

**解决步骤：**
```bash
# 查看后端错误日志
tail -50 /opt/douplus/douplus-sync-python/logs/api_server.log

# 常见后端错误：
# 1. 数据库连接失败
# 2. openpyxl库未安装
# 3. SQL查询错误
```

#### 问题5：下载的文件无法打开

**可能原因：**
1. 文件内容不完整
2. 文件类型错误
3. Excel格式问题

**解决：**
使用Python测试脚本验证导出文件是否正常

### 检查清单

- [ ] 用户已登录（localStorage中有token）
- [ ] 前端代码已构建并部署
- [ ] 后端服务正在运行
- [ ] openpyxl库已安装
- [ ] 数据库连接正常
- [ ] 浏览器Console无错误
- [ ] Network标签显示请求成功（200）
- [ ] 浏览器允许文件下载

### 获取支持

如果以上方法都无法解决问题，请提供以下信息：

1. **浏览器Console的错误信息**（截图或文本）
2. **Network标签的请求详情**（Headers、Response）
3. **后端日志的错误信息**
4. **Python测试脚本的输出结果**

执行诊断脚本获取完整信息：
```bash
cd /opt/douplus
python3 test_frontend_export.py > export_diagnostic.log 2>&1
cat export_diagnostic.log
```
