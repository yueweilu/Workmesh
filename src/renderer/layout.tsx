/**
 * @license
 * Copyright 2025 AionUi (aionui.com)
 * SPDX-License-Identifier: Apache-2.0
 */

import { ipcBridge } from '@/common';
import { ConfigStorage } from '@/common/storage';
import PwaPullToRefresh from '@/renderer/components/PwaPullToRefresh';
import Titlebar from '@/renderer/components/Titlebar';
import { Layout as ArcoLayout } from '@arco-design/web-react';
import { MenuFold, MenuUnfold } from '@icon-park/react';
import classNames from 'classnames';
import React, { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { LayoutContext } from './context/LayoutContext';
import { useDirectorySelection } from './hooks/useDirectorySelection';
import { useMultiAgentDetection } from './hooks/useMultiAgentDetection';
import { processCustomCss } from './utils/customCssProcessor';

const useDebug = () => {
  const [count, setCount] = useState(0);
  const timer = useRef<any>(null);
  const onClick = () => {
    const open = () => {
      ipcBridge.application.openDevTools.invoke().catch((error) => {
        console.error('Failed to open dev tools:', error);
      });
      setCount(0);
    };
    if (count >= 3) {
      return open();
    }
    setCount((prev) => {
      if (prev >= 2) {
        open();
        return 0;
      }
      return prev + 1;
    });
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      clearTimeout(timer.current);
      setCount(0);
    }, 1000);
  };

  return { onClick };
};

const DEFAULT_SIDER_WIDTH = 250;

const Layout: React.FC<{
  sider: React.ReactNode;
  onSessionClick?: () => void;
}> = ({ sider, onSessionClick: _onSessionClick }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [customCss, setCustomCss] = useState<string>('');
  const { onClick } = useDebug();
  const { contextHolder: multiAgentContextHolder } = useMultiAgentDetection();
  const { contextHolder: directorySelectionContextHolder } = useDirectorySelection();
  const location = useLocation();
  const workspaceAvailable = location.pathname.startsWith('/conversation/');
  const collapsedRef = useRef(collapsed);

  // 加载并监听自定义 CSS 配置 / Load & watch custom CSS configuration
  useEffect(() => {
    const loadCustomCss = () => {
      ConfigStorage.get('customCss')
        .then((css) => setCustomCss(css || ''))
        .catch((error) => {
          console.error('Failed to load custom CSS:', error);
        });
    };

    loadCustomCss();

    const handleCssUpdate = (event: CustomEvent) => {
      if (event.detail?.customCss !== undefined) {
        setCustomCss(event.detail.customCss || '');
      }
    };
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key && event.key.includes('customCss')) {
        loadCustomCss();
      }
    };

    window.addEventListener('custom-css-updated', handleCssUpdate as EventListener);
    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('custom-css-updated', handleCssUpdate as EventListener);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  // 注入自定义 CSS / Inject custom CSS into document head
  useEffect(() => {
    const styleId = 'user-defined-custom-css';

    if (!customCss) {
      document.getElementById(styleId)?.remove();
      return;
    }

    const wrappedCss = processCustomCss(customCss);

    const ensureStyleAtEnd = () => {
      let styleEl = document.getElementById(styleId) as HTMLStyleElement | null;

      if (styleEl && styleEl.textContent === wrappedCss && styleEl === document.head.lastElementChild) {
        return;
      }

      styleEl?.remove();
      styleEl = document.createElement('style');
      styleEl.id = styleId;
      styleEl.type = 'text/css';
      styleEl.textContent = wrappedCss;
      document.head.appendChild(styleEl);
    };

    ensureStyleAtEnd();

    const observer = new MutationObserver((mutations) => {
      const hasNewStyle = mutations.some((mutation) => Array.from(mutation.addedNodes).some((node) => node.nodeName === 'STYLE' || node.nodeName === 'LINK'));

      if (hasNewStyle) {
        const element = document.getElementById(styleId);
        if (element && element !== document.head.lastElementChild) {
          ensureStyleAtEnd();
        }
      }
    });

    observer.observe(document.head, { childList: true });

    return () => {
      observer.disconnect();
      document.getElementById(styleId)?.remove();
    };
  }, [customCss]);

  // 检测移动端并响应窗口大小变化
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
    };

    // 初始检测
    checkMobile();

    // 监听窗口大小变化
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 进入移动端后立即折叠 / Collapse immediately when switching to mobile
  useEffect(() => {
    if (!isMobile || collapsedRef.current) {
      return;
    }
    setCollapsed(true);
  }, [isMobile]);
  useEffect(() => {
    collapsedRef.current = collapsed;
  }, [collapsed]);
  return (
    <LayoutContext.Provider value={{ isMobile, siderCollapsed: collapsed, setSiderCollapsed: setCollapsed }}>
      <div className='app-shell flex flex-col size-full min-h-0'>
        <Titlebar workspaceAvailable={workspaceAvailable} />
        {/* 移动端左侧边栏蒙板 / Mobile left sider backdrop */}
        {isMobile && !collapsed && <div className='fixed inset-0 bg-black/30 z-90' onClick={() => setCollapsed(true)} aria-hidden='true' />}

        <ArcoLayout className={'size-full layout flex-1 min-h-0'}>
          <ArcoLayout.Sider
            collapsedWidth={isMobile ? 0 : 64}
            collapsed={collapsed}
            width={DEFAULT_SIDER_WIDTH}
            className={classNames('!bg-2 layout-sider', {
              collapsed: collapsed,
            })}
            style={
              isMobile
                ? {
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    height: '100vh',
                    zIndex: 100,
                    transform: collapsed ? 'translateX(-100%)' : 'translateX(0)',
                    transition: 'none',
                    pointerEvents: collapsed ? 'none' : 'auto',
                  }
                : undefined
            }
          >
            <ArcoLayout.Header
              className={classNames('flex items-center justify-start py-10px px-16px pl-20px gap-12px layout-sider-header', {
                'cursor-pointer group ': collapsed,
              })}
            >
              <div
                className={classNames('bg-black shrink-0 size-40px relative rd-0.5rem', {
                  '!size-24px': collapsed,
                })}
                onClick={onClick}
              >
                <svg
                  className={classNames('w-5.5 h-5.5 absolute inset-0 m-auto', {
                    ' scale-140': !collapsed,
                  })}
                  viewBox='0 0 80 80'
                  fill='none'
                >
                  <path
                    d='M36.1152758,17.665252 C35.7009807,17.0602083 34.9202012,16.9747774 34.3460575,17.440129 C34.1095633,17.6318007 33.875255,17.8484354 33.7098719,18.0983388 C32.9807164,19.2000405 32.2600719,20.3080399 31.571146,21.4342482 C31.2124282,22.0206724 30.9459828,22.6580721 30.8128298,23.3374571 C30.5574068,24.6409161 30.0930335,26.7738276 31.429296,29.5036733 C32.04246,30.5510223 32.6645071,31.5933514 33.282415,32.6380079 C34.4950697,34.6881195 35.7100964,36.736862 36.9191699,38.7889816 C37.9887189,40.6042954 39.0524079,42.4228949 40.1171665,44.2409468 C41.7373725,47.0074999 43.3539974,49.776061 44.9764823,52.5413363 C45.8689746,54.0624796 46.7710941,55.5781922 47.6672605,57.0972819 C48.0862529,57.8076081 48.4978504,58.5220873 48.9190286,59.2311358 C49.3170458,59.9011197 50.0017394,60.1842918 50.620996,59.8749246 C50.8952084,59.7379706 51.1460736,59.4879302 51.3157355,59.2308619 C51.7398437,58.588214 52.1185134,57.9160852 52.5026246,57.2487025 C53.2445699,55.9595277 53.9824224,54.668071 54.7124151,53.3723702 C55.0576919,52.759477 55.2751642,52.106059 55.2681293,51.2491038 C55.2500033,50.8417558 55.1496851,50.3079957 54.867892,49.8189134 L54.0330698,48.3706053 C52.5282041,45.7656041 51.0274777,43.1582298 49.5167519,40.5564687 C48.2247543,38.3314795 46.9187576,36.114294 45.6233183,33.8912215 C43.8933064,30.9223635 42.1702708,27.9496264 40.4389102,24.9815441 C39.3654545,23.1413131 38.2831158,21.306102 37.2025444,19.4698869 L36.6740136,18.5577291 C36.4962825,18.2546197 36.3135169,17.9547904 36.1152758,17.665252 Z M16.164364,25.361144 L15.581106,25.3617824 C14.9279139,25.3647727 14.385731,25.3753249 14.1177831,25.3903114 C13.1463664,25.4446641 12.5881285,26.4248367 12.9874944,27.29708 C13.0855337,27.5112503 13.2097106,27.7145136 13.3298878,27.9182333 C14.5711915,30.0227431 15.8187739,32.123739 17.0553338,34.2309414 C18.3690973,36.4697127 19.6743498,38.7133215 20.980672,40.9562914 C22.9057393,44.2616246 24.8312716,47.5666839 26.751316,50.8748466 C28.3455704,53.6217305 29.9301512,56.3739995 31.5262659,59.1198338 C31.6434201,59.3213173 31.799083,59.5112549 31.97214,59.6693384 C32.3824818,60.0441935 32.9234186,60.0922483 33.3514336,59.7670453 C33.578161,59.594769 33.7800531,59.3640784 33.9262284,59.1210204 C34.9997771,57.3357352 36.0595128,55.5424637 37.1163185,53.7475493 C37.4063437,53.254953 37.7114374,52.7651405 37.9396531,52.2444779 C38.3556224,51.2956116 38.1614507,50.3865857 37.6433494,49.5202751 C36.9690271,48.392789 36.2967046,47.2641164 35.6316374,46.1313822 C34.6572907,44.4718702 33.6898272,42.8084335 32.7200848,41.1463202 C31.3694403,38.8313822 30.0163308,36.5178588 28.6702441,34.2003652 C27.7574278,32.628794 26.8795856,31.0371885 25.9418873,29.4801752 C24.5692444,27.2010159 22.4848866,25.9070949 19.8508484,25.4971456 C19.2350637,25.4013098 17.5709671,25.364316 16.164364,25.361144 Z M65.8737292,25.3648374 C63.5888745,25.4153566 61.30202,25.3801711 59.0160026,25.3801711 L59.0160026,25.3676668 C56.7454725,25.3676668 54.4748959,25.3616428 52.2044123,25.3738277 C51.8443458,25.3757444 51.4751638,25.4235254 51.1264918,25.5119226 C49.2763028,25.980925 48.2543782,27.7224908 48.8655424,29.4301033 C49.0914792,30.0613878 49.4414534,30.6555245 49.7802656,31.2413098 C51.3851704,34.0162599 53.0101668,36.7800293 54.6178156,39.5535191 C55.0347615,40.2727444 55.4069201,41.0167957 55.814611,41.7413605 C56.0807309,42.214242 56.4828407,42.4973685 57.0589378,42.4659252 C57.5235081,42.4405515 57.8526466,42.1822967 58.0997447,41.8217257 C58.3544236,41.4501564 58.5938943,41.0680907 58.8290397,40.6841084 C60.0406712,38.7057368 61.2544421,36.7285517 62.456493,34.7445212 C63.5198563,32.9894472 64.5696393,31.2265237 65.6237476,29.4660646 C66.0743655,28.7134336 66.5119611,27.9531358 66.9716016,27.2058442 C67.4206848,26.4756206 66.9630906,25.3407415 65.8737292,25.3648374 Z'
                    fill='white'
                  />
                </svg>
              </div>
              <div className=' flex-1 text-20px collapsed-hidden font-bold'>Workmesh</div>
              {isMobile && !collapsed && (
                <button type='button' className='app-titlebar__button' onClick={() => setCollapsed(true)} aria-label='Collapse sidebar'>
                  {collapsed ? <MenuUnfold theme='outline' size='18' fill='currentColor' /> : <MenuFold theme='outline' size='18' fill='currentColor' />}
                </button>
              )}
              {/* 侧栏折叠改由标题栏统一控制 / Sidebar folding handled by Titlebar toggle */}
            </ArcoLayout.Header>
            <ArcoLayout.Content className='h-[calc(100%-72px-16px)] p-8px layout-sider-content'>
              {React.isValidElement(sider)
                ? React.cloneElement(sider, {
                    onSessionClick: () => {
                      if (isMobile) setCollapsed(true);
                    },
                    collapsed,
                  } as any)
                : sider}
            </ArcoLayout.Content>
          </ArcoLayout.Sider>

          <ArcoLayout.Content
            className={'bg-1 layout-content flex flex-col min-h-0'}
            onClick={() => {
              if (isMobile && !collapsed) setCollapsed(true);
            }}
            style={
              isMobile
                ? {
                    width: '100vw',
                  }
                : undefined
            }
          >
            <Outlet />
            {multiAgentContextHolder}
            {directorySelectionContextHolder}
            <PwaPullToRefresh />
          </ArcoLayout.Content>
        </ArcoLayout>
      </div>
    </LayoutContext.Provider>
  );
};

export default Layout;
