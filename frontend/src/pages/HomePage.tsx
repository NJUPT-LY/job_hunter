import { Card, Row, Col, Typography, Space, Button, Statistic } from 'antd';
import { 
  RocketOutlined, 
  AimOutlined, 
  BulbOutlined, 
  TrophyOutlined,
  ArrowRightOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph, Text } = Typography;

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <RocketOutlined style={{ fontSize: 40, color: '#1677ff' }} />,
      title: '职位搜索',
      description: '爬取主流招聘网站，获取最新岗位信息',
      path: '/jobs'
    },
    {
      icon: <AimOutlined style={{ fontSize: 40, color: '#52c41a' }} />,
      title: '岗位分析',
      description: 'AI智能解析JD，把招聘描述翻译为真实工作内容与能力要求',
      path: '/analysis'
    },
    {
      icon: <BulbOutlined style={{ fontSize: 40, color: '#faad14' }} />,
      title: '行动清单',
      description: '根据目标岗位生成个性化阶段性学习路径',
      path: '/action-plan'
    },
    {
      icon: <TrophyOutlined style={{ fontSize: 40, color: '#722ed1' }} />,
      title: '简历与面试',
      description: 'AI简历优化与模拟面试，提升求职竞争力',
      path: '/resume'
    }
  ];

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title level={1}>职路AI - 大学生求职导航平台</Title>
        <Paragraph style={{ fontSize: 18, color: '#666', maxWidth: 800, margin: '0 auto' }}>
          帮助大学生跨越求职迷茫，让信息不对称与经验缺乏不再成为障碍
        </Paragraph>
        <Space style={{ marginTop: 24 }}>
          <Button type="primary" size="large" icon={<ArrowRightOutlined />} onClick={() => navigate('/jobs')}>
            开始探索
          </Button>
          <Button size="large" onClick={() => navigate('/analysis')}>
            岗位分析
          </Button>
        </Space>
      </div>

      <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="已收录职位" value={1200} suffix="+" />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="岗位类别" value={50} suffix="+" />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="技能标签" value={200} suffix="+" />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="AI分析模型" value={5} suffix="个" />
          </Card>
        </Col>
      </Row>

      <Title level={2} style={{ textAlign: 'center', marginBottom: 32 }}>核心功能</Title>
      
      <Row gutter={[24, 24]}>
        {features.map((feature, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card 
              hoverable 
              style={{ height: '100%', textAlign: 'center' }}
              onClick={() => navigate(feature.path)}
            >
              <div style={{ marginBottom: 16 }}>{feature.icon}</div>
              <Title level={4}>{feature.title}</Title>
              <Paragraph type="secondary">{feature.description}</Paragraph>
              <Button type="link" onClick={(e) => { e.stopPropagation(); navigate(feature.path); }}>
                立即使用 <ArrowRightOutlined />
              </Button>
            </Card>
          </Col>
        ))}
      </Row>

      <Card style={{ marginTop: 48, background: '#f6ffed', borderColor: '#b7eb8f' }}>
        <Title level={3} style={{ textAlign: 'center' }}>
          <BulbOutlined /> 为什么选择职路AI？
        </Title>
        <Row gutter={[24, 16]} style={{ marginTop: 24 }}>
          <Col xs={24} md={8}>
            <Space direction="vertical">
              <Text strong>真实数据驱动</Text>
              <Text type="secondary">不是空泛建议，而是基于真实招聘需求</Text>
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Space direction="vertical">
              <Text strong>AI深度解析</Text>
              <Text type="secondary">把JD"翻译"成学生能理解的语言</Text>
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Space direction="vertical">
              <Text strong>完整闭环设计</Text>
              <Text type="secondary">从了解岗位到准备面试的完整链路</Text>
            </Space>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default HomePage;
