export interface InterviewQuestion {
  question: string;
  category: string;
  difficulty: string;
  hints: string[];
  evaluation_criteria: string[];
}

export interface AnswerEvaluation {
  score: number;
  feedback: string[];
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  ai_provider: string;
  is_fallback: boolean;
}

export interface ChatHistoryItem {
  question: string;
  answer: string;
  evaluation: AnswerEvaluation;
}
