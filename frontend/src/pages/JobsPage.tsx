import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Table, AutoComplete, Button, Space, Tag, message, Typography, Empty } from 'antd';
import { SearchOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { getJobsPage, crawlJobs } from '../services/api';
import type { Job } from '../types/job';
import { useWindowSize } from '../hooks';
import { JobCardSkeleton } from '../components/Skeleton/JobCardSkeleton';
import { useSearchCacheStore } from '../stores/cacheStore';

const { Title } = Typography;

const JobsPage: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [crawling, setCrawling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isMobile } = useWindowSize();
  const { recentKeywords, addKeyword } = useSearchCacheStore();
  const requestId = useRef(0);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    fetchJobs();
    return () => { requestId.current += 1; };
  }, [page, searchKeyword, refresh]);

  const fetchJobs = async () => {
    const currentRequest = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const data = await getJobsPage(searchKeyword, page, pageSize);
      if (currentRequest !== requestId.current) return;
      setJobs(data.items);
      setTotal(data.total);
    } catch (err: any) {
      if (currentRequest !== requestId.current) return;
      const msg = err?.message || '获取职位列表失败';
      setError(msg);
      message.error(msg);
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
    }
  };

  const handleSearch = () => {
    if (keyword.trim()) {
      addKeyword(keyword.trim());
    }
    setPage(1);
    setSearchKeyword(keyword.trim());
    setRefresh((value) => value + 1);
  };

  const handleCrawl = async () => {
    if (!keyword.trim()) {
      message.warning('请先输入搜索关键词');
      return;
    }
    setCrawling(true);
    try {
      const result = await crawlJobs(keyword.trim());
      if (result.fetched) message.success(result.message);
      else message.warning(result.message);
      addKeyword(keyword.trim());
      setPage(1);
      setSearchKeyword(keyword.trim());
      setRefresh((value) => value + 1);
    } catch (err: any) {
      const msg = err?.message || '爬取失败';
      message.error(msg);
    } finally {
      setCrawling(false);
    }
  };

  const handleSelectKeyword = (value: string) => {
    setKeyword(value);
  };

  const columns = [
    {
      title: '职位名称',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: any) => (
        <Link to={`/jobs/${record.id}`}>{text}</Link>
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
      
      <Space style={{ marginBottom: 24, width: '100%' }} wrap>
        <AutoComplete
          allowClear
          placeholder="搜索关键词，如：前端开发、数据分析..."
          value={keyword}
          onChange={handleSelectKeyword}
          style={{ width: isMobile ? '100%' : 300, flex: isMobile ? '0 0 100%' : 'none' }}
          options={recentKeywords.map((k) => ({ label: k, value: k }))}
          onKeyDown={(event) => { if (event.key === 'Enter') handleSearch(); }}
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

      {loading && jobs.length === 0 ? (
        <JobCardSkeleton />
      ) : error && jobs.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              加载失败：<span style={{ color: '#ff4d4f' }}>{error}</span>
              <br />
              <Button type="link" onClick={() => setRefresh((value) => value + 1)} style={{ marginTop: 8 }}>
                点击重试
              </Button>
            </span>
          }
        />
      ) : jobs.length === 0 && !loading ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              暂无职位数据
              <br />
              <span style={{ fontSize: 12, color: '#999' }}>
                请输入关键词搜索，或点击"爬取新职位"获取最新职位
              </span>
            </span>
          }
        />
      ) : (
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 900 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: false,
            onChange: (p) => setPage(p)
          }}
        />
      )}
    </div>
  );
};

export default JobsPage;
