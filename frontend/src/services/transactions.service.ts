import { apiFetch } from "@/api/client";

export interface Transaction {
  id: number;
  user_id: number;
  amount: number;
  status: string;
  created_at: string;
}

export interface BalanceResponse {
  balance: number;
}

interface TransactionStoreWriter {
  setAll(transactions: Transaction[], balance: number): void;
  add(transaction: Transaction): void;
}

export function getBalanceApi(userId: number): Promise<BalanceResponse> {
  return apiFetch<BalanceResponse>(`/transactions/${userId}/balance`);
}

export function listApi(userId: number): Promise<Transaction[]> {
  return apiFetch<Transaction[]>(`/transactions/${userId}`);
}

export function addFundsApi(userId: number, amount: number): Promise<Transaction> {
  return apiFetch<Transaction>(`/transactions/${userId}/funds`, {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export async function loadTransactions(
  store: TransactionStoreWriter,
  userId: number,
): Promise<void> {
  const [{ balance }, transactions] = await Promise.all([
    getBalanceApi(userId),
    listApi(userId),
  ]);
  store.setAll(transactions, balance);
}

export async function depositFunds(
  store: TransactionStoreWriter,
  userId: number,
  amount: number,
): Promise<void> {
  const transaction = await addFundsApi(userId, amount);
  store.add(transaction);
}
