import { setTokenGetter } from "@/api/client";
import { AuthStore } from "./auth.store";
import { AudioStore } from "./audio.store";
import { TransactionStore } from "./transaction.store";
import { InferenceStore } from "./inference.store";

export class RootStore {
  readonly auth: AuthStore;
  readonly audio: AudioStore;
  readonly transaction: TransactionStore;
  readonly inference: InferenceStore;

  constructor() {
    this.auth = new AuthStore();
    this.audio = new AudioStore();
    this.transaction = new TransactionStore();
    this.inference = new InferenceStore();
    setTokenGetter(() => this.auth.token);
  }
}
