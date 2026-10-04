export interface ResumeTemplate {
  id: string;
  name: string;
  category: string;
  content: string;
}

export interface ResumeEvaluation {
  overall_score: number;
  category_scores: Record<string, number>;
  suggestions: string[];
  strengths: string[];
  weaknesses: string[];
}

export interface ResumeOptimizeResult {
  original_content: string;
  optimized_content: string;
  changes: string[];
}
