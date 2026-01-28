/**
 * 前端导出功能调试脚本
 * 
 * 使用方法：
 * 1. 在浏览器打开投放记录或历史记录页面
 * 2. 按F12打开开发者工具
 * 3. 切换到Console标签
 * 4. 复制粘贴下面的代码并回车执行
 * 
 * 这个脚本会：
 * 1. 检查token是否存在
 * 2. 检查环境变量配置
 * 3. 模拟导出API调用
 * 4. 显示详细的请求和响应信息
 */

(async function debugExport() {
    console.log('='.repeat(60));
    console.log('前端导出功能调试');
    console.log('='.repeat(60));
    
    // 1. 检查token
    console.log('\n1. 检查Token:');
    const token = localStorage.getItem('token');
    if (!token) {
        console.error('✗ Token不存在！请先登录');
        return;
    }
    console.log(`✓ Token存在: ${token.substring(0, 30)}...`);
    
    // 2. 检查环境变量
    console.log('\n2. 检查环境配置:');
    const baseURL = import.meta.env?.VITE_API_BASE_URL || '';
    console.log(`  VITE_API_BASE_URL: ${baseURL || '(空，使用相对路径)'}`);
    
    // 3. 构建导出URL
    console.log('\n3. 构建导出请求:');
    const exportURL = `${baseURL}/api/douplus/task/export`;
    console.log(`  导出URL: ${exportURL}`);
    
    // 4. 发送请求
    console.log('\n4. 发送导出请求...');
    try {
        const response = await fetch(exportURL, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log(`  状态码: ${response.status}`);
        console.log(`  Content-Type: ${response.headers.get('Content-Type')}`);
        console.log(`  Content-Disposition: ${response.headers.get('Content-Disposition')}`);
        
        if (!response.ok) {
            const text = await response.text();
            console.error(`✗ 请求失败: ${text}`);
            return;
        }
        
        // 5. 下载文件
        console.log('\n5. 下载文件...');
        const blob = await response.blob();
        console.log(`  文件大小: ${blob.size.toLocaleString()} 字节`);
        
        // 获取文件名
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = '订单数据.xlsx';
        if (contentDisposition) {
            const matches = /filename\*=UTF-8''(.+)/.exec(contentDisposition) ||
                          /filename="(.+)"/.exec(contentDisposition);
            if (matches && matches[1]) {
                filename = decodeURIComponent(matches[1]);
            }
        }
        console.log(`  文件名: ${filename}`);
        
        // 触发下载
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        console.log('\n✓ 导出成功！请检查浏览器下载');
        
    } catch (error) {
        console.error(`✗ 导出失败: ${error.message}`);
        console.error(error);
    }
    
    console.log('\n' + '='.repeat(60));
})();
