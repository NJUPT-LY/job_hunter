import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Descriptions, Tag, Button, Divider, Typography, Space, Card, Alert } from 'antd';
import { ArrowLeftOutlined, BarChartOutlined } from '@ant-design/icons';
import { getJob } from '../services/api';
import { JobDetailSkeleton } from '../components/Skeleton/JobCardSkeleton';
import type { Job } from '../types/job';

const { Title, Paragraph, Text } = Typography;

const JobDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setJob(null);
    setError('');
    getJob(id!).then((data) => { if (active) setJob(data); })
      .catch((err) => { if (active) setError(err.message || '获取职位详情失败'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);

  if (loading) {
    return <JobDetailSkeleton />;
  }

  if (!job) {
    return <Alert type="error" message={error || '职位不存在'} showIcon />;
  }

  return (
    <div>
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={() => navigate(-1)} 
        style={{ marginBottom: 16 }}
      >
        返回
      </Button>

      <Title level={2}>{job.title}</Title>
      
      <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="公司名称">{job.company}</Descriptions.Item>
        <Descriptions.Item label="工作地点">{job.location}</Descriptions.Item>
        <Descriptions.Item label="薪资范围">
          {job.salary ? <Tag color="green">{job.salary}</Tag> : '面议'}
        </Descriptions.Item>
        <Descriptions.Item label="经验要求">
          <Tag>{job.experience || '不限'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="学历要求">
          <Tag>{job.education || '不限'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="数据来源">
          {job.source || '未知'}
        </Descriptions.Item>
      </Descriptions>

      <Card title="职位技能" style={{ marginBottom: 24 }}>
        <Space wrap>
          {job.skills?.map((skill: string, index: number) => (
            <Tag key={index} color="blue">{skill}</Tag>
          ))}
        </Space>
      </Card>

      <Card title="职位描述" style={{ marginBottom: 24 }}>
        <Paragraph>{job.description}</Paragraph>
      </Card>

      <Card title="任职要求">
        <ul>
          {job.requirements?.map((req: string, index: number) => (
            <li key={index}>{req}</li>
          ))}
        </ul>
      </Card>

      <Divider />

      <Space>
        <Button 
          type="primary" 
          icon={<BarChartOutlined />}
          onClick={() => navigate(`/analysis?jobId=${job.id}`)}
        >
          分析此岗位
        </Button>
      </Space>
    </div>
  );
};

export default JobDetailPage;
