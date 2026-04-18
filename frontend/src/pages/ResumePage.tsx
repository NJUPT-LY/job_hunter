import { useState } from 'react';
import { Card, Form, Input, Button, message, Radio, Typography, Divider, List, Tag, Space, Progress } from 'antd';
import { UploadOutlined, FileTextOutlined } from '@ant-design/icons';
import { evaluateResume, optimizeResume, getResumeTemplates } from '../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const ResumePage: React.FC = () => {
  const [form] = Form.useForm();
  const [templates, setTemplates] = useState<any[]>([]);
  const [evaluation, setEvaluation] = useState<any>(null);
  const [optimized, setOptimized] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [resumeContent, setResumeContent] = useState('');

  const handleEvaluate = async (values: any) => {
    setLoading(true);
    try {
      const result = await evaluateResume(values.resumeContent, values.targetJob);
      setEvaluation(result);
      message.success('简历评估完成');
    } catch (error) {
      message.error('评估失败');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!resumeContent) {
      message.warning('请输入简历内容');
      return;
    }
    setLoading(true);
    try {
      const result = await optimizeResume(resumeContent, form.getFieldValue('targetJob') || '目标岗位');
      setOptimized(result);
      message.success('简历优化完成');
    } catch (error) {
      message.error('优化失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={2}>简历优化助手</Title>
      <Paragraph>AI帮你优化简历，提升求职成功率</Paragraph>

      <Card title="简历评估" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleEvaluate}>
          <Form.Item name="targetJob" label="目标岗位" rules={[{ required: true }]}>
            <Input placeholder="例如：前端开发工程师" />
          </Form.Item>
          <Form.Item name="resumeContent" label="简历内容" rules={[{ required: true }]}>
            <TextArea 
              rows={10} 
              placeholder="粘贴你的简历内容..."
              value={resumeContent}
              onChange={(e) => setResumeContent(e.target.value)}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                评估简历
              </Button>
              <Button onClick={handleOptimize} loading={loading}>
                AI优化
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {evaluation && (
        <Card title="评估结果" style={{ marginBottom: 24 }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <Progress type="circle" percent={evaluation.overall_score} size={120} 
              strokeColor={evaluation.overall_score > 80 ? '#52c41a' : evaluation.overall_score > 60 ? '#faad14' : '#ff4d4f'} 
            />
            <div style={{ marginTop: 8 }}>综合评分：{evaluation.overall_score}分</div>
          </div>

          <Title level={4}>各维度评分</Title>
          <List
            dataSource={Object.entries(evaluation.category_scores || {})}
            renderItem={([key, value]: [string, any]) => (
              <List.Item>
                <List.Item.Meta
                  title={key}
                  description={
                    <Progress percent={value as number} size="small" />
                  }
                />
              </List.Item>
            )}
          />

          <Title level={4}>优势</Title>
          <Space wrap>
            {evaluation.strengths?.map((s: string, idx: number) => (
              <Tag key={idx} color="green">{s}</Tag>
            ))}
          </Space>

          <Title level={4}>待改进</Title>
          <Space wrap>
            {evaluation.weaknesses?.map((w: string, idx: number) => (
              <Tag key={idx} color="orange">{w}</Tag>
            ))}
          </Space>

          <Title level={4}>建议</Title>
          <ul>
            {evaluation.suggestions?.map((s: string, idx: number) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </Card>
      )}

      {optimized && (
        <Card title="优化结果" style={{ marginBottom: 24 }}>
          <Title level={4}>优化建议</Title>
          <List
            dataSource={optimized.changes}
            renderItem={(item: string, idx: number) => <List.Item>{item}</List.Item>}
          />
          <Divider />
          <Title level={4}>优化后内容</Title>
          <TextArea rows={10} value={optimized.optimized_content} readOnly />
        </Card>
      )}
    </div>
  );
};

export default ResumePage;
