import React from 'react';
import { Breadcrumb } from 'antd';
import type { BreadcrumbProps } from 'antd';
import { useLocation, Link } from 'react-router-dom';
import { HomeOutlined } from '@ant-design/icons';

// 路由到面包屑的映射配置
const breadcrumbNameMap: Record<string, string> = {
  '/': '首页',
  '/jobs': '职位搜索',
  '/analysis': '岗位分析',
  '/action-plan': '行动清单',
  '/resume': '简历优化',
  '/interview': '模拟面试',
};

/**
 * 面包屑导航组件
 * 根据当前路由自动生成面包屑
 */
const AppBreadcrumb: React.FC = () => {
  const location = useLocation();
  const pathSnippets = location.pathname.split('/').filter((i) => i);

  // 构建面包屑项目
  const items: BreadcrumbProps['items'] = [
    {
      title: (
        <Link to="/">
          <HomeOutlined /> 首页
        </Link>
      ),
    },
  ];

  let currentPath = '';
  pathSnippets.forEach((snippet, index) => {
    currentPath += `/${snippet}`;
    const isLast = index === pathSnippets.length - 1;
    const name = breadcrumbNameMap[currentPath];

    if (name) {
      items.push({
        title: isLast ? (
          name
        ) : (
          <Link to={currentPath}>{name}</Link>
        ),
      });
    } else if (snippet.match(/^[a-f0-9-]+$/)) {
      // 可能是职位ID
      items.push({
        title: '职位详情',
      });
    }
  });

  return (
    <Breadcrumb style={{ marginBottom: 16 }} items={items} />
  );
};

export default AppBreadcrumb;
