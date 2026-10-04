import { Skeleton, Card, Row, Col } from 'antd';

/**
 * 职位卡片骨架屏 - 用于职位列表加载时显示
 */
export const JobCardSkeleton: React.FC = () => {
  return (
    <div style={{ marginBottom: 16 }}>
      {Array.from({ length: 5 }).map((_, index) => (
        <Card key={index} style={{ marginBottom: 12 }}>
          <Skeleton avatar paragraph={{ rows: 2 }} active>
            <Skeleton.Input style={{ width: 200, marginBottom: 8 }} active />
            <br />
            <Skeleton.Input style={{ width: 150 }} active />
          </Skeleton>
        </Card>
      ))}
    </div>
  );
};

/**
 * 职位详情骨架屏 - 用于职位详情页加载时显示
 */
export const JobDetailSkeleton: React.FC = () => {
  return (
    <div>
      <Skeleton.Button style={{ width: 80, marginBottom: 16 }} active />
      <Skeleton.Input style={{ width: '50%', marginBottom: 24, height: 36 }} active />
      <Card style={{ marginBottom: 24 }}>
        <Skeleton paragraph={{ rows: 4 }} active />
      </Card>
      <Card title={<Skeleton.Input style={{ width: 100 }} active />} style={{ marginBottom: 24 }}>
        <Skeleton paragraph={{ rows: 3 }} active />
      </Card>
      <Card title={<Skeleton.Input style={{ width: 100 }} active />}>
        <Skeleton paragraph={{ rows: 2 }} active />
      </Card>
    </div>
  );
};

/**
 * 分析结果骨架屏 - 用于分析页面加载时显示
 */
export const AnalysisSkeleton: React.FC = () => {
  return (
    <Row gutter={[24, 24]}>
      <Col xs={24} md={12}>
        <Card title={<Skeleton.Input style={{ width: 80 }} active />}>
          <Skeleton.Input style={{ width: '100%', marginBottom: 16 }} active />
          <Skeleton.Button style={{ width: '100%' }} active />
          <Skeleton paragraph={{ rows: 6 }} active style={{ marginTop: 24 }} />
        </Card>
      </Col>
      <Col xs={24} md={12}>
        <Card title={<Skeleton.Input style={{ width: 80 }} active />}>
          <Skeleton.Input style={{ width: '100%', marginBottom: 16 }} active />
          <Skeleton.Button style={{ width: '100%' }} active />
          <Skeleton paragraph={{ rows: 6 }} active style={{ marginTop: 24 }} />
        </Card>
      </Col>
    </Row>
  );
};

/**
 * 行动清单骨架屏
 */
export const ActionPlanSkeleton: React.FC = () => {
  return (
    <div>
      <Card title={<Skeleton.Input style={{ width: 80 }} active />} style={{ marginBottom: 24 }}>
        <Skeleton paragraph={{ rows: 4 }} active />
        <Skeleton.Button style={{ width: '100%', marginTop: 16 }} active />
      </Card>
      <Skeleton paragraph={{ rows: 3 }} active style={{ marginBottom: 16 }} />
      <Card title={<Skeleton.Input style={{ width: 120 }} active />}>
        <Skeleton paragraph={{ rows: 5 }} active />
      </Card>
    </div>
  );
};

/**
 * 简历评估骨架屏
 */
export const ResumeSkeleton: React.FC = () => {
  return (
    <div>
      <Card title={<Skeleton.Input style={{ width: 80 }} active />} style={{ marginBottom: 24 }}>
        <Skeleton paragraph={{ rows: 3 }} active />
        <Skeleton.Button style={{ width: 120, marginTop: 16 }} active />
      </Card>
      <Card title={<Skeleton.Input style={{ width: 80 }} active />}>
        <Skeleton.Avatar active size={120} shape="circle" style={{ margin: '0 auto', display: 'block' }} />
        <Skeleton paragraph={{ rows: 4 }} active style={{ marginTop: 24 }} />
      </Card>
    </div>
  );
};

/**
 * 模拟面试骨架屏
 */
export const InterviewSkeleton: React.FC = () => {
  return (
    <div>
      <Card title={<Skeleton.Input style={{ width: 80 }} active />} style={{ marginBottom: 24 }}>
        <Skeleton paragraph={{ rows: 2 }} active />
        <Skeleton.Button style={{ width: 100, marginTop: 16 }} active />
      </Card>
      <Card title={<Skeleton.Input style={{ width: 80 }} active />}>
        <Skeleton paragraph={{ rows: 3 }} active />
        <Skeleton.Input style={{ width: '100%', marginTop: 16, height: 100 }} active />
        <Skeleton.Button style={{ width: 120, marginTop: 16 }} active />
      </Card>
    </div>
  );
};

export default JobCardSkeleton;
