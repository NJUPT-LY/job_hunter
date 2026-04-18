import { useState } from 'react';
import { Card, Form, Input, Select, Button, message, Steps, Timeline, Tag, Space, Typography } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { generateActionPlan } from '../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const ActionPlanPage: React.FC = () => {
  const [form] = Form.useForm();
  const [plan, setPlan] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async (values: any) => {
    setLoading(true);
    try {
      const result = await generateActionPlan(values.jobTitle, {
        major: values.major,
        grade: values.grade,
        skills: values.skills?.split(',').map((s: string) => s.trim()) || []
      });
      setPlan(result);
      message.success('行动清单生成成功');
    } catch (error) {
      message.error('生成失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={2}>阶段性行动清单</Title>
      <Paragraph>输入你的信息和目标岗位，AI将为你生成个性化的学习路径和行动清单</Paragraph>

      <Card title="生成行动清单" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleGenerate}>
          <Form.Item name="jobTitle" label="目标岗位" rules={[{ required: true }]}>
            <Input placeholder="例如：前端开发工程师、数据分析师" />
          </Form.Item>
          <Form.Item name="major" label="专业">
            <Input placeholder="例如：计算机科学与技术" />
          </Form.Item>
          <Form.Item name="grade" label="年级">
            <Select placeholder="选择年级">
              <Select.Option value="大一">大一</Select.Option>
              <Select.Option value="大二">大二</Select.Option>
              <Select.Option value="大三">大三</Select.Option>
              <Select.Option value="大四">大四</Select.Option>
              <Select.Option value="研究生">研究生</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="skills" label="现有技能">
            <Input placeholder="用逗号分隔，例如：HTML, CSS, JavaScript" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              生成行动清单
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {plan.length > 0 && (
        <>
          <Steps
            current={0}
            items={plan.map((p, i) => ({ title: p.phase }))}
            style={{ marginBottom: 32 }}
          />

          {plan.map((phase, phaseIndex) => (
            <Card key={phaseIndex} title={phase.phase} style={{ marginBottom: 24 }}>
              <Title level={4}>{phase.title}</Title>
              <Paragraph>{phase.description}</Paragraph>
              
              <Timeline>
                {phase.tasks?.map((task: string, idx: number) => (
                  <Timeline.Item key={idx} dot={<ClockCircleOutlined style={{ fontSize: '16px' }} />}>
                    {task}
                  </Timeline.Item>
                ))}
              </Timeline>

              {phase.resources && phase.resources.length > 0 && (
                <>
                  <Title level={5}>推荐资源</Title>
                  <Space wrap>
                    {phase.resources.map((resource: string, idx: number) => (
                      <Tag key={idx} color="geekblue">{resource}</Tag>
                    ))}
                  </Space>
                </>
              )}
            </Card>
          ))}
        </>
      )}
    </div>
  );
};

export default ActionPlanPage;
