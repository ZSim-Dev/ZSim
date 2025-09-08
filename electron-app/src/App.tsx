import { useState, useMemo } from 'react';
import { useLanguage } from './hooks/useLanguage';
import { useApiStatus } from './hooks/useApiStatus';
import LanguageSwitch from './components/LanguageSwitch';
import IZsim from '~icons/zsim/zsim';

type MenuItem = {
  label: string;
  key: string;
};

const App = () => {
  const { t } = useLanguage();
  const { apiStatus, apiResponse, testApi } = useApiStatus();

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
  const [activeMenu, setActiveMenu] = useState('session-management');

  return (
    <div className="w-screen h-screen bg-[#F1F1F1] overflow-hidden">
      {/* 侧栏 */}
      <div className="w-[192px] h-full overflow-hidden absolute top-0 left-0 flex flex-col text-[14px]">
        {/* 侧边顶部 */}
        <div className="flex items-center p-4 gap-x-3">
          <div className="size-10 bg-gradient-to-b from-[#494949] to-[#000000] rounded-lg flex items-center justify-center shadow-[0rem_0.5rem_1rem_-0.25rem_#0000004D]">
            <IZsim className="size-7" />
          </div>
          <div className="font-ibm-plex-sans-hebrew text-[1.75rem] leading-9 font-bold tracking-normal bg-gradient-to-br from-[#656565] to-[#262626] bg-clip-text text-transparent">
            ZSim
          </div>
        </div>

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
                  menu.key === activeMenu
                    ? 'border-[#0000001A] bg-white'
                    : 'border-transparent hover:bg-[#38302E0D] active:bg-[#38302E17]'
                }
              `}
              onClick={() => setActiveMenu(menu.key)}
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
          {asideMenuMap.get(activeMenu)}
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
          <div className="px-[10px] h-[32px] rounded-[8px] bg-[#FA7319] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80 mr-[8px]">
            创建会话
          </div>
          <div
            className="px-[10px] h-[32px] rounded-[8px] bg-[#28A745] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80"
            onClick={testApi}
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
