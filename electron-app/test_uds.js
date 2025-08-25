const { ipcRenderer } = require('electron');

async function testElectronUDS() {
    console.log('测试Electron应用中的UDS功能');
    console.log('==========================================');
    
    try {
        // 获取IPC配置
        console.log('获取IPC配置...');
        const config = await ipcRenderer.invoke('get-ipc-config');
        console.log('IPC配置:', config);
        
        // 测试健康检查
        console.log('\n测试健康检查...');
        const healthResponse = await window.apiClient.get('/health');
        console.log('健康检查响应:', healthResponse);
        
        // 测试API端点
        console.log('\n测试API端点...');
        const sessionsResponse = await window.apiClient.get('/api/sessions/');
        console.log('会话列表响应:', sessionsResponse);
        
        console.log('\n==========================================');
        console.log('✓ 所有Electron UDS测试通过!');
        console.log('==========================================');
        
    } catch (error) {
        console.error('\n==========================================');
        console.error('✗ Electron UDS测试失败:', error);
        console.error('==========================================');
    }
}

// 在开发控制台中运行此函数
if (typeof window !== 'undefined' && window.apiClient) {
    window.testElectronUDS = testElectronUDS;
    console.log('UDS测试函数已加载，运行 testElectronUDS() 开始测试');
}

module.exports = { testElectronUDS };