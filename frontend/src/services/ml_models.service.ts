import { apiFetch } from "@/api/client";

export interface MLModel {
  id: number;
  model_path: string;
  prediction_cost: number;
  input_width: number;
  input_height: number;
}

export function listModels(): Promise<MLModel[]> {
  return apiFetch<MLModel[]>("/ml-models/");
}
