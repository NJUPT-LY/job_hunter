import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const getJobs = async (keyword?: string, page: number = 1, pageSize: number = 20): Promise<any> => {
  const params: any = { page, page_size: pageSize };
  if (keyword) params.keyword = keyword;
  return api.get('/jobs/', { params });
};

export const getJob = async (id: string): Promise<any> => {
  return api.get(`/jobs/${id}`);
};

export const crawlJobs = async (keyword: string): Promise<any> => {
  return api.post('/jobs/crawl', null, { params: { keyword } });
};

export const analyzeJob = async (jobId: string): Promise<any> => {
  return api.post(`/analysis/analyze/${jobId}`);
};

export const parseJD = async (jdText: string): Promise<any> => {
  return api.post('/analysis/parse-jd', null, { params: { jd_text: jdText } });
};

export const analyzeSkillGap = async (userSkills: any, jobId: string): Promise<any> => {
  return api.post('/analysis/gap', userSkills, { params: { job_id: jobId } });
};

export const generateActionPlan = async (jobTitle: string, userProfile: any): Promise<any> => {
  return api.post('/action-plan/generate', { job_title: jobTitle, user_profile: userProfile });
};

export const getResumeTemplates = async (category?: string): Promise<any> => {
  const params: any = {};
  if (category) params.category = category;
  return api.get('/resume/templates', { params });
};

export const evaluateResume = async (resumeContent: string, targetJob: string): Promise<any> => {
  return api.post('/resume/evaluate', { resume_content: resumeContent, target_job: targetJob });
};

export const optimizeResume = async (resumeContent: string, targetJob: string): Promise<any> => {
  return api.post('/resume/optimize', { resume_content: resumeContent, target_job: targetJob });
};

export const getInterviewQuestions = async (jobCategory: string, interviewType: string, difficulty: string): Promise<any> => {
  return api.get('/interview/questions', { 
    params: { job_category: jobCategory, interview_type: interviewType, difficulty } 
  });
};

export const simulateInterview = async (jobTitle: string, interviewType: string, userAnswer?: string): Promise<any> => {
  return api.post('/interview/simulate', { job_title: jobTitle, interview_type: interviewType, user_answer: userAnswer });
};

export const evaluateAnswer = async (question: string, answer: string, jobTitle: string): Promise<any> => {
  return api.post('/interview/evaluate', { question, answer, job_title: jobTitle });
};

export default api;
