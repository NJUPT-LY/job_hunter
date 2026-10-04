import { Empty, Button, Typography } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title = '暂无数据',
  description,
  actionText,
  onAction,
  icon
}) => {
  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={
        <div style={{ textAlign: 'center' }}>
          {title && <div style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>{title}</div>}
          {description && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {description}
            </Text>
          )}
        </div>
      }
    >
      {actionText && onAction && (
        <Button type="primary" icon={<SearchOutlined />} onClick={onAction}>
          {actionText}
        </Button>
      )}
    </Empty>
  );
};

export default EmptyState;