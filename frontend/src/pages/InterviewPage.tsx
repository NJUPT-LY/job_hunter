import { useState } from 'react';
import { Card, Form, Select, Button, message, Typography, List, Tag, Space, Divider, Input } from 'antd';
import { MessageOutlined, SendOutlined } from '@ant-design/icons';
import { getInterviewQuestions, evaluateAnswer } from '../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const InterviewPage: React.FC = () => {
  const [form] = Form.useForm();
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<any[]>([]);

  const handleGetQuestions = async (values: any) => {
    setLoading(true);
    try {
      const result = await getInterviewQuestions(
        values.jobCategory || '技术',
        values.interviewType || '技术面',
        values.difficulty || '中等'
      );
      setQuestions(result);
      if (result.length > 0) {
        setCurrentQuestion(result[0]);
      }
      message.success('获取面试题目成功');
    } catch (error) {
      message.error('获取失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!answer.trim() || !currentQuestion) {
      message.warning('请先回答问题');
      return;
    }
    setLoading(true);
    try {
      const result = await evaluateAnswer(
        currentQuestion.question,
        answer,
        '目标岗位'
      );
      setEvaluation(result);
      setChatHistory([...chatHistory, { question: currentQuestion.question, answer, evaluation: result }]);
      message.success('回答评估完成');
    } catch (error) {
      message.error('评估失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = () => {
    const currentIndex = questions.findIndex(q => q.question === currentQuestion?.question);
    if (currentIndex < questions.length - 1) {
      setCurrentQuestion(questions[currentIndex + 1]);
      setAnswer('');
      setEvaluation(null);
    } else {
      message.info('已是最后一题');
    }
  };

  return (
    <div>
      <Title level={2}>模拟面试</Title>
      <Paragraph>AI模拟面试官，帮助你练习面试技巧，提供实时反馈</Paragraph>

      <Card title="面试设置" style={{ marginBottom: 24 }}>
        <Form form={form} layout="inline" onFinish={handleGetQuestions}>
          <Form.Item name="jobCategory" label="岗位类别">
            <Select style={{ width: 120 }}>
              <Select.Option value="技术">技术</Select.Option>
              <Select.Option value="产品">产品</Select.Option>
              <Select.Option value="数据分析">数据分析</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="interviewType" label="面试类型">
            <Select style={{ width: 120 }}>
              <Select.Option value="技术面">技术面</Select.Option>
              <Select.Option value="HR面">HR面</Select.Option>
              <Select.Option value="行为面">行为面</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="difficulty" label="难度">
            <Select style={{ width: 120 }}>
              <Select.Option value="简单">简单</Select.Option>
              <Select.Option value="中等">中等</Select.Option>
              <Select.Option value="困难">困难</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<MessageOutlined />}>
              获取题目
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {currentQuestion && (
        <Card title="当前问题" style={{ marginBottom: 24 }}>
          <Typography.Paragraph strong style={{ fontSize: 16 }}>
            {currentQuestion.question}
          </Typography.Paragraph>
          
          <Title level={5}>提示</Title>
          <Space wrap>
            {currentQuestion.hints?.map((hint: string, idx: number) => (
              <Tag key={idx} color="blue">{hint}</Tag>
            ))}
          </Space>

          <Divider />

          <Title level={5}>你的回答</Title>
          <TextArea
            rows={4}
            placeholder="请输入你的回答..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            style={{ marginBottom: 16 }}
          />
          <Space>
            <Button type="primary" icon={<SendOutlined />} onClick={handleSubmitAnswer} loading={loading}>
              提交回答
            </Button>
            <Button onClick={handleNextQuestion}>下一题</Button>
          </Space>

          {evaluation && (
            <>
              <Divider />
              <Title level={4}>评估结果</Title>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: evaluation.score > 80 ? '#52c41a' : evaluation.score > 60 ? '#faad14' : '#ff4d4f' }}>
                得分：{evaluation.score}分
              </div>
              
              <Title level={5}>优势</Title>
              <Space wrap>
                {evaluation.strengths?.map((s: string, idx: number) => (
                  <Tag key={idx} color="green">{s}</Tag>
                ))}
              </Space>

              <Title level={5}>不足</Title>
              <Space wrap>
                {evaluation.weaknesses?.map((w: string, idx: number) => (
                  <Tag key={idx} color="orange">{w}</Tag>
                ))}
              </Space>

              <Title level={5}>建议</Title>
              <ul>
                {evaluation.suggestions?.map((s: string, idx: number) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </>
          )}
        </Card>
      )}

      {chatHistory.length > 0 && (
        <Card title="面试记录">
          <List
            dataSource={chatHistory}
            renderItem={(item, idx) => (
              <List.Item>
                <List.Item.Meta
                  title={`问题${idx + 1}: ${item.question}`}
                  description={
                    <div>
                      <div>回答: {item.answer}</div>
                      <div>得分: <Tag color={item.evaluation.score > 80 ? 'green' : item.evaluation.score > 60 ? 'orange' : 'red'}>{item.evaluation.score}分</Tag></div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
};

export default InterviewPage;
