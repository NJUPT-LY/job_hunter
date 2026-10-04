import { useState, useEffect } from 'react';

export interface WindowSize {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
}

/**
 * Hook to track window size and provide responsive breakpoints
 * Replaces duplicate resize handlers across multiple components
 */
export const useWindowSize = (breakpoint: number = 768, tabletBreakpoint: number = 1024): WindowSize => {
  const [windowSize, setWindowSize] = useState<WindowSize>({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
    isMobile: typeof window !== 'undefined' ? window.innerWidth < breakpoint : false,
    isTablet: typeof window !== 'undefined' ? window.innerWidth >= breakpoint && window.innerWidth < tabletBreakpoint : false,
    isDesktop: typeof window !== 'undefined' ? window.innerWidth >= tabletBreakpoint : false,
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      setWindowSize({
        width,
        height,
        isMobile: width < breakpoint,
        isTablet: width >= breakpoint && width < tabletBreakpoint,
        isDesktop: width >= tabletBreakpoint,
      });
    };

    // Initial detection
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [breakpoint, tabletBreakpoint]);

  return windowSize;
};

export default useWindowSize;