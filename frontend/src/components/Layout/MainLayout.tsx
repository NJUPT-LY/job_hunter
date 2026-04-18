import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Drawer, Space } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HomeOutlined,
  SearchOutlined,
  BarChartOutlined,
  CheckSquareOutlined,
  FileTextOutlined,
  VideoCameraOutlined,
  GithubOutlined
} from '@ant-design/icons';

const { Header, Sider, Content, Footer } = Layout;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

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
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        breakpoint="lg"
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
        }}
      >
        <div style={{ 
          height: 32, 
          margin: 16, 
          color: '#fff', 
          fontSize: collapsed ? 16 : 20, 
          fontWeight: 'bold',
          textAlign: 'center',
          lineHeight: '32px'
        }}>
          {collapsed ? '职' : '职路AI'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header style={{ 
          padding: '0 16px', 
          background: '#fff', 
          display: 'flex', 
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '16px', width: 64, height: 64 }}
          />
          <Space>
            <Button 
              type="link" 
              icon={<GithubOutlined />}
              onClick={() => window.open('https://github.com', '_blank')}
            >
              GitHub
            </Button>
          </Space>
        </Header>
        
        <Content style={{ 
          margin: '24px 16px',
          padding: 24,
          minHeight: 280,
          background: '#fff',
          borderRadius: 8
        }}>
          <Outlet />
        </Content>
        
        <Footer style={{ textAlign: 'center' }}>
          职路AI ©2024 帮助大学生跨越求职迷茫 | TRAE「AI 无限职场」SOLO 挑战赛
        </Footer>
      </Layout>

      <Drawer
        title="职路AI"
        placement="left"
        onClose={() => setMobileOpen(false)}
        open={mobileOpen}
        width={250}
      >
        <Menu
          mode="vertical"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Drawer>
    </Layout>
  );
};

export default MainLayout;
