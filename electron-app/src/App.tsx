import { useState, useMemo } from 'react';
import { useLanguage } from './hooks';

type MenuItem = {
  label: string;
  key: string;
};

const App = () => {
  const { t, language, setLanguage } = useLanguage();

  // DEMO
  const asideMenuList = useMemo<MenuItem[]>(
    () => [
      { label: t('aside.name.session-managerment'), key: 'session-managerment' },
      { label: t('aside.name.character-configuration'), key: 'character-configuration' },
      { label: t('aside.name.simulator'), key: 'simulator' },
      { label: t('aside.name.data-analysis'), key: 'data-analysis' },
      { label: t('aside.name.apl-editor'), key: 'apl-editor' },
      { label: t('aside.name.character-support-list'), key: 'character-support-list' },
      { label: t('aside.name.apl-specification'), key: 'apl-specification' },
      { label: t('aside.name.contribution-guide'), key: 'contribution-guide' },
    ],
    [t]
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
  const [activedMenu, setActivedMenu] = useState('session-managerment');

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
        <div className="shrink-0 w-full h-[64px] p-[16px] pb-[24px] flex gap-[4px]">
          <div
            className={`
              px-[10px] h-[32px] rounded-[8px] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80
              ${language === 'zh' ? 'bg-[#FA7319]' : 'bg-[#333]'}
            `}
            onClick={() => setLanguage('zh')}
          >
            中文
          </div>
          <div
            className={`
              px-[10px] h-[32px] rounded-[8px] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80
              ${language === 'en' ? 'bg-[#FA7319]' : 'bg-[#333]'}
            `}
            onClick={() => setLanguage('en')}
          >
            English
          </div>
        </div>
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
          <div>info left</div>
          <div className="px-[10px] h-[32px] rounded-[8px] bg-[#FA7319] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80">
            创建会话
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
