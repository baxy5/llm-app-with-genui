import { ECBasicOption } from "echarts/types/dist/shared";

export interface IChatSessionsResponse {
  session_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface IChatMessagesResponse {
  id: number;
  type: string;
  content?: string | null;
  option?: ECBasicOption | null;
  component?: UIEvent | null | any;
}
