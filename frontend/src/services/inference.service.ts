import { apiFetch, apiFetchBlob } from "@/api/client";

export interface MLTask {
  id: number;
  audio_spectrogram_id: number;
  transaction_id: number;
  ml_model_id: number;
  status: string;
  result: Record<string, unknown> | null;
  error: string | null;
}

interface InferenceStoreWriter {
  setAll(tasks: MLTask[]): void;
  add(task: MLTask): void;
}

export function runApi(audioFileId: number, mlModelId: number): Promise<MLTask> {
  return apiFetch<MLTask>("/inference/", {
    method: "POST",
    body: JSON.stringify({ audio_file_id: audioFileId, ml_model_id: mlModelId }),
  });
}

export function listTasksApi(userId: number): Promise<MLTask[]> {
  return apiFetch<MLTask[]>(`/inference/${userId}`);
}

export function fetchSpectrogram(taskId: number): Promise<Blob> {
  return apiFetchBlob(`/inference/spectrograms/${taskId}`);
}

export async function runInference(
  store: InferenceStoreWriter,
  audioFileId: number,
  mlModelId: number,
): Promise<void> {
  const task = await runApi(audioFileId, mlModelId);
  store.add(task);
}

export async function loadTasks(store: InferenceStoreWriter, userId: number): Promise<void> {
  const tasks = await listTasksApi(userId);
  store.setAll(tasks);
}
