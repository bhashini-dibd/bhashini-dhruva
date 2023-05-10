export enum FeedbackType {
  RATING = "rating",
  COMMENT = "comment",
  THUMBS = "thumbs",
  RATING_LIST = "ratingList",
  COMMENT_LIST = "commentList",
  THUMBS_LIST = "thumbsList",
  CHECKBOX_LIST = "checkboxList",
}

export enum ULCATaskType {
  ASR = "asr",
  TRANSLATION = "translation",
  TTS = "tts",
  TRANSLITERATION = "transliteration",
  NER = "ner",
  STS = "sts", // TODO: Remove
}

interface RequestConfig {
  taskType: ULCATaskType;
  config: any;
}

interface ControlConfig {
  dataTracking: boolean;
}

export interface PipelineOutput {
  controlConfig: ControlConfig;
  pipelineResponse: string[];
}

interface ULCAGenericInferenceResponse {
  taskType: ULCATaskType;
  config?: Record<string, unknown> | null;
  output?: Record<string, unknown>[] | null;
  audio?: Record<string, unknown>[] | null;
}

export interface PipelineInput {
  pipelineTasks: RequestConfig[];
  inputData: any;
  controlConfig: ControlConfig;
}
interface BaseFeedbackType {
  parameterName: string;
}

interface FeedbackTypeRating extends BaseFeedbackType {
  rating: number;
}

interface FeedbackTypeCheckbox extends BaseFeedbackType {
  isSelected: boolean;
}

interface FeedbackTypeComment extends BaseFeedbackType {
  comment: string;
}

interface FeedbackTypeThumbs extends BaseFeedbackType {
  isLiked: boolean;
}

interface CommonFeedback {
  question: string;
  feedbackType: FeedbackType;
  comment?: string | null;
  isLiked?: boolean | null;
  rating?: number | null;
}

interface GranularFeedback extends CommonFeedback {
  checkboxList?: FeedbackTypeCheckbox[] | null;
  ratingList?: FeedbackTypeRating[] | null;
  commentList?: FeedbackTypeComment[] | null;
  thumbsList?: FeedbackTypeThumbs[] | null;
}

export interface TaskFeedback {
  taskType: ULCATaskType;
  commonFeedback: CommonFeedback[];
  granularFeedback?: GranularFeedback[] | null;
}

export interface PipelineFeedback {
  commonFeedback: CommonFeedback[];
}

export interface ULCAFeedbackRequest {
  feedbackTimeStamp?: number | null;
  feedbackLanguage: string;
  pipelineInput: PipelineInput;
  pipelineOutput?: PipelineOutput | null;
  suggestedPipelineOutput?: PipelineOutput | null;
  pipelineFeedback?: PipelineFeedback | null;
  taskFeedback?: TaskFeedback[] | null;
}
