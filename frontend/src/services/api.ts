import axios, { AxiosError } from 'axios';
import type { Job, JobPage, JobStats, JobAnalysis, ParsedJD } from '../types/job';
import type { ResumeTemplate, ResumeEvaluation, ResumeOptimizeResult } from '../types/resume';
import type { InterviewQuestion, AnswerEvaluation } from '../types/interview';
export type { JobAnalysis, ParsedJD } from '../types/job';

// 统一响应格式接口
interface ApiResponse {
  code: number;
  message: string;
  data: any;
  success: boolean;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器：添加加载状态等（预留扩展）
api.interceptors.request.use(
  (config) => config,
  (error) => {
    console.error('请求配置错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器：统一解包响应数据和错误处理
api.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse;
    // 统一响应格式: {code, message, data, success}
    if (data && typeof data === 'object' && 'success' in data) {
      if (data.success) {
        return data.data;
      }
      // 业务错误：服务器返回了 success: false
      const error = new Error(data.message || '请求失败');
      (error as any).code = data.code;
      (error as any).response = response;
      return Promise.reject(error);
    }
    // 兼容旧格式：直接返回数据
    return data;
  },
  (error: AxiosError<ApiResponse>) => {
    // 统一错误信息提取
    let errorMessage = '网络错误，请稍后重试';
    if (error.response) {
      const responseData = error.response.data;
      // 优先使用统一响应格式中的message
      if (responseData && responseData.message) {
        errorMessage = responseData.message;
      } else if (typeof error.response.data === 'string') {
        errorMessage = error.response.data;
      } else if (error.response.status === 404) {
        errorMessage = '请求的资源不存在';
      } else if (error.response.status === 422) {
        errorMessage = '请求参数有误，请检查后重试';
      } else if (error.response.status >= 500) {
        errorMessage = '服务器错误，请稍后重试';
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMessage = '请求超时，请检查网络后重试';
    }
    console.error('API错误:', errorMessage, error);
    return Promise.reject(new Error(errorMessage));
  }
);

export const getJobs = async (keyword?: string, page: number = 1, pageSize: number = 20): Promise<any> => {
  const params: any = { page, page_size: pageSize };
  if (keyword) params.keyword = keyword;
  return api.get('/jobs/', { params });
};

export const getJobsPage = (keyword: string, page: number, pageSize: number): Promise<JobPage> =>
  api.get<JobPage, JobPage>('/jobs/page', { params: { keyword, page, page_size: pageSize } });

export const getJobStats = (): Promise<JobStats> => api.get<JobStats, JobStats>('/jobs/stats');

export const getJob = async (id: string): Promise<Job> => {
  return api.get<Job, Job>(`/jobs/${id}`);
};

export const crawlJobs = async (keyword: string): Promise<any> => {
  return api.post('/jobs/crawl', { keyword }, { timeout: 180000 });
};

export const analyzeJob = async (jobId: string): Promise<JobAnalysis> => {
  return api.post<JobAnalysis, JobAnalysis>(`/analysis/analyze/${jobId}`);
};

export const parseJD = async (jdText: string): Promise<ParsedJD> => {
  return api.post<ParsedJD, ParsedJD>('/analysis/parse-jd', { jd_text: jdText });
};

export const analyzeSkillGap = async (userSkills: any, jobId: string): Promise<any> => {
  return api.post('/analysis/gap', { user_skills: userSkills, job_id: jobId });
};

export const generateActionPlan = async (jobTitle: string, userProfile: any): Promise<any> => {
  return api.post('/action-plan/generate', { job_title: jobTitle, user_profile: userProfile });
};

export const getResumeTemplates = async (category?: string): Promise<ResumeTemplate[]> => {
  const params: any = {};
  if (category) params.category = category;
  return api.get<ResumeTemplate[], ResumeTemplate[]>('/resume/templates', { params });
};

export const evaluateResume = async (resumeContent: string, targetJob: string): Promise<ResumeEvaluation> => {
  return api.post<ResumeEvaluation, ResumeEvaluation>('/resume/evaluate', { resume_content: resumeContent, target_job: targetJob });
};

export const optimizeResume = async (resumeContent: string, targetJob: string): Promise<ResumeOptimizeResult> => {
  return api.post<ResumeOptimizeResult, ResumeOptimizeResult>('/resume/optimize', { resume_content: resumeContent, target_job: targetJob });
};

export const getInterviewQuestions = async (jobCategory: string, interviewType: string, difficulty: string): Promise<InterviewQuestion[]> => {
  return api.get<InterviewQuestion[], InterviewQuestion[]>('/interview/questions', {
    params: { job_category: jobCategory, interview_type: interviewType, difficulty } 
  });
};

export const simulateInterview = async (jobTitle: string, interviewType: string, userAnswer?: string): Promise<any> => {
  return api.post('/interview/simulate', { job_title: jobTitle, interview_type: interviewType, user_answer: userAnswer });
};

export const evaluateAnswer = async (question: string, answer: string, jobTitle: string): Promise<AnswerEvaluation> => {
  return api.post<AnswerEvaluation, AnswerEvaluation>('/interview/evaluate', { question, answer, job_title: jobTitle });
};

export default api;
