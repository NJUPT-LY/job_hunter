import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ==================== 用户偏好Store ====================

interface UserPreference {
  theme: 'light' | 'dark';
  language: 'zh-CN' | 'en-US';
  sidebarCollapsed: boolean;
  setTheme: (theme: 'light' | 'dark') => void;
  setLanguage: (language: 'zh-CN' | 'en-US') => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  resetPreferences: () => void;
}

export const useUserPreferenceStore = create<UserPreference>()(
  persist(
    (set) => ({
      theme: 'light',
      language: 'zh-CN',
      sidebarCollapsed: false,
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      resetPreferences: () =>
        set({
          theme: 'light',
          language: 'zh-CN',
          sidebarCollapsed: false,
        }),
    }),
    {
      name: 'zhilu-user-preferences',
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// ==================== 搜索缓存Store ====================

interface SearchCache {
  recentKeywords: string[];
  addKeyword: (keyword: string) => void;
  clearKeywords: () => void;
  removeKeyword: (keyword: string) => void;
}

export const useSearchCacheStore = create<SearchCache>()(
  persist(
    (set, get) => ({
      recentKeywords: [],
      addKeyword: (keyword) => {
        if (!keyword.trim()) return;
        keyword = keyword.trim();
        const keywords = get().recentKeywords;
        // 去重并添加到最前面
        const filtered = keywords.filter((k) => k !== keyword);
        const newKeywords = [keyword, ...filtered].slice(0, 10); // 最多保留10个
        set({ recentKeywords: newKeywords });
      },
      clearKeywords: () => set({ recentKeywords: [] }),
      removeKeyword: (keyword) =>
        set({
          recentKeywords: get().recentKeywords.filter((k) => k !== keyword),
        }),
    }),
    {
      name: 'zhilu-search-cache',
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// ==================== 表单缓存Store ====================

interface FormCache {
  // 行动清单表单
  actionPlanForm: {
    jobTitle?: string;
    major?: string;
    grade?: string;
    skills?: string;
  };
  // 简历表单
  resumeForm: {
    targetJob?: string;
    resumeContent?: string;
  };
  // 模拟面试表单
  interviewForm: {
    jobCategory?: string;
    interviewType?: string;
    difficulty?: string;
  };
  setActionPlanForm: (data: Partial<FormCache['actionPlanForm']>) => void;
  setResumeForm: (data: Partial<FormCache['resumeForm']>) => void;
  setInterviewForm: (data: Partial<FormCache['interviewForm']>) => void;
  clearAllForms: () => void;
  clearActionPlanForm: () => void;
  clearResumeForm: () => void;
  clearInterviewForm: () => void;
}

export const useFormCacheStore = create<FormCache>()(
  persist(
    (set) => ({
      actionPlanForm: {},
      resumeForm: {},
      interviewForm: {},
      setActionPlanForm: (data) =>
        set((state) => ({
          actionPlanForm: { ...state.actionPlanForm, ...data },
        })),
      setResumeForm: (data) =>
        set((state) => ({
          resumeForm: { ...state.resumeForm, ...data },
        })),
      setInterviewForm: (data) =>
        set((state) => ({
          interviewForm: { ...state.interviewForm, ...data },
        })),
      clearAllForms: () =>
        set({
          actionPlanForm: {},
          resumeForm: {},
          interviewForm: {},
        }),
      clearActionPlanForm: () => set({ actionPlanForm: {} }),
      clearResumeForm: () => set({ resumeForm: {} }),
      clearInterviewForm: () => set({ interviewForm: {} }),
    }),
    {
      name: 'zhilu-form-cache',
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// ==================== 缓存管理工具函数 ====================

/**
 * 清理所有缓存
 */
export const clearAllCache = (): void => {
  useUserPreferenceStore.getState().resetPreferences();
  useSearchCacheStore.getState().clearKeywords();
  useFormCacheStore.getState().clearAllForms();
  localStorage.removeItem('zhilu-user-preferences');
  localStorage.removeItem('zhilu-search-cache');
  localStorage.removeItem('zhilu-form-cache');
};

/**
 * 获取缓存大小（字节）
 */
export const getCacheSize = (): number => {
  let size = 0;
  const keys = ['zhilu-user-preferences', 'zhilu-search-cache', 'zhilu-form-cache'];
  for (const key of keys) {
    const value = localStorage.getItem(key);
    if (value) {
      size += new Blob([value]).size;
    }
  }
  return size;
};

/**
 * 格式化缓存大小
 */
export const formatCacheSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};
