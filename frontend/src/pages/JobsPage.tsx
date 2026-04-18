import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Input, Button, Space, Tag, InputNumber, message, Spin, Typography } from 'antd';
import { SearchOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { getJobs, crawlJobs } from '../services/api';

const { Title } = Typography;

const JobsPage: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [crawling, setCrawling] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, [page]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const data = await getJobs(keyword, page, pageSize);
      setJobs(data);
      setTotal(100);
    } catch (error) {
      message.error('获取职位列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchJobs();
  };

  const handleCrawl = async () => {
    if (!keyword) {
      message.warning('请先输入搜索关键词');
      return;
    }
    setCrawling(true);
    try {
      const result = await crawlJobs(keyword);
      message.success(result.message || '爬取完成');
      fetchJobs();
    } catch (error) {
      message.error('爬取失败');
    } finally {
      setCrawling(false);
    }
  };

  const columns = [
    {
      title: '职位名称',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: any) => (
        <a onClick={() => navigate(`/jobs/${record.id}`)}>{text}</a>
      )
    },
    {
      title: '公司',
      dataIndex: 'company',
      key: 'company'
    },
    {
      title: '地点',
      dataIndex: 'location',
      key: 'location'
    },
    {
      title: '薪资',
      dataIndex: 'salary',
      key: 'salary',
      render: (text: string) => text ? <Tag color="green">{text}</Tag> : '-'
    },
    {
      title: '经验',
      dataIndex: 'experience',
      key: 'experience',
      render: (text: string) => text || '不限'
    },
    {
      title: '学历',
      dataIndex: 'education',
      key: 'education',
      render: (text: string) => text || '不限'
    },
    {
      title: '技能',
      dataIndex: 'skills',
      key: 'skills',
      render: (skills: string[]) => (
        <Space wrap>
          {skills?.slice(0, 3).map((skill, index) => (
            <Tag key={index}>{skill}</Tag>
          ))}
          {skills && skills.length > 3 && <Tag>+{skills.length - 3}</Tag>}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Button 
          type="link" 
          icon={<EyeOutlined />}
          onClick={() => navigate(`/jobs/${record.id}`)}
        >
          查看详情
        </Button>
      )
    }
  ];

  return (
    <div>
      <Title level={2}>职位搜索</Title>
      
      <Space style={{ marginBottom: 24 }} wrap>
        <Input
          placeholder="搜索关键词，如：前端开发、数据分析..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onPressEnter={handleSearch}
          style={{ width: 300 }}
          prefix={<SearchOutlined />}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>
          搜索
        </Button>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={handleCrawl} 
          loading={crawling}
        >
          爬取新职位
        </Button>
      </Space>

      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="id"
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            onChange: (p) => setPage(p)
          }}
        />
      </Spin>
    </div>
  );
};

export default JobsPage;
