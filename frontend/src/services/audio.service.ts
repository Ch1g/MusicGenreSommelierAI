import { apiFetch, apiFetchBlob } from "@/api/client";

export interface AudioFile {
  id: number;
  user_id: number;
  file_path: string;
}

interface AudioStoreWriter {
  setAll(files: AudioFile[]): void;
  add(file: AudioFile): void;
  remove(id: number): void;
}

export function listApi(userId: number): Promise<AudioFile[]> {
  return apiFetch<AudioFile[]>(`/audio/${userId}`);
}

export function uploadApi(userId: number, file: File): Promise<AudioFile> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<AudioFile>(`/audio/${userId}`, {
    method: "POST",
    body: form,
  });
}

export function deleteAudioApi(audioId: number): Promise<void> {
  return apiFetch<void>(`/audio/files/${audioId}`, { method: "DELETE" });
}

export function fetchAudioStream(audioId: number): Promise<Blob> {
  return apiFetchBlob(`/audio/files/${audioId}/stream`);
}

export async function loadAudios(store: AudioStoreWriter, userId: number): Promise<void> {
  const files = await listApi(userId);
  store.setAll(files);
}

export async function uploadAudio(
  store: AudioStoreWriter,
  userId: number,
  file: File,
): Promise<void> {
  const audio = await uploadApi(userId, file);
  store.add(audio);
}

export async function removeAudio(store: AudioStoreWriter, audioId: number): Promise<void> {
  await deleteAudioApi(audioId);
  store.remove(audioId);
}
