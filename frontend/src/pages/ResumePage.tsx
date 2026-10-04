import { useState, useEffect } from 'react';
import { useWindowSize } from '../hooks';
import { Card, Form, Input, Button, message, Typography, Divider, List, Tag, Space, Progress, Empty, Select } from 'antd';
import { evaluateResume, optimizeResume, getResumeTemplates } from '../services/api';
import type { ResumeTemplate, ResumeEvaluation, ResumeOptimizeResult } from '../types/resume';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const ResumePage: React.FC = () => {
  const [form] = Form.useForm();
  const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
  const [evaluation, setEvaluation] = useState<ResumeEvaluation | null>(null);
  const [optimized, setOptimized] = useState<ResumeOptimizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const { isMobile } = useWindowSize();

  useEffect(() => {
    let active = true;
    getResumeTemplates().then((data) => { if (active) setTemplates(data); })
      .catch(() => { if (active) message.error('简历模板加载失败'); });
    return () => { active = false; };
  }, []);


  const handleEvaluate = async (values: any) => {
    setLoading(true);
    try {
      const result = await evaluateResume(values.resumeContent, values.targetJob);
      setEvaluation(result);
      message.success('简历评估完成');
    } catch (error: any) {
      message.error(error?.message || '评估失败');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    setLoading(true);
    try {
      const result = await optimizeResume(values.resumeContent, values.targetJob);
      setOptimized(result);
      message.success('简历优化完成');
    } catch (error: any) {
      message.error(error?.message || '优化失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={2}>简历优化助手</Title>
      <Paragraph>根据规则检查简历完整性、技能匹配和经历表达，并整理排版</Paragraph>

      <Select
        placeholder="选择简历模板"
        style={{ width: '100%', marginBottom: 16 }}
        disabled={loading}
        options={templates.map((template) => ({ label: template.name, value: template.id }))}
        onChange={(id) => {
          const template = templates.find((item) => item.id === id);
          if (template) form.setFieldValue('resumeContent', template.content);
          setEvaluation(null);
          setOptimized(null);
        }}
      />

      <Card title="简历评估" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleEvaluate} disabled={loading}>
          <Form.Item name="targetJob" label="目标岗位" rules={[{ required: true, whitespace: true }]}>
            <Input placeholder="例如：前端开发工程师" />
          </Form.Item>
          <Form.Item name="resumeContent" label="简历内容" rules={[{ required: true, whitespace: true }]}>
            <TextArea 
              rows={isMobile ? 6 : 10} 
              placeholder="粘贴你的简历内容..."
            />
          </Form.Item>
          <Form.Item>
            <Space wrap>
              <Button type="primary" htmlType="submit" loading={loading}>
                评估简历
              </Button>
              <Button onClick={handleOptimize} loading={loading}>
                整理与建议
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
          {evaluation.category_scores && Object.keys(evaluation.category_scores).length > 0 ? (
            <List
              dataSource={Object.entries(evaluation.category_scores)}
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
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无维度评分" />
          )}

          <Title level={4}>优势</Title>
          {evaluation.strengths && evaluation.strengths.length > 0 ? (
            <Space wrap>
              {evaluation.strengths.map((s: string, idx: number) => (
                <Tag key={idx} color="green">{s}</Tag>
              ))}
            </Space>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无优势项" />
          )}

          <Title level={4}>待改进</Title>
          {evaluation.weaknesses && evaluation.weaknesses.length > 0 ? (
            <Space wrap>
              {evaluation.weaknesses.map((w: string, idx: number) => (
                <Tag key={idx} color="orange">{w}</Tag>
              ))}
            </Space>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无改进建议" />
          )}

          <Title level={4}>建议</Title>
          {evaluation.suggestions && evaluation.suggestions.length > 0 ? (
            <ul>
              {evaluation.suggestions.map((s: string, idx: number) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无建议" />
          )}
        </Card>
      )}

      {!evaluation && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              尚未评估简历
              <br />
              <span style={{ fontSize: 12, color: '#999' }}>
                填写上方表单并点击"评估简历"开始
              </span>
            </span>
          }
          style={{ marginBottom: 24 }}
        />
      )}

      {optimized && (
        <Card title="优化结果" style={{ marginBottom: 24 }}>
          <Title level={4}>优化建议</Title>
          {optimized.changes && optimized.changes.length > 0 ? (
            <List
              dataSource={optimized.changes}
              renderItem={(item: string, idx: number) => <List.Item key={idx}>{item}</List.Item>}
            />
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无优化建议" />
          )}
          <Divider />
          <Title level={4}>优化后内容</Title>
          <TextArea rows={10} value={optimized.optimized_content} readOnly />
        </Card>
      )}

      {!optimized && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              尚未优化简历
              <br />
              <span style={{ fontSize: 12, color: '#999' }}>
                输入简历内容并点击"整理与建议"开始
              </span>
            </span>
          }
          style={{ marginBottom: 24 }}
        />
      )}
    </div>
  );
};

export default ResumePage;
