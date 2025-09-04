import { useState, useMemo, useEffect } from 'react';
import { useLanguage } from './hooks';
import LanguageSwitch from './components/LanguageSwitch';

type MenuItem = {
  label: string;
  key: string;
};

const App = () => {
  const { t } = useLanguage();
  const [apiStatus, setApiStatus] = useState<string>('初始化中...');
  const [apiResponse, setApiResponse] = useState<unknown>(null);

  // 检查 apiClient 是否可用
  useEffect(() => {
    const checkApiClient = async () => {
      console.log('[App] Checking window.apiClient...');

      // 等待preload脚本加载，最多等待10秒
      const maxAttempts = 50;
      let attempts = 0;

      const checkInterval = setInterval(() => {
        attempts++;
        console.log(`[App] Attempt ${attempts}: window.apiClient =`, typeof window.apiClient);

        if (typeof window !== 'undefined' && window.apiClient) {
          clearInterval(checkInterval);
          console.log('[App] window.apiClient is available:', window.apiClient);
          setApiStatus('API 客户端已就绪');

          // 测试IPC配置获取
          (async () => {
            try {
              if (window.electron && window.electron.ipcRenderer) {
                console.log('[App] Testing IPC config retrieval...');
                const config = await window.electron.ipcRenderer.invoke('get-ipc-config');
                console.log('[App] IPC Config:', config);
              } else {
                console.log('[App] window.electron.ipcRenderer not available');
              }
            } catch (error) {
              console.error('[App] IPC config error:', error);
            }
          })();
        } else if (attempts >= maxAttempts) {
          clearInterval(checkInterval);
          console.error('[App] window.apiClient not available after maximum attempts');
          setApiStatus('API 客户端加载超时');
        } else {
          console.log('[App] window.apiClient not available yet, waiting...');
        }
      }, 200);
    };

    checkApiClient();
  }, []);

  // 测试 API 连接
  useEffect(() => {
    const testApi = async () => {
      if (!window.apiClient) {
        setApiStatus('API 客户端未加载');
        return;
      }

      try {
        const response = await window.apiClient.get('/health');
        setApiStatus(`API 连接成功 (${response.status})`);
        setApiResponse(JSON.parse(response.body));
      } catch (error) {
        setApiStatus(`API 连接失败: ${error}`);
        console.error('API test failed:', error);
      }
    };

    // 延迟测试 API，确保客户端已完全加载
    setTimeout(testApi, 1000);
  }, []);

  // DEMO
  const asideMenuList = useMemo<MenuItem[]>(
    () => [
      { label: t('aside.name.session-management'), key: 'session-management' },
      { label: t('aside.name.character-configuration'), key: 'character-configuration' },
      { label: t('aside.name.simulator'), key: 'simulator' },
      { label: t('aside.name.data-analysis'), key: 'data-analysis' },
      { label: t('aside.name.apl-editor'), key: 'apl-editor' },
      { label: t('aside.name.character-support-list'), key: 'character-support-list' },
      { label: t('aside.name.apl-specification'), key: 'apl-specification' },
      { label: t('aside.name.contribution-guide'), key: 'contribution-guide' },
    ],
    [t],
  );

  // DEMO
  const asideMenuMap = useMemo<Map<string, string>>(() => {
    const map = new Map<string, string>();
    asideMenuList.forEach(item => {
      map.set(item.key, item.label);
    });
    return map;
  }, [asideMenuList]);

  // DEMO
  const [activedMenu, setActivedMenu] = useState('session-management');

  return (
    <div className="w-screen h-screen bg-[#F1F1F1] overflow-hidden">
      {/* 侧栏 */}
      <div className="w-[192px] h-full overflow-hidden absolute top-0 left-0 flex flex-col text-[14px]">
        {/* 侧边顶部 */}
        <div className="shrink-0 w-full h-[72px] p-[16px] text-[28px] font-[700]">ZSim</div>

        {/* 侧边列表 */}
        <div className="flex-1 w-full overflow-auto flex flex-col">
          {asideMenuList.map(menu => (
            <div
              key={menu.key}
              className={`
                shrink-0 h-[40px] my-[1px] mx-[8px] px-[10px] overflow-hidden
                rounded-[8px] border border-solid
                flex items-center gap-[8px] text-[#6B6B6B]
                select-none cursor-pointer
                ${
                  menu.key === activedMenu
                    ? 'border-[#0000001A] bg-white'
                    : 'border-transparent hover:bg-[#38302E0D] active:bg-[#38302E17]'
                }
              `}
              onClick={() => setActivedMenu(menu.key)}
            >
              <div className="w-[16px] h-[16px] rounded-sm bg-[#6B6B6B40]" />
              <div>{menu.label}</div>
            </div>
          ))}
        </div>

        {/* 侧边底部 */}
        <LanguageSwitch className="shrink-0 w-full h-[64px] p-[16px] pb-[24px]" />
      </div>

      {/* 模块 */}
      <div
        className={`
          w-[calc(100%-192px-16px)] h-[calc(100%-32px)] m-[16px] ml-0
          absolute left-[192px] overflow-hidden
          flex flex-col
          bg-[#FFF] rounded-[8px] border border-solid border-[#E6E6E6]
        `}
      >
        {/* 模块.1 */}
        <div className="w-full shrink-0 p-[24px] pb-0 text-[24px] font-[400]">
          {asideMenuMap.get(activedMenu)}
        </div>

        {/* 模块.2 */}
        <div className="w-[calc(100%-48px)] shrink-0 mx-[24px] h-[56px] flex items-center justify-between">
          <div className="text-[14px] text-[#666]">
            <span className="mr-[16px]">API 状态: {apiStatus}</span>
            {apiResponse && typeof apiResponse === 'object' && 'message' in apiResponse ? (
              <span className="text-[12px] text-[#999]">
                后端: {(apiResponse as { message?: string }).message || '未知'}
              </span>
            ) : null}
          </div>
          <div
            className="px-[10px] h-[32px] rounded-[8px] bg-[#FA7319] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80 mr-[8px]"
            onClick={() => {
              const testApi = async () => {
                if (!window.apiClient) {
                  setApiStatus('API 客户端未加载');
                  return;
                }

                try {
                  const response = await window.apiClient.get('/health');
                  setApiStatus(`API 连接成功 (${response.status})`);
                  setApiResponse(JSON.parse(response.body));
                } catch (error) {
                  setApiStatus(
                    `API 连接失败: ${error instanceof Error ? error.message : String(error)}`,
                  );
                  console.error('API test failed:', error);
                }
              };
              testApi();
            }}
          >
            创建会话
          </div>
          <div
            className="px-[10px] h-[32px] rounded-[8px] bg-[#28A745] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80"
            onClick={() => {
              const testApi = async () => {
                if (!window.apiClient) {
                  setApiStatus('API 客户端未加载');
                  return;
                }

                try {
                  const response = await window.apiClient.get('/health');
                  setApiStatus(`API 连接成功 (${response.status})`);
                  setApiResponse(JSON.parse(response.body));
                } catch (error) {
                  setApiStatus(
                    `API 连接失败: ${error instanceof Error ? error.message : String(error)}`,
                  );
                  console.error('API test failed:', error);
                }
              };
              testApi();
            }}
          >
            重新测试API
          </div>
        </div>

        {/* 模块.3 */}
        <div className="w-full flex-1 overflow-auto flex gap-[16px]">
          <div className="shrink-0 w-[248px] h-[767px] ml-[24px] my-[16px] bg-[#F1F1F1] rounded-[12px] border border-solid border-[#E6E6E6]" />
          <div className="shrink-0 w-[248px] h-[522px] my-[16px] bg-[#F1F1F1] rounded-[12px] border border-solid border-[#E6E6E6]" />
          <div className="shrink-0 w-[248px] h-[277px] my-[16px] bg-[#F1F1F1] rounded-[12px] border border-solid border-[#E6E6E6]" />
          <div className="shrink-0 w-[248px] h-[522px] mr-[24px] my-[16px] bg-[#F1F1F1] rounded-[12px] border border-solid border-[#E6E6E6]" />
        </div>
      </div>
    </div>
  );
};

export default App;
