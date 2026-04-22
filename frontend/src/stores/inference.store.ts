import { makeAutoObservable } from "mobx";
import type { MLTask } from "@/services/inference.service";

export class InferenceStore {
  tasks: MLTask[] = [];

  constructor() {
    makeAutoObservable(this);
  }

  setAll(tasks: MLTask[]): void {
    this.tasks = tasks;
  }

  add(task: MLTask): void {
    this.tasks.push(task);
  }

  flush(): void {
    this.tasks = [];
  }
}
