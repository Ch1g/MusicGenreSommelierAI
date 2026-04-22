import { makeAutoObservable } from "mobx";
import type { Transaction } from "@/services/transactions.service";

export class TransactionStore {
  balance: number = 0;
  transactions: Transaction[] = [];

  constructor() {
    makeAutoObservable(this);
  }

  setAll(transactions: Transaction[], balance: number): void {
    this.transactions = transactions;
    this.balance = balance;
  }

  add(transaction: Transaction): void {
    this.transactions.push(transaction);
    if (transaction.status === "success") {
      this.balance += transaction.amount;
    }
  }

  flush(): void {
    this.transactions = [];
    this.balance = 0;
  }
}
