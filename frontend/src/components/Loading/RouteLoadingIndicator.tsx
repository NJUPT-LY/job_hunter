import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * 路由切换加载指示器
 * 在页面路由切换时显示顶部进度条
 */
const RouteLoadingIndicator: React.FC = () => {
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let fadeTimer: ReturnType<typeof setTimeout>;
    let interval: ReturnType<typeof setInterval>;

    // 路由变化时显示加载指示器
    setLoading(true);
    setProgress(0);

    // 模拟进度增加
    interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 15;
      });
    }, 50);

    // 一段时间后自动完成
    timer = setTimeout(() => {
      clearInterval(interval);
      setProgress(100);
      fadeTimer = setTimeout(() => {
        setLoading(false);
        setProgress(0);
      }, 300);
    }, 500);

    return () => {
      clearInterval(interval);
      clearTimeout(timer);
      clearTimeout(fadeTimer);
    };
  }, [location.pathname]);

  if (!loading) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        zIndex: 9999,
        height: 3,
        background: 'transparent',
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${progress}%`,
          background: 'linear-gradient(90deg, #1677ff, #4096ff)',
          transition: 'width 0.1s ease',
          boxShadow: '0 0 10px rgba(22, 119, 255, 0.5)',
        }}
      />
    </div>
  );
};

export default RouteLoadingIndicator;
