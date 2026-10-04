import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Drawer, Space, Typography } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HomeOutlined,
  SearchOutlined,
  BarChartOutlined,
  CheckSquareOutlined,
  FileTextOutlined,
  VideoCameraOutlined,
  GithubOutlined,
  MenuOutlined
} from '@ant-design/icons';
import AppBreadcrumb from '../Breadcrumb/AppBreadcrumb';
import RouteLoadingIndicator from '../Loading/RouteLoadingIndicator';

const { Header, Sider, Content, Footer } = Layout;
const { Text } = Typography;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // 监听屏幕尺寸变化
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setCollapsed(true);
      }
    };

    // 初始化检测
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/jobs', icon: <SearchOutlined />, label: '职位搜索' },
    { key: '/analysis', icon: <BarChartOutlined />, label: '岗位分析' },
    { key: '/action-plan', icon: <CheckSquareOutlined />, label: '行动清单' },
    { key: '/resume', icon: <FileTextOutlined />, label: '简历优化' },
    { key: '/interview', icon: <VideoCameraOutlined />, label: '模拟面试' },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    setMobileOpen(false);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          breakpoint="lg"
          collapsedWidth={80}
          width={200}
          onBreakpoint={(broken) => {
            if (broken) setCollapsed(true);
          }}
          style={{
            overflow: 'auto',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            bottom: 0,
            zIndex: 10,
          }}
        >
          <div style={{ 
            height: 32, 
            margin: 16, 
            color: '#fff', 
            fontSize: collapsed ? 16 : 20, 
            fontWeight: 'bold',
            textAlign: 'center',
            lineHeight: '32px',
            whiteSpace: 'nowrap',
            overflow: 'hidden'
          }}>
            {collapsed ? '职' : '职路AI'}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[location.pathname.startsWith('/jobs/') ? '/jobs' : location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Sider>
      )}
      
      <Layout style={{ 
        marginLeft: isMobile ? 0 : (collapsed ? 80 : 200), 
        transition: 'margin-left 0.2s ease',
        minHeight: '100vh'
      }}>
        <Header style={{ 
          padding: isMobile ? '0 12px' : '0 16px', 
          background: '#fff', 
          display: 'flex', 
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          position: 'sticky',
          top: 0,
          zIndex: 9,
          height: 64,
          lineHeight: '64px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {isMobile ? (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setMobileOpen(true)}
                style={{ fontSize: '18px', width: 40, height: 40 }}
              />
            ) : (
              <Button
                type="text"
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={() => setCollapsed(!collapsed)}
                style={{ fontSize: '16px', width: 48, height: 48 }}
              />
            )}
            {!collapsed && !isMobile && <Text strong>职路AI</Text>}
          </div>
          <Space size="small">
            <Button 
              type="text" 
              icon={<GithubOutlined />}
              onClick={() => window.open('https://github.com/NJUPT-LY/job_hunter', '_blank', 'noopener,noreferrer')}
              style={{ fontSize: isMobile ? 14 : 16 }}
            >
              {!isMobile && 'GitHub'}
            </Button>
          </Space>
        </Header>
        
        <Content style={{ 
          margin: isMobile ? '12px 8px' : '24px 16px',
          padding: isMobile ? 12 : 24,
          minHeight: 280,
          background: '#fff',
          borderRadius: 8,
          overflow: 'auto'
        }}>
          <RouteLoadingIndicator />
          <AppBreadcrumb />
          <Outlet />
        </Content>
        
        <Footer style={{ 
          textAlign: 'center',
          padding: isMobile ? '12px 8px' : '24px 50px',
          fontSize: isMobile ? 12 : 14
        }}>
          职路AI ©{new Date().getFullYear()} 帮助大学生跨越求职迷茫
        </Footer>
      </Layout>

      {/* 移动端抽屉菜单 */}
      <Drawer
        title="职路AI"
        placement="left"
        onClose={() => setMobileOpen(false)}
        open={mobileOpen}
        width={250}
        destroyOnClose
      >
        <Menu
          mode="inline"
          selectedKeys={[location.pathname.startsWith('/jobs/') ? '/jobs' : location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 'none' }}
        />
      </Drawer>
    </Layout>
  );
};

export default MainLayout;
