import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, Row, Col, Spin, Button, Input, Typography, Tag, Divider, message, Select, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { analyzeJob, parseJD } from '../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const AnalysisPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [analysis, setAnalysis] = useState<any>(null);
  const [parsing, setParsing] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [jdText, setJdText] = useState('');
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('jobId') || '');

  const handleAnalyzeJob = async () => {
    if (!selectedJobId) {
      message.warning('请输入职位ID');
      return;
    }
    setLoading(true);
    try {
      const result = await analyzeJob(selectedJobId);
      setAnalysis(result);
    } catch (error) {
      message.error('分析失败');
    } finally {
      setLoading(false);
    }
  };

  const handleParseJD = async () => {
    if (!jdText.trim()) {
      message.warning('请输入JD文本');
      return;
    }
    setLoading(true);
    try {
      const result = await parseJD(jdText);
      setParsing(result);
    } catch (error) {
      message.error('解析失败');
    } finally {
      setLoading(false);
    }
  };

  const getRadarOption = () => {
    if (!analysis) return {};
    const skills = analysis.hard_skills?.slice(0, 6) || [];
    return {
      title: { text: '技能要求雷达图' },
      radar: {
        indicator: skills.map((s: any) => ({ name: s.name, max: 100 }))
      },
      series: [{
        type: 'radar',
        data: [{
          value: skills.map(() => 80),
          name: '要求水平'
        }]
      }]
    };
  };

  return (
    <div>
      <Title level={2}>岗位智能分析</Title>
      <Paragraph>输入职位ID或直接粘贴JD文本，AI将为您智能分析岗位的真实工作内容与能力要求</Paragraph>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card title="职位分析">
            <Input 
              placeholder="输入职位ID" 
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              style={{ marginBottom: 16 }}
            />
            <Button 
              type="primary" 
              icon={<SearchOutlined />} 
              onClick={handleAnalyzeJob} 
              loading={loading}
              block
            >
              分析职位
            </Button>

            {analysis && (
              <>
                <Divider />
                <Title level={4}>真实工作内容</Title>
                <ul>
                  {analysis.real_work_content?.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>

                <Title level={4}>硬技能要求</Title>
                <Space wrap>
                  {analysis.hard_skills?.map((skill: any, idx: number) => (
                    <Tag key={idx} color="blue">{skill.name}</Tag>
                  ))}
                </Space>

                <Title level={4}>软技能要求</Title>
                <Space wrap>
                  {analysis.soft_skills?.map((skill: any, idx: number) => (
                    <Tag key={idx} color="green">{skill.name}</Tag>
                  ))}
                </Space>

                <Title level={4}>职业发展路径</Title>
                <Space wrap>
                  {analysis.career_path?.map((path: string, idx: number) => (
                    <Tag key={idx} color="purple">{path}</Tag>
                  ))}
                </Space>
              </>
            )}
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="JD文本解析">
            <TextArea
              rows={6}
              placeholder="粘贴招聘JD文本，AI将为您解析..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              style={{ marginBottom: 16 }}
            />
            <Button 
              type="primary" 
              onClick={handleParseJD} 
              loading={loading}
              block
            >
              解析JD
            </Button>

            {parsing && (
              <>
                <Divider />
                <Title level={4}>关键职责</Title>
                <ul>
                  {parsing.key_responsibilities?.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>

                <Title level={4}>所需技能</Title>
                <Space wrap>
                  {parsing.required_skills?.map((skill: string, idx: number) => (
                    <Tag key={idx} color="blue">{skill}</Tag>
                  ))}
                </Space>

                <Title level={4}>经验要求</Title>
                <Tag>{parsing.experience_level}</Tag>

                <Title level={4}>学历要求</Title>
                <Tag>{parsing.education_requirement}</Tag>

                <Title level={4}>白话翻译</Title>
                <Paragraph>{parsing.plain_language}</Paragraph>
              </>
            )}
          </Card>
        </Col>
      </Row>

      {analysis && (
        <Card title="技能雷达图" style={{ marginTop: 24 }}>
          <ReactECharts option={getRadarOption()} style={{ height: 400 }} />
        </Card>
      )}
    </div>
  );
};

export default AnalysisPage;
