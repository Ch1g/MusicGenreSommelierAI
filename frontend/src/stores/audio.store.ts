import { makeAutoObservable } from "mobx";
import type { AudioFile } from "@/services/audio.service";

export class AudioStore {
  files: AudioFile[] = [];

  constructor() {
    makeAutoObservable(this);
  }

  setAll(files: AudioFile[]): void {
    this.files = files;
  }

  add(file: AudioFile): void {
    this.files.push(file);
  }

  remove(id: number): void {
    this.files = this.files.filter((f) => f.id !== id);
  }

  flush(): void {
    this.files = [];
  }
}
