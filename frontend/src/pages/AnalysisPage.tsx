import { useState, useEffect } from 'react';
import { useWindowSize } from '../hooks';
import { useSearchParams } from 'react-router-dom';
import { Card, Row, Col, Spin, Button, Input, Typography, Tag, Divider, message, Space, Empty } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { analyzeJob, parseJD, type JobAnalysis, type ParsedJD } from '../services/api';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const AnalysisPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);
  const [parsing, setParsing] = useState<ParsedJD | null>(null);
  const [loading, setLoading] = useState(false);
  const [jdText, setJdText] = useState('');
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('jobId') || '');
  const { isMobile } = useWindowSize();

  useEffect(() => {
    setSelectedJobId(searchParams.get('jobId') || '');
    setAnalysis(null);
  }, [searchParams]);


  const handleAnalyzeJob = async () => {
    if (!selectedJobId.trim()) {
      message.warning('请输入职位ID');
      return;
    }
    setLoading(true);
    setAnalysis(null);
    try {
      const result = await analyzeJob(selectedJobId.trim());
      setAnalysis(result);
      message.success('职位分析完成');
    } catch (error: any) {
      message.error(error?.message || '分析失败');
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
    setParsing(null);
    try {
      const result = await parseJD(jdText);
      setParsing(result);
      message.success('JD解析完成');
    } catch (error: any) {
      message.error(error?.message || '解析失败');
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
          value: skills.map((skill) => ({ '入门': 30, '进阶': 60, '精通': 100 }[analysis.skill_levels[skill.name]] || 60)),
          name: '要求水平'
        }]
      }]
    };
  };

  return (
    <div>
      <Title level={2}>岗位智能分析</Title>
      <Paragraph>输入职位ID提取岗位要求，或粘贴JD文本进行解析；未配置模型时使用规则分析</Paragraph>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card title="职位分析">
            <Spin spinning={loading}>
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

              {analysis ? (
                <>
                  <Divider />
                  <Title level={4}>真实工作内容</Title>
                  {analysis.real_work_content && analysis.real_work_content.length > 0 ? (
                    <ul>
                      {analysis.real_work_content.map((item: string, idx: number) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无工作内容数据" />
                  )}

                  <Title level={4}>硬技能要求</Title>
                  {analysis.hard_skills && analysis.hard_skills.length > 0 ? (
                    <Space wrap>
                      {analysis.hard_skills.map((skill: any, idx: number) => (
                        <Tag key={idx} color="blue">{skill.name}</Tag>
                      ))}
                    </Space>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无硬技能要求" />
                  )}

                  <Title level={4}>软技能要求</Title>
                  {analysis.soft_skills && analysis.soft_skills.length > 0 ? (
                    <Space wrap>
                      {analysis.soft_skills.map((skill: any, idx: number) => (
                        <Tag key={idx} color="green">{skill.name}</Tag>
                      ))}
                    </Space>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无软技能要求" />
                  )}

                  <Title level={4}>职业发展路径</Title>
                  {analysis.career_path && analysis.career_path.length > 0 ? (
                    <Space wrap>
                      {analysis.career_path.map((path: string, idx: number) => (
                        <Tag key={idx} color="purple">{path}</Tag>
                      ))}
                    </Space>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无职业发展路径" />
                  )}
                </>
              ) : (
                !loading && (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      <span>
                        尚未分析任何职位
                        <br />
                        <span style={{ fontSize: 12, color: '#999' }}>
                          输入职位ID并点击"分析职位"开始
                        </span>
                      </span>
                    }
                  />
                )
              )}
            </Spin>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="JD文本解析">
            <Spin spinning={loading}>
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

              {parsing ? (
                <>
                  <Divider />
                  {parsing.is_fallback && <Tag>规则解析</Tag>}
                  <Title level={4}>关键职责</Title>
                  {parsing.key_responsibilities && parsing.key_responsibilities.length > 0 ? (
                    <ul>
                      {parsing.key_responsibilities.map((item: string, idx: number) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无关键职责数据" />
                  )}

                  <Title level={4}>所需技能</Title>
                  {parsing.required_skills && parsing.required_skills.length > 0 ? (
                    <Space wrap>
                      {parsing.required_skills.map((skill: string, idx: number) => (
                        <Tag key={idx} color="blue">{skill}</Tag>
                      ))}
                    </Space>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无技能要求" />
                  )}

                  <Title level={4}>经验要求</Title>
                  {parsing.experience_level ? (
                    <Tag>{parsing.experience_level}</Tag>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无经验要求" />
                  )}

                  <Title level={4}>学历要求</Title>
                  {parsing.education_requirement ? (
                    <Tag>{parsing.education_requirement}</Tag>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无学历要求" />
                  )}

                  <Title level={4}>白话翻译</Title>
                  {parsing.plain_language ? (
                    <Paragraph>{parsing.plain_language}</Paragraph>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无翻译内容" />
                  )}
                </>
              ) : (
                !loading && (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      <span>
                        尚未解析任何JD
                        <br />
                        <span style={{ fontSize: 12, color: '#999' }}>
                          粘贴JD文本并点击"解析JD"开始
                        </span>
                      </span>
                    }
                  />
                )
              )}
            </Spin>
          </Card>
        </Col>
      </Row>

      {analysis && analysis.hard_skills.length > 0 && (
        <Card title="技能雷达图" style={{ marginTop: 24 }}>
          <ReactECharts option={getRadarOption()} style={{ height: 400 }} />
        </Card>
      )}
    </div>
  );
};

export default AnalysisPage;
