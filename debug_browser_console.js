// ========================================
// 在投放记录页面的浏览器Console中执行此代码
// ========================================

// 1. 检查Vue实例
console.log('========== 检查Vue实例 ==========');
const app = document.querySelector('#app').__vueParentComponent;
console.log('App实例:', app);

// 2. 直接调用API测试
console.log('\n========== 测试API调用 ==========');
fetch('/api/account/list', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  }
})
.then(res => res.json())
.then(data => {
  console.log('API响应:', data);
  console.log('code:', data.code);
  console.log('success:', data.success);
  console.log('data类型:', typeof data.data);
  console.log('data是否为数组:', Array.isArray(data.data));
  console.log('data长度:', data.data ? data.data.length : 'null');
  console.log('data内容:', data.data);
  
  // 3. 模拟前端处理逻辑
  console.log('\n========== 模拟前端处理逻辑 ==========');
  if (data.code === 200) {
    const members = (data.data || []).map((account) => ({
      id: account.id,
      nickname: account.remark || account.nickname || `账号${account.id}`
    }));
    console.log('处理后的members数组:', members);
    console.log('members.length:', members.length);
  }
})
.catch(err => {
  console.error('API调用失败:', err);
});

// 4. 检查当前页面的members变量（需要Vue Devtools）
console.log('\n========== 提示 ==========');
console.log('请安装Vue Devtools查看组件状态中的members变量');
console.log('或者刷新页面并观察Network标签中的account/list请求');
