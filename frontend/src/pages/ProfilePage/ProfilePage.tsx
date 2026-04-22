import { observer } from "mobx-react-lite";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useStores } from "@/stores/context";
import { fetchAudioStream, loadAudios, uploadAudio, removeAudio } from "@/services/audio.service";
import { fetchSpectrogram, loadTasks, runInference } from "@/services/inference.service";
import { listModels, type MLModel } from "@/services/ml_models.service";
import { loadTransactions, depositFunds } from "@/services/transactions.service";
import type { AudioFile } from "@/services/audio.service";
import styles from "./ProfilePage.module.css";

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function audioName(filePath: string): string {
  const base = filePath.split("/").pop() ?? filePath;
  const withoutUuid = base.replace(/^[0-9a-f-]{36}_/i, "");
  return withoutUuid;
}

// ── Balance & Funds ──────────────────────────────────────────────────────────

const BalanceSection = observer(() => {
  const { auth, transaction } = useStores();
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const handleAddFunds = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseFloat(amount);
    if (isNaN(parsed) || parsed <= 0) return;
    setLoading(true);
    setMsg(null);
    try {
      await depositFunds(transaction, auth.currentUser!.id, parsed);
      setAmount("");
      setMsg({ type: "ok", text: `+$${parsed.toFixed(2)} added` });
    } catch (err) {
      setMsg({ type: "err", text: err instanceof Error ? err.message : "Failed" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>
        <span className={styles.sectionTitleIcon}>💎</span> Balance
      </h2>
      <div className={styles.balanceDisplay}>
        <span className={styles.balanceCurrency}>$</span>
        <span className={styles.balanceAmount}>{transaction.balance.toFixed(2)}</span>
      </div>
      <form className={styles.addFundsForm} onSubmit={(e) => void handleAddFunds(e)}>
        <div className={styles.addFundsField}>
          <label className={styles.label} htmlFor="funds-amount">Add funds</label>
          <input
            id="funds-amount"
            type="number"
            min="0.01"
            step="0.01"
            className={styles.input}
            placeholder="10.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            disabled={loading}
          />
        </div>
        <button type="submit" className={styles.btnPrimary} disabled={loading || amount === ""}>
          {loading ? <span className="spinner" /> : null}
          Add
        </button>
      </form>
      {msg !== null && (
        <p
          className="error-message"
          style={{ color: msg.type === "ok" ? "var(--color-success)" : undefined }}
          role="status"
        >
          {msg.text}
        </p>
      )}
    </section>
  );
});

// ── Transaction History ──────────────────────────────────────────────────────

const TransactionSection = observer(() => {
  const { transaction } = useStores();

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>
        <span className={styles.sectionTitleIcon}>📋</span> Transactions
      </h2>
      {transaction.transactions.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>🧾</div>
          <p className={styles.emptyText}>No transactions yet</p>
        </div>
      ) : (
        <div className={styles.txList}>
          {[...transaction.transactions].reverse().map((tx) => (
            <div key={tx.id} className={styles.txRow}>
              <span className={styles.txDate}>{formatDate(tx.created_at)}</span>
              <span
                className={`${styles.txAmount} ${tx.amount >= 0 ? styles.txAmountPos : styles.txAmountNeg}`}
              >
                {tx.amount >= 0 ? "+" : "-"}${Math.abs(tx.amount).toFixed(2)}
              </span>
              <span className={`badge badge-${statusClass(tx.status)}`}>{tx.status}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
});

function statusClass(status: string): string {
  if (status === "success") return "success";
  if (status.startsWith("fail")) return "error";
  return "pending";
}

// ── Model Picker Modal ───────────────────────────────────────────────────────

interface ModelPickerProps {
  audioFile: AudioFile;
  onClose: () => void;
  onSubmit: (audioFileId: number, modelId: number) => Promise<void>;
}

function ModelPicker({ audioFile, onClose, onSubmit }: ModelPickerProps) {
  const [models, setModels] = useState<MLModel[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchErr, setFetchErr] = useState<string | null>(null);

  useEffect(() => {
    listModels()
      .then((m) => {
        setModels(m);
        if (m.length > 0) setSelected(m[0]!.id);
      })
      .catch(() => setFetchErr("Could not load models"));
  }, []);

  const handleRun = async () => {
    if (selected === null) return;
    setLoading(true);
    try {
      await onSubmit(audioFile.id, selected);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.modalTitle}>Run Inference</h3>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)" }}>
          File: <strong style={{ color: "var(--color-text-primary)" }}>{audioName(audioFile.file_path)}</strong>
        </p>
        {fetchErr !== null ? (
          <p className="error-message">{fetchErr}</p>
        ) : models.length === 0 ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "var(--space-4)" }}>
            <span className="spinner" />
          </div>
        ) : (
          <div className={styles.modelList}>
            {models.map((m) => (
              <button
                key={m.id}
                className={`${styles.modelOption} ${selected === m.id ? styles.modelOptionSelected : ""}`}
                onClick={() => setSelected(m.id)}
              >
                <span className={styles.modelName}>{audioName(m.model_path)}</span>
                <span className={styles.modelCost}>${m.prediction_cost.toFixed(2)} / inference</span>
              </button>
            ))}
          </div>
        )}
        <div className={styles.modalActions}>
          <button className={styles.btnCancel} onClick={onClose}>Cancel</button>
          <button
            className={styles.btnPrimary}
            onClick={() => void handleRun()}
            disabled={selected === null || loading}
          >
            {loading ? <span className="spinner" /> : null}
            Run
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Audio Files ──────────────────────────────────────────────────────────────

function AudioPlayer({ audioId, label }: { audioId: number; label: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    fetchAudioStream(audioId)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {});
    return () => {
      if (objectUrl !== null) URL.revokeObjectURL(objectUrl);
    };
  }, [audioId]);

  return (
    <audio
      controls
      src={src ?? ""}
      preload="none"
      aria-label={label}
    />
  );
}

const AudioSection = observer(({ onToast }: { onToast: (msg: string) => void }) => {
  const { auth, audio, inference } = useStores();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [pickerFile, setPickerFile] = useState<AudioFile | null>(null);

  const uploadFile = async (file: File) => {
    setUploading(true);
    try {
      await uploadAudio(audio, auth.currentUser!.id, file);
      onToast(`Uploaded "${file.name}"`);
    } catch (err) {
      onToast(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) void uploadFile(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void uploadFile(file);
    e.target.value = "";
  };

  const handleDelete = async (audioId: number) => {
    try {
      await removeAudio(audio, audioId);
      onToast("File deleted");
    } catch (err) {
      onToast(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const handleInferenceSubmit = async (audioFileId: number, modelId: number) => {
    await runInference(inference, audioFileId, modelId);
    onToast("Inference task queued");
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>
        <span className={styles.sectionTitleIcon}>🎵</span> Audio Files
      </h2>

      <div
        className={`${styles.dropzone} ${dragOver ? styles.dropzoneActive : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload audio file"
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
      >
        <div className={styles.dropzoneIcon}>{uploading ? <span className="spinner" /> : "🎧"}</div>
        <p className={styles.dropzoneText}>{uploading ? "Uploading…" : "Drop audio or click to browse"}</p>
        <p className={styles.dropzoneHint}>MP3, WAV, FLAC, OGG, AAC</p>
        <input
          ref={inputRef}
          type="file"
          accept="audio/*"
          hidden
          onChange={handleFileInput}
          disabled={uploading}
        />
      </div>

      {audio.files.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>📂</div>
          <p className={styles.emptyText}>No audio files yet</p>
        </div>
      ) : (
        <div className={styles.audioList}>
          {audio.files.map((f) => (
            <div key={f.id} className={styles.audioItem}>
              <div className={styles.audioHeader}>
                <span className={styles.audioName}>{audioName(f.file_path)}</span>
                <div className={styles.audioActions}>
                  <button
                    className={styles.btnSecondary}
                    onClick={() => setPickerFile(f)}
                    title="Run genre inference"
                  >
                    ⚡ Predict
                  </button>
                  <button
                    className={styles.btnDanger}
                    onClick={() => void handleDelete(f.id)}
                    title="Delete file"
                  >
                    ✕
                  </button>
                </div>
              </div>
              <AudioPlayer audioId={f.id} label={`Audio player for ${audioName(f.file_path)}`} />
            </div>
          ))}
        </div>
      )}

      {pickerFile !== null && (
        <ModelPicker
          audioFile={pickerFile}
          onClose={() => setPickerFile(null)}
          onSubmit={handleInferenceSubmit}
        />
      )}
    </section>
  );
});

// ── Inference Log ────────────────────────────────────────────────────────────

const InferenceSection = observer(() => {
  const { inference } = useStores();

  return (
    <section className={`${styles.section} ${styles.inferenceSection}`}>
      <h2 className={styles.sectionTitle}>
        <span className={styles.sectionTitleIcon}>🔬</span> Inference Log
      </h2>
      {inference.tasks.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>📊</div>
          <p className={styles.emptyText}>No inference tasks yet. Upload an audio file and click Predict.</p>
        </div>
      ) : (
        <div className={styles.taskGrid}>
          {[...inference.tasks].reverse().map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </section>
  );
});

function TaskCard({ task }: { task: { id: number; status: string; result: Record<string, unknown> | null; error: string | null } }) {
  const isSuccess = task.status === "success";
  const isPending = task.status === "pending";
  const [spectrogramSrc, setSpectrogramSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!isSuccess) return;
    let objectUrl: string | null = null;
    fetchSpectrogram(task.id)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSpectrogramSrc(objectUrl);
      })
      .catch(() => {});
    return () => {
      if (objectUrl !== null) URL.revokeObjectURL(objectUrl);
    };
  }, [isSuccess, task.id]);

  const resultGenre =
    task.result !== null && typeof task.result === "object" && "genre" in task.result
      ? String(task.result["genre"])
      : task.result !== null
        ? JSON.stringify(task.result)
        : null;

  return (
    <div className={`${styles.taskCard} ${isSuccess ? styles.taskCardSuccess : ""}`}>
      {isSuccess ? (
        <div className={styles.taskSpectrogramWrapper}>
          <img
            src={spectrogramSrc ?? ""}
            alt={`Spectrogram for task ${task.id}`}
            className={styles.taskSpectrogram}
          />
          <div className={styles.spectrogramGlow} />
        </div>
      ) : (
        <div className={`${styles.spectrogramPlaceholder} ${isPending ? "pulse" : ""}`}>
          {isPending ? "Processing…" : "—"}
        </div>
      )}
      <div className={styles.taskCardBody}>
        <div className={styles.taskMeta}>
          <span className={styles.taskId}>Task #{task.id}</span>
          <span className={`badge badge-${statusClass(task.status)}`}>
            {isPending && <span className="pulse">●</span>} {task.status}
          </span>
        </div>
        {resultGenre !== null && (
          <div className={styles.taskResult}>{resultGenre}</div>
        )}
        {task.error !== null && (
          <div className={styles.taskError}>{task.error}</div>
        )}
      </div>
    </div>
  );
}

// ── ProfilePage ──────────────────────────────────────────────────────────────

export const ProfilePage = observer(() => {
  const { auth, audio, transaction, inference } = useStores();
  const navigate = useNavigate();
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const userId = auth.currentUser!.id;

  useEffect(() => {
    void loadAudios(audio, userId);
    void loadTransactions(transaction, userId);
    void loadTasks(inference, userId);
  }, [audio, transaction, inference, userId]);

  // Poll inference tasks every 5 s to pick up worker results
  useEffect(() => {
    const id = setInterval(() => {
      void loadTasks(inference, userId);
    }, 5000);
    return () => clearInterval(id);
  }, [inference, userId]);

  const showToast = (msg: string) => {
    setToast(msg);
    if (toastTimer.current !== null) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3500);
  };

  const handleSignOut = () => {
    auth.clearSession();
    audio.flush();
    transaction.flush();
    inference.flush();
    void navigate("/");
  };

  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <span className={styles.navBrand}>
          <svg width="20" height="20" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="rgba(124,92,252,0.15)" />
            {[4, 8, 12, 16, 20, 24, 28].map((x, i) => (
              <rect
                key={x}
                x={x - 1}
                y={32 - [16, 24, 12, 28, 10, 20, 14][i]!}
                width="2"
                height={[16, 24, 12, 28, 10, 20, 14][i]}
                rx="1"
                fill="currentColor"
              />
            ))}
          </svg>
          Sommelier
        </span>
        <div className={styles.navRight}>
          <span className={styles.navUser}>{auth.currentUser?.email}</span>
          <button className={styles.signOutBtn} onClick={handleSignOut}>Sign Out</button>
        </div>
      </nav>

      <main className={styles.main}>
        <div className={styles.grid}>
          <BalanceSection />
          <TransactionSection />
          <AudioSection onToast={showToast} />
          <InferenceSection />
        </div>
      </main>

      {toast !== null && (
        <div className={styles.toast} role="status">{toast}</div>
      )}
    </div>
  );
});
