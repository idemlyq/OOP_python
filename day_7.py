# ============================================================
# DAY 7 — СИСТЕМА ОТЧЁТНОСТИ И ВИЗУАЛИЗАЦИИ
# ============================================================
# Зависимости: pip install matplotlib

import os
import csv
import json
import uuid
import enum
import heapq
from abc import ABC, abstractmethod
from collections import Counter
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ============================================================
# БАЗА ДНЕЙ 1–4
# ============================================================
class AccountError(Exception): ...
class AccountFrozenError(AccountError): ...
class AccountClosedError(AccountError): ...
class InvalidOperationError(AccountError): ...
class InsufficientFundsError(AccountError): ...


class AccountStatus(enum.Enum):
    ACTIVE = "активный"
    FROZEN = "замороженный"
    CLOSED = "закрытый"


class Currency(enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class AbstractAccount(ABC):
    def __init__(self, owner, account_id=None, currency=Currency.RUB):
        self.owner = owner
        self.account_id = account_id or uuid.uuid4().hex[:8].upper()
        self._balance = Decimal("0")
        self._status = AccountStatus.ACTIVE
        self.currency = currency

    @abstractmethod
    def deposit(self, amount): ...
    @abstractmethod
    def withdraw(self, amount): ...
    @abstractmethod
    def get_account_info(self): ...


class BankAccount(AbstractAccount):
    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0):
        super().__init__(owner, account_id, currency)
        if initial_balance:
            self.deposit(initial_balance)

    @staticmethod
    def _validate_amount(amount):
        if isinstance(amount, bool):
            raise InvalidOperationError("bool не сумма")
        try:
            v = Decimal(str(amount))
        except Exception:
            raise InvalidOperationError(f"bad: {amount!r}")
        if v <= 0:
            raise InvalidOperationError("сумма <= 0")
        return v

    def _ensure_active(self):
        if self._status == AccountStatus.FROZEN:
            raise AccountFrozenError(f"{self.account_id} заморожен")
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(f"{self.account_id} закрыт")

    def deposit(self, amount):
        self._ensure_active()
        self._balance += self._validate_amount(amount)

    def withdraw(self, amount):
        self._ensure_active()
        v = self._validate_amount(amount)
        if v > self._balance:
            raise InsufficientFundsError(f"{self._balance} < {v}")
        self._balance -= v

    def freeze(self):
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError("закрыт")
        self._status = AccountStatus.FROZEN

    def activate(self):
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError("закрыт")
        self._status = AccountStatus.ACTIVE

    def close(self):
        if self._balance != 0:
            raise InvalidOperationError("баланс != 0")
        self._status = AccountStatus.CLOSED

    def get_account_info(self):
        return (f"{self.owner} ...{self.account_id[-4:]} "
                f"{self._status.value} {self._balance} {self.currency.value}")

    def __str__(self):
        return (f"[{self.__class__.__name__}] {self.owner} | "
                f"...{self.account_id[-4:]} | {self._status.value} | "
                f"{self._balance} {self.currency.value}")


class SavingsAccount(BankAccount):
    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0, min_balance=0, monthly_rate=0.01):
        super().__init__(owner, account_id, currency, initial_balance)
        self.min_balance = Decimal(str(min_balance))
        self.monthly_rate = Decimal(str(monthly_rate))

    def withdraw(self, amount):
        v = self._validate_amount(amount)
        self._ensure_active()
        if self._balance - v < self.min_balance:
            raise InsufficientFundsError(f"ниже минимума {self.min_balance}")
        self._balance -= v

    def __str__(self):
        return f"💎 {super().__str__()} (min={self.min_balance})"


class PremiumAccount(BankAccount):
    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0, overdraft_limit=50000, commission=0.005):
        super().__init__(owner, account_id, currency, initial_balance)
        self.overdraft_limit = Decimal(str(overdraft_limit))
        self.commission = Decimal(str(commission))

    def withdraw(self, amount):
        v = self._validate_amount(amount)
        self._ensure_active()
        commission = (v * self.commission).quantize(Decimal("0.01"))
        total = v + commission
        if self._balance - total < -self.overdraft_limit:
            raise InsufficientFundsError(f"овердрафт {self.overdraft_limit}")
        self._balance -= total

    def __str__(self):
        return f" {super().__str__()} (overdraft={self.overdraft_limit})"


class InvestmentAccount(BankAccount):
    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0):
        super().__init__(owner, account_id, currency, initial_balance)
        self.portfolio: Dict[str, Decimal] = {}

    def __str__(self):
        return f" {super().__str__()}"


# ---- Транзакции ----
class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER_INTERNAL = "transfer_internal"
    TRANSFER_EXTERNAL = "transfer_external"
    CURRENCY_EXCHANGE = "currency_exchange"


class TransactionStatus(enum.Enum):
    PENDING = "в ожидании"
    DELAYED = "отложена"
    COMPLETED = "выполнена"
    FAILED = "провалена"
    CANCELLED = "отменена"


class Priority(enum.Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10


class Transaction:
    def __init__(self, tx_type, amount, currency,
                 sender_account_id=None, recipient_account_id=None,
                 max_retries=2):
        self.transaction_id = "T" + uuid.uuid4().hex[:8].upper()
        self.tx_type = tx_type
        self.amount = Decimal(str(amount))
        self.currency = currency
        self.commission = Decimal("0")
        self.sender_account_id = sender_account_id
        self.recipient_account_id = recipient_account_id
        self.status = TransactionStatus.PENDING
        self.rejection_reason = None
        self.created_at = datetime.now()
        self.scheduled_at = None
        self.processed_at = None
        self.retry_count = 0
        self.max_retries = max_retries
        self.priority = Priority.NORMAL
        self.risk_level = None

    def __str__(self):
        return (f"[{self.transaction_id}] {self.tx_type.value} "
                f"{self.amount} {self.currency.value} ({self.status.value})")


class TransactionQueue:
    def __init__(self):
        self._heap = []
        self._counter = 0

    def add(self, tx, priority=None, delay_seconds=0):
        if priority is not None:
            tx.priority = priority
        now = datetime.now()
        if delay_seconds > 0:
            tx.scheduled_at = now + timedelta(seconds=delay_seconds)
            tx.status = TransactionStatus.DELAYED
        else:
            tx.scheduled_at = now
            tx.status = TransactionStatus.PENDING
        self._counter += 1
        heapq.heappush(self._heap, (-tx.priority.value, self._counter, tx))

    def get_ready(self):
        now = datetime.now()
        ready, not_ready, all_items = [], [], []
        while self._heap:
            all_items.append(heapq.heappop(self._heap))
        for item in all_items:
            tx = item[2]
            if tx.status in (TransactionStatus.COMPLETED,
                             TransactionStatus.FAILED,
                             TransactionStatus.CANCELLED):
                continue
            if tx.scheduled_at and tx.scheduled_at > now:
                not_ready.append(item)
            else:
                ready.append(item)
        for item in not_ready:
            heapq.heappush(self._heap, item)
        ready.sort(key=lambda x: (x[0], x[1]))
        return [item[2] for item in ready]

    def cancel(self, tx_id):
        for item in self._heap:
            tx = item[2]
            if tx.transaction_id == tx_id:
                if tx.status == TransactionStatus.COMPLETED:
                    raise InvalidOperationError("нельзя отменить")
                tx.status = TransactionStatus.CANCELLED
                return True
        return False

    def __len__(self):
        return sum(1 for i in self._heap
                   if i[2].status in (TransactionStatus.PENDING,
                                      TransactionStatus.DELAYED))


class TransactionProcessor:
    EXTERNAL_COMMISSION_RATE = Decimal("0.01")
    FX_RATES = {
        (Currency.RUB, Currency.USD): Decimal("0.011"),
        (Currency.USD, Currency.RUB): Decimal("90"),
        (Currency.RUB, Currency.EUR): Decimal("0.010"),
        (Currency.EUR, Currency.RUB): Decimal("100"),
        (Currency.USD, Currency.EUR): Decimal("0.92"),
        (Currency.EUR, Currency.USD): Decimal("1.09"),
    }

    def __init__(self, bank, retry_limit=2):
        self.bank = bank
        self.retry_limit = retry_limit
        self.error_log: List[dict] = []

    def process(self, tx):
        try:
            self._pre_validate(tx)
            self._calculate_commission(tx)
            self._execute(tx)
            tx.status = TransactionStatus.COMPLETED
            tx.processed_at = datetime.now()
            return True
        except AccountError as exc:
            self._handle_failure(tx, exc)
            return False

    def _pre_validate(self, tx):
        if tx.amount <= 0:
            raise InvalidOperationError("сумма <= 0")
        if tx.sender_account_id:
            s = self.bank._get_account(tx.sender_account_id)
            if s._status == AccountStatus.FROZEN:
                raise AccountFrozenError("отправитель заморожен")
            if s._status == AccountStatus.CLOSED:
                raise AccountClosedError("отправитель закрыт")
            if s.currency != tx.currency:
                raise InvalidOperationError("валюта не совпадает")
            if tx.tx_type in (TransactionType.TRANSFER_INTERNAL,
                              TransactionType.TRANSFER_EXTERNAL):
                if not isinstance(s, PremiumAccount) and s._balance < 0:
                    raise InvalidOperationError("перевод при минусе запрещён")
        if (tx.recipient_account_id
                and tx.tx_type != TransactionType.TRANSFER_EXTERNAL):
            r = self.bank._get_account(tx.recipient_account_id)
            if r._status == AccountStatus.FROZEN:
                raise AccountFrozenError("получатель заморожен")
            if r._status == AccountStatus.CLOSED:
                raise AccountClosedError("получатель закрыт")

    def _calculate_commission(self, tx):
        if tx.tx_type == TransactionType.TRANSFER_EXTERNAL:
            tx.commission = (tx.amount * self.EXTERNAL_COMMISSION_RATE
                             ).quantize(Decimal("0.01"))
        else:
            tx.commission = Decimal("0")

    def _execute(self, tx):
        if tx.tx_type == TransactionType.DEPOSIT:
            self.bank._get_account(tx.recipient_account_id).deposit(tx.amount)
        elif tx.tx_type == TransactionType.WITHDRAW:
            self.bank._get_account(tx.sender_account_id).withdraw(tx.amount)
        elif tx.tx_type == TransactionType.TRANSFER_INTERNAL:
            self._transfer_internal(tx)
        elif tx.tx_type == TransactionType.TRANSFER_EXTERNAL:
            self.bank._get_account(tx.sender_account_id).withdraw(
                tx.amount + tx.commission)
        elif tx.tx_type == TransactionType.CURRENCY_EXCHANGE:
            self._exchange(tx)

    def _convert(self, amount, frm, to):
        if frm == to:
            return amount
        rate = self.FX_RATES.get((frm, to))
        if rate is None:
            raise InvalidOperationError(f"нет курса {frm.value}→{to.value}")
        return (amount * rate).quantize(Decimal("0.01"))

    def _transfer_internal(self, tx):
        s = self.bank._get_account(tx.sender_account_id)
        r = self.bank._get_account(tx.recipient_account_id)
        ra = self._convert(tx.amount, tx.currency, r.currency)
        s.withdraw(tx.amount + tx.commission)
        r.deposit(ra)

    def _exchange(self, tx):
        s = self.bank._get_account(tx.sender_account_id)
        r = self.bank._get_account(tx.recipient_account_id)
        conv = self._convert(tx.amount, tx.currency, r.currency)
        s.withdraw(tx.amount)
        r.deposit(conv)

    def _handle_failure(self, tx, exc):
        tx.retry_count += 1
        tx.rejection_reason = str(exc)
        self.error_log.append({
            "time": datetime.now(),
            "transaction_id": tx.transaction_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "retry_count": tx.retry_count,
        })
        tx.status = (TransactionStatus.PENDING if tx.retry_count <= tx.max_retries
                     else TransactionStatus.FAILED)


# ============================================================
# ДЕНЬ 5. АУДИТ И РИСК
# ============================================================
class AuditLevel(enum.Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3


class AuditRecord:
    def __init__(self, level, category, message, metadata=None):
        self.timestamp = datetime.now()
        self.level = level
        self.category = category
        self.message = message
        self.metadata = metadata or {}

    def __str__(self):
        return (f"[{self.timestamp.strftime('%H:%M:%S')}] "
                f"[{self.level.name:8}] [{self.category:10}] {self.message}")


class AuditLog:
    def __init__(self):
        self.records: List[AuditRecord] = []

    def log(self, level, category, message, metadata=None):
        r = AuditRecord(level, category, message, metadata)
        self.records.append(r)
        return r

    def info(self, cat, msg, **md): return self.log(AuditLevel.INFO, cat, msg, md)
    def warning(self, cat, msg, **md): return self.log(AuditLevel.WARNING, cat, msg, md)
    def critical(self, cat, msg, **md): return self.log(AuditLevel.CRITICAL, cat, msg, md)

    def __len__(self):
        return len(self.records)


class RiskLevel(enum.Enum):
    LOW = "низкий"
    MEDIUM = "средний"
    HIGH = "высокий"


class RiskAnalyzer:
    LARGE_AMOUNT_THRESHOLD = {
        Currency.RUB: Decimal("100000"),
        Currency.USD: Decimal("1000"),
        Currency.EUR: Decimal("1000"),
        Currency.KZT: Decimal("500000"),
        Currency.CNY: Decimal("10000"),
    }
    FREQUENCY_WINDOW = 60
    FREQUENCY_MAX = 3

    def __init__(self, bank):
        self.bank = bank
        self.history: Dict[str, List[datetime]] = {}
        self.known_recipients: Dict[str, set] = {}

    def assess(self, client_id, tx) -> Tuple[RiskLevel, List[str]]:
        score, reasons = 0, []

        threshold = self.LARGE_AMOUNT_THRESHOLD.get(tx.currency)
        if threshold and tx.amount >= threshold:
            score += 2
            reasons.append(f"Крупная сумма ({tx.amount} {tx.currency.value})")

        now = datetime.now()
        cutoff = now - timedelta(seconds=self.FREQUENCY_WINDOW)
        recent = [t for t in self.history.get(client_id, []) if t >= cutoff]
        if len(recent) >= self.FREQUENCY_MAX:
            score += 2
            reasons.append(f"Частые операции: {len(recent)}/{self.FREQUENCY_WINDOW}с")

        if tx.tx_type in (TransactionType.TRANSFER_INTERNAL,
                          TransactionType.TRANSFER_EXTERNAL):
            if tx.recipient_account_id and tx.recipient_account_id not in \
                    self.known_recipients.get(client_id, set()):
                score += 1
                reasons.append(f"Новый получатель ...{tx.recipient_account_id[-4:]}")

        if self.bank._is_night():
            score += 1
            reasons.append("Ночное время")

        if score >= 3:
            level = RiskLevel.HIGH
        elif score >= 1:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return level, reasons

    def record_operation(self, client_id, tx):
        self.history.setdefault(client_id, []).append(datetime.now())
        if tx.recipient_account_id:
            self.known_recipients.setdefault(client_id, set()).add(
                tx.recipient_account_id)


# ============================================================
# КЛИЕНТ И БАНК
# ============================================================
class ClientStatus(enum.Enum):
    ACTIVE = "активный"
    BLOCKED = "заблокирован"


class Client:
    def __init__(self, full_name, birth_year, contacts, pin):
        age = datetime.now().year - birth_year
        if age < 18:
            raise InvalidOperationError(f"возраст {age} < 18")
        if not isinstance(pin, str) or not pin.isdigit() or len(pin) != 4:
            raise InvalidOperationError("PIN — 4 цифры")
        self.full_name = full_name.strip()
        self.birth_year = birth_year
        self.age = age
        self.contacts = contacts
        self.pin = pin
        self.client_id = "C" + uuid.uuid4().hex[:6].upper()
        self.status = ClientStatus.ACTIVE
        self.account_numbers: List[str] = []
        self.failed_attempts = 0
        self.suspicious_actions: List[str] = []
        self.history: List[Transaction] = []

    def __str__(self):
        return (f"👤 {self.full_name} (ID {self.client_id}, "
                f"{self.age} лет, {self.status.value})")


class Bank:
    ACCOUNT_TYPES = {
        "basic": BankAccount,
        "savings": SavingsAccount,
        "premium": PremiumAccount,
        "investment": InvestmentAccount,
    }
    NIGHT_START = 0
    NIGHT_END = 5

    def __init__(self, name):
        self.name = name
        self.clients: Dict[str, Client] = {}
        self.accounts: Dict[str, AbstractAccount] = {}
        self._current_hour = None
        self.audit = AuditLog()
        self.risk_analyzer = RiskAnalyzer(self)
        self.blocked_operations: List[dict] = []

    def _get_client(self, cid):
        if cid not in self.clients:
            raise InvalidOperationError(f"клиент {cid} не найден")
        return self.clients[cid]

    def _get_account(self, aid):
        if aid not in self.accounts:
            raise InvalidOperationError(f"счёт {aid} не найден")
        return self.accounts[aid]

    def _is_night(self):
        hour = (self._current_hour if self._current_hour is not None
                else datetime.now().hour)
        return self.NIGHT_START <= hour < self.NIGHT_END

    def add_client(self, full_name, birth_year, contacts, pin):
        c = Client(full_name, birth_year, contacts, pin)
        self.clients[c.client_id] = c
        self.audit.info("client", f"Зарегистрирован {c.full_name}")
        return c

    def open_account(self, client_id, account_type="basic", **kwargs):
        client = self._get_client(client_id)
        cls = self.ACCOUNT_TYPES.get(account_type)
        if cls is None:
            raise InvalidOperationError(f"тип {account_type!r} неизвестен")
        acc = cls(client.full_name, **kwargs)
        self.accounts[acc.account_id] = acc
        client.account_numbers.append(acc.account_id)
        self.audit.info("account", f"Открыт {account_type} {acc.account_id}")
        return acc

    def freeze_account(self, client_id, account_id):
        self._get_client(client_id)
        self._get_account(account_id).freeze()
        self.audit.warning("account", f"Счёт {account_id} заморожен")

    def process_with_risk_check(self, processor, tx, client_id) -> bool:
        level, reasons = self.risk_analyzer.assess(client_id, tx)
        tx.risk_level = level

        audit_level = {
            RiskLevel.LOW: AuditLevel.INFO,
            RiskLevel.MEDIUM: AuditLevel.WARNING,
            RiskLevel.HIGH: AuditLevel.CRITICAL,
        }[level]

        self.audit.log(audit_level, "risk",
                       f"{tx.transaction_id}: риск «{level.value}»",
                       {"client_id": client_id, "amount": str(tx.amount),
                        "currency": tx.currency.value, "reasons": reasons})

        if level == RiskLevel.HIGH:
            tx.status = TransactionStatus.CANCELLED
            tx.rejection_reason = "Заблокировано: " + "; ".join(reasons)
            self.blocked_operations.append({
                "transaction_id": tx.transaction_id,
                "client_id": client_id,
                "reasons": reasons,
                "timestamp": datetime.now(),
            })
            self.audit.critical("security",
                                f" Заблокирована {tx.transaction_id}",
                                {"client_id": client_id, "reasons": reasons})
            return False

        if level == RiskLevel.MEDIUM:
            self.audit.warning("risk",
                               f"  {tx.transaction_id} пропущена",
                               {"client_id": client_id, "reasons": reasons})

        ok = processor.process(tx)
        if ok:
            self.risk_analyzer.record_operation(client_id, tx)
            self._get_client(client_id).history.append(tx)
            self.audit.info("operation", f" {tx.transaction_id}",
                            {"client_id": client_id, "amount": str(tx.amount)})
        else:
            self.audit.warning("operation",
                               f" {tx.transaction_id}: {tx.rejection_reason}",
                               {"client_id": client_id})
        return ok

    def get_client_accounts(self, client_id):
        c = self._get_client(client_id)
        return [self.accounts[aid] for aid in c.account_numbers
                if aid in self.accounts]

    def get_client_history(self, client_id):
        return list(self._get_client(client_id).history)

    def get_suspicious_for_client(self, client_id):
        return [r for r in self.audit.records
                if r.metadata.get("client_id") == client_id
                and r.level in (AuditLevel.WARNING, AuditLevel.CRITICAL)]

    def get_clients_ranking(self):
        data = []
        for c in self.clients.values():
            total = sum((self.accounts[aid]._balance
                         for aid in c.account_numbers
                         if aid in self.accounts), Decimal("0"))
            data.append({"client_id": c.client_id,
                         "full_name": c.full_name,
                         "total_balance": total})
        data.sort(key=lambda r: r["total_balance"], reverse=True)
        return data

    def get_top_clients(self, n=3):
        return self.get_clients_ranking()[:n]

    def get_total_balance(self):
        return sum((a._balance for a in self.accounts.values()), Decimal("0"))


# ============================================================
# ДЕНЬ 6. СТАТИСТИКА + ОРКЕСТРАТОР
# ============================================================
class TransactionStats:
    @staticmethod
    def compute(transactions):
        stats = {"total": len(transactions),
                 "by_status": {}, "by_type": {}, "by_risk": {},
                 "volume_by_currency": {}, "commission_by_currency": {},
                 "successful": 0, "failed": 0, "blocked": 0}
        for tx in transactions:
            s = tx.status.value
            stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
            t = tx.tx_type.value
            stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
            if tx.risk_level:
                r = tx.risk_level.value
                stats["by_risk"][r] = stats["by_risk"].get(r, 0) + 1
            cur = tx.currency.value
            stats["volume_by_currency"][cur] = (
                stats["volume_by_currency"].get(cur, Decimal("0")) + tx.amount)
            stats["commission_by_currency"][cur] = (
                stats["commission_by_currency"].get(cur, Decimal("0")) + tx.commission)
            if tx.status == TransactionStatus.COMPLETED:
                stats["successful"] += 1
            elif tx.status == TransactionStatus.FAILED:
                stats["failed"] += 1
            elif tx.status == TransactionStatus.CANCELLED:
                stats["blocked"] += 1
        return stats


class BankingDemo:
    def __init__(self):
        self.bank = Bank("Демо-Банк")
        self.processor = TransactionProcessor(self.bank)
        self.queue = TransactionQueue()
        self.transactions: List[Transaction] = []
        self.clients: Dict[str, Client] = {}
        self.accounts: Dict[str, AbstractAccount] = {}

    def setup(self):
        specs = [
            ("ivan", "Иван Петров", 1990, "1111"),
            ("maria", "Мария Сидорова", 1985, "2222"),
            ("petr", "Пётр Новиков", 1988, "3333"),
            ("anna", "Анна Белова", 1992, "4444"),
            ("sergey", "Сергей Волков", 1975, "5555"),
            ("elena", "Елена Морозова", 1995, "6666"),
        ]
        for key, name, year, pin in specs:
            c = self.bank.add_client(name, year, {"phone": f"+7-{pin}"}, pin)
            self.clients[key] = c

        c, a = self.clients, self.accounts
        # У Ивана крупный начальный баланс для крупных переводов
        a["ivan_rub"] = self.bank.open_account(c["ivan"].client_id, "basic",
            currency=Currency.RUB, initial_balance=300000)
        a["ivan_usd"] = self.bank.open_account(c["ivan"].client_id, "premium",
            currency=Currency.USD, initial_balance=5000)
        a["maria_rub"] = self.bank.open_account(c["maria"].client_id, "basic",
            currency=Currency.RUB, initial_balance=30000)
        a["maria_usd"] = self.bank.open_account(c["maria"].client_id, "basic",
            currency=Currency.USD, initial_balance=500)
        a["petr_rub"] = self.bank.open_account(c["petr"].client_id, "savings",
            currency=Currency.RUB, initial_balance=10000, min_balance=0)
        a["anna_rub"] = self.bank.open_account(c["anna"].client_id, "basic",
            currency=Currency.RUB, initial_balance=15000)
        a["anna_eur"] = self.bank.open_account(c["anna"].client_id, "basic",
            currency=Currency.EUR, initial_balance=200)
        a["sergey_rub"] = self.bank.open_account(c["sergey"].client_id, "basic",
            currency=Currency.RUB, initial_balance=8000)
        a["elena_rub"] = self.bank.open_account(c["elena"].client_id, "basic",
            currency=Currency.RUB, initial_balance=12000)
        a["elena_usd"] = self.bank.open_account(c["elena"].client_id, "basic",
            currency=Currency.USD, initial_balance=300)
        a["petr_frozen"] = self.bank.open_account(c["petr"].client_id, "basic",
            currency=Currency.RUB, initial_balance=500)
        self.bank.freeze_account(c["petr"].client_id, a["petr_frozen"].account_id)

    def _run(self, label, tx, client_key, verbose=True):
        self.transactions.append(tx)
        cid = self.clients[client_key].client_id
        level, reasons = self.bank.risk_analyzer.assess(cid, tx)
        ok = self.bank.process_with_risk_check(self.processor, tx, cid)
        if verbose:
            marker = "+" if ok else "-"
            print(f"  {marker} {label} [риск: {level.value}]")

    def simulate_routine(self):
        print("\n" + "─" * 70)
        print("📋 СЦЕНАРИЙ 1: Обычные операции")
        print("─" * 70)
        a = self.accounts
        run = self._run

        run("Иван: депозит 5000 RUB",
            Transaction(TransactionType.DEPOSIT, 5000, Currency.RUB,
                        recipient_account_id=a["ivan_rub"].account_id), "ivan")
        run("Мария: депозит 3000 RUB",
            Transaction(TransactionType.DEPOSIT, 3000, Currency.RUB,
                        recipient_account_id=a["maria_rub"].account_id), "maria")
        run("Пётр: депозит 2000 RUB",
            Transaction(TransactionType.DEPOSIT, 2000, Currency.RUB,
                        recipient_account_id=a["petr_rub"].account_id), "petr")
        run("Иван: снятие 500 RUB",
            Transaction(TransactionType.WITHDRAW, 500, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id), "ivan")
        run("Мария: снятие 300 RUB",
            Transaction(TransactionType.WITHDRAW, 300, Currency.RUB,
                        sender_account_id=a["maria_rub"].account_id), "maria")
        run("Иван → Мария: 500 RUB",
            Transaction(TransactionType.TRANSFER_INTERNAL, 500, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["maria_rub"].account_id), "ivan")
        run("Иван → Мария: 300 RUB (повтор)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 300, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["maria_rub"].account_id), "ivan")
        run("Мария → Пётр: 200 RUB",
            Transaction(TransactionType.TRANSFER_INTERNAL, 200, Currency.RUB,
                        sender_account_id=a["maria_rub"].account_id,
                        recipient_account_id=a["petr_rub"].account_id), "maria")
        run("Иван → Мария USD: 5000 RUB (конвертация)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 5000, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["maria_usd"].account_id), "ivan")
        run("Иван: внешний перевод 100 USD",
            Transaction(TransactionType.TRANSFER_EXTERNAL, 100, Currency.USD,
                        sender_account_id=a["ivan_usd"].account_id,
                        recipient_account_id="EXT-1"), "ivan")
        run("Анна: депозит 1000 RUB",
            Transaction(TransactionType.DEPOSIT, 1000, Currency.RUB,
                        recipient_account_id=a["anna_rub"].account_id), "anna")
        run("Сергей: депозит 500 RUB",
            Transaction(TransactionType.DEPOSIT, 500, Currency.RUB,
                        recipient_account_id=a["sergey_rub"].account_id), "sergey")

    def simulate_suspicious(self):
        print("\n" + "─" * 70)
        print("📋 СЦЕНАРИЙ 2: Подозрительные операции")
        print("─" * 70)
        a = self.accounts
        run = self._run

        run("Иван → Мария: 150000 RUB (крупная, знакомый)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 150000, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["maria_rub"].account_id), "ivan")
        run("Иван → Елена: 200000 RUB (крупная + новый) → блок",
            Transaction(TransactionType.TRANSFER_INTERNAL, 200000, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["elena_rub"].account_id), "ivan")
        run("Пётр → Анна: 120000 RUB (крупная + новый) → блок",
            Transaction(TransactionType.TRANSFER_INTERNAL, 120000, Currency.RUB,
                        sender_account_id=a["petr_rub"].account_id,
                        recipient_account_id=a["anna_rub"].account_id), "petr")
        self.bank._current_hour = 3
        run(" Сергей → Анна: 500 RUB (ночь + новый)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 500, Currency.RUB,
                        sender_account_id=a["sergey_rub"].account_id,
                        recipient_account_id=a["anna_rub"].account_id), "sergey")
        self.bank._current_hour = None

        for i in range(1, 5):
            run(f"Сергей: быстрый депозит #{i}",
                Transaction(TransactionType.DEPOSIT, 100, Currency.RUB,
                            recipient_account_id=a["sergey_rub"].account_id),
                "sergey")

    def simulate_errors(self):
        print("\n" + "─" * 70)
        print("📋 СЦЕНАРИЙ 3: Ошибки")
        print("─" * 70)
        a = self.accounts
        run = self._run

        run("Пётр: снять 999999 RUB",
            Transaction(TransactionType.WITHDRAW, 999999, Currency.RUB,
                        sender_account_id=a["petr_rub"].account_id), "petr")
        run("Иван → frozen: 100 RUB",
            Transaction(TransactionType.TRANSFER_INTERNAL, 100, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["petr_frozen"].account_id), "ivan")
        run("Мария: снять 999999 RUB",
            Transaction(TransactionType.WITHDRAW, 999999, Currency.RUB,
                        sender_account_id=a["maria_rub"].account_id), "maria")

    def simulate_queue(self):
        print("\n" + "─" * 70)
        print("📋 СЦЕНАРИЙ 4: Приоритетная очередь")
        print("─" * 70)
        a = self.accounts
        tx_low = Transaction(TransactionType.DEPOSIT, 100, Currency.RUB,
                             recipient_account_id=a["anna_rub"].account_id)
        tx_normal = Transaction(TransactionType.DEPOSIT, 100, Currency.RUB,
                                recipient_account_id=a["anna_rub"].account_id)
        tx_high = Transaction(TransactionType.DEPOSIT, 100, Currency.RUB,
                              recipient_account_id=a["anna_rub"].account_id)
        self.queue.add(tx_low, priority=Priority.LOW)
        self.queue.add(tx_normal, priority=Priority.NORMAL)
        self.queue.add(tx_high, priority=Priority.HIGH)
        self.transactions.extend([tx_low, tx_normal, tx_high])
        print(f"  В очереди: {len(self.queue)} транзакций")
        for tx in self.queue.get_ready():
            print(f"    {tx.priority.name:6} — {tx}")
        for tx in [tx_high, tx_normal, tx_low]:
            cid = self.clients["anna"].client_id
            self.bank.process_with_risk_check(self.processor, tx, cid)

    def simulate_delayed_and_cancel(self):
        print("\n" + "─" * 70)
        print("📋 СЦЕНАРИЙ 5: Отложенные и отмена")
        print("─" * 70)
        a = self.accounts
        tx_delayed = Transaction(TransactionType.DEPOSIT, 200, Currency.RUB,
                                 recipient_account_id=a["anna_rub"].account_id)
        self.queue.add(tx_delayed, delay_seconds=60)
        self.transactions.append(tx_delayed)
        print(f"  ⏳ Отложена: {tx_delayed}")
        tx_cancel = Transaction(TransactionType.DEPOSIT, 300, Currency.RUB,
                                recipient_account_id=a["anna_rub"].account_id)
        self.queue.add(tx_cancel, priority=Priority.HIGH)
        self.transactions.append(tx_cancel)
        ok = self.queue.cancel(tx_cancel.transaction_id)
        print(f"  Отмена: {'успешно' if ok else 'нет'}, статус: {tx_cancel.status.value}")


# ============================================================
# ДЕНЬ 7. REPORT BUILDER
# ============================================================
class ReportBuilder:
    def __init__(self, bank, transactions, processor=None, output_dir="reports"):
        self.bank = bank
        self.transactions = transactions
        self.processor = processor
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # ---------- Текстовые отчёты ----------
    def client_report(self, client_id):
        client = self.bank._get_client(client_id)
        accounts = self.bank.get_client_accounts(client_id)
        history = self.bank.get_client_history(client_id)
        suspicious = self.bank.get_suspicious_for_client(client_id)
        total = sum((a._balance for a in accounts), Decimal("0"))

        lines = [
            "=" * 60,
            f"ОТЧЁТ ПО КЛИЕНТУ: {client.full_name}",
            "=" * 60,
            f"ID:        {client.client_id}",
            f"Статус:    {client.status.value}",
            f"Возраст:   {client.age}",
            f"Контакты:  {client.contacts}",
            "",
            f"Счета ({len(accounts)}):",
        ]
        for acc in accounts:
            lines.append(f"  • {acc}")
        lines.append(f"\nБаланс всех счетов (условный): {total}")
        lines.append(f"История операций: {len(history)}")
        for tx in history:
            lines.append(f"  {tx}")
        lines.append(f"\nПодозрительные записи ({len(suspicious)}):")
        if not suspicious:
            lines.append("  (нет)")
        else:
            for r in suspicious:
                lines.append(f"  {r}")
        return "\n".join(lines)

    def bank_report(self):
        stats = TransactionStats.compute(self.transactions)
        total = self.bank.get_total_balance()
        top = self.bank.get_top_clients(3)

        lines = [
            "=" * 60,
            f"ОТЧЁТ ПО БАНКУ: {self.bank.name}",
            "=" * 60,
            f"Клиентов:  {len(self.bank.clients)}",
            f"Счетов:    {len(self.bank.accounts)}",
            f"Общий баланс (условный): {total}",
            "",
            "Топ-3 клиента:",
        ]
        for i, row in enumerate(top, 1):
            lines.append(f"  {i}. {row['full_name']}: {row['total_balance']}")

        lines.extend([
            "",
            f"Транзакций: {stats['total']}",
            f"  выполнено: {stats['successful']}",
            f"  провалено:  {stats['failed']}",
            f"  заблокировано: {stats['blocked']}",
            "",
            "По типам:",
        ])
        for k, v in stats["by_type"].items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def risk_report(self):
        blocked = self.bank.blocked_operations
        suspicious = [r for r in self.bank.audit.records
                      if r.level in (AuditLevel.WARNING, AuditLevel.CRITICAL)]

        lines = [
            "=" * 60,
            "ОТЧЁТ ПО РИСКАМ",
            "=" * 60,
            f"Всего блокировок (HIGH): {len(blocked)}",
        ]
        for b in blocked:
            lines.append(f"  • {b['transaction_id']} (клиент {b['client_id']})")
            for reason in b["reasons"]:
                lines.append(f"      - {reason}")

        lines.append("")
        lines.append(f"Подозрительных записей: {len(suspicious)}")
        by_level = Counter(r.level.name for r in suspicious)
        for level, count in by_level.items():
            lines.append(f"  {level}: {count}")
        return "\n".join(lines)

    # ---------- JSON ----------
    def _client_to_dict(self, client):
        accounts = self.bank.get_client_accounts(client.client_id)
        return {
            "id": client.client_id,
            "full_name": client.full_name,
            "status": client.status.value,
            "age": client.age,
            "contacts": client.contacts,
            "accounts": [
                {"id": a.account_id,
                 "type": a.__class__.__name__,
                 "balance": str(a._balance),
                 "currency": a.currency.value,
                 "status": a._status.value}
                for a in accounts
            ],
        }

    def _transaction_to_dict(self, tx):
        return {
            "id": tx.transaction_id,
            "type": tx.tx_type.value,
            "amount": str(tx.amount),
            "currency": tx.currency.value,
            "commission": str(tx.commission),
            "sender": tx.sender_account_id,
            "recipient": tx.recipient_account_id,
            "status": tx.status.value,
            "risk_level": tx.risk_level.value if tx.risk_level else None,
            "rejection_reason": tx.rejection_reason,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "processed_at": tx.processed_at.isoformat() if tx.processed_at else None,
        }

    def export_to_json(self, filename="report.json"):
        data = {
            "generated_at": datetime.now().isoformat(),
            "bank": {
                "name": self.bank.name,
                "total_balance": str(self.bank.get_total_balance()),
                "clients_count": len(self.bank.clients),
                "accounts_count": len(self.bank.accounts),
            },
            "clients": [self._client_to_dict(c)
                        for c in self.bank.clients.values()],
            "transactions": [self._transaction_to_dict(tx)
                             for tx in self.transactions],
            "blocked_operations": [
                {"transaction_id": b["transaction_id"],
                 "client_id": b["client_id"],
                 "reasons": b["reasons"],
                 "timestamp": b["timestamp"].isoformat()}
                for b in self.bank.blocked_operations
            ],
        }
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    # ---------- CSV ----------
    def export_to_csv(self, filename="transactions.csv"):
        path = os.path.join(self.output_dir, filename)
        headers = ["id", "type", "amount", "currency", "commission",
                   "sender", "recipient", "status", "risk_level",
                   "created_at", "processed_at"]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for tx in self.transactions:
                writer.writerow([
                    tx.transaction_id,
                    tx.tx_type.value,
                    str(tx.amount),
                    tx.currency.value,
                    str(tx.commission),
                    tx.sender_account_id or "",
                    tx.recipient_account_id or "",
                    tx.status.value,
                    tx.risk_level.value if tx.risk_level else "",
                    tx.created_at.isoformat() if tx.created_at else "",
                    tx.processed_at.isoformat() if tx.processed_at else "",
                ])
        return path

    # ---------- Графики ----------
    def _ensure_mpl(self):
        if not HAS_MPL:
            raise InvalidOperationError(
                "matplotlib не установлен. Установи: pip install matplotlib"
            )

    def _convert(self, amount, frm, to):
        if frm == to:
            return amount
        if self.processor:
            rate = self.processor.FX_RATES.get((frm, to))
            if rate:
                return (amount * rate).quantize(Decimal("0.01"))
        return amount

    def chart_accounts_by_currency(self,
                                   filename="chart_accounts_by_currency.png"):
        self._ensure_mpl()
        counts = Counter(a.currency.value for a in self.bank.accounts.values())
        if not counts:
            raise InvalidOperationError("Нет счетов для графика")

        fig, ax = plt.subplots(figsize=(7, 6))
        ax.pie(list(counts.values()), labels=list(counts.keys()),
               autopct="%1.1f%%", startangle=90,
               colors=["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2"])
        ax.set_title(f"Счета по валютам (всего {sum(counts.values())})")
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        return path

    def chart_transactions_by_type(self,
                                   filename="chart_transactions_by_type.png"):
        self._ensure_mpl()
        counts = Counter(tx.tx_type.value for tx in self.transactions)
        if not counts:
            raise InvalidOperationError("Нет транзакций для графика")

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(list(counts.keys()), list(counts.values()),
                      color="#4C78A8", edgecolor="black")
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}",
                    ha="center", va="bottom", fontsize=10)
        ax.set_title("Транзакции по типам")
        ax.set_ylabel("Количество")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        return path

    def _delta_for(self, tx, account):
        acc_id = account.account_id
        if tx.tx_type == TransactionType.DEPOSIT:
            if tx.recipient_account_id == acc_id:
                return tx.amount
        elif tx.tx_type == TransactionType.WITHDRAW:
            if tx.sender_account_id == acc_id:
                return -tx.amount
        elif tx.tx_type in (TransactionType.TRANSFER_INTERNAL,
                            TransactionType.TRANSFER_EXTERNAL):
            delta = Decimal("0")
            if tx.sender_account_id == acc_id:
                delta -= (tx.amount + tx.commission)
            if tx.recipient_account_id == acc_id:
                delta += self._convert(tx.amount, tx.currency, account.currency)
            return delta
        elif tx.tx_type == TransactionType.CURRENCY_EXCHANGE:
            delta = Decimal("0")
            if tx.sender_account_id == acc_id:
                delta -= tx.amount
            if tx.recipient_account_id == acc_id:
                delta += self._convert(tx.amount, tx.currency, account.currency)
            return delta
        return Decimal("0")

    def _balance_series(self, account):
        acc_id = account.account_id
        relevant = [tx for tx in self.transactions
                    if tx.status == TransactionStatus.COMPLETED
                    and (tx.sender_account_id == acc_id
                         or tx.recipient_account_id == acc_id)]
        relevant.sort(key=lambda t: t.processed_at or t.created_at)

        deltas = [self._delta_for(tx, account) for tx in relevant]
        initial = account._balance - sum(deltas, Decimal("0"))
        balances = [initial]
        for d in deltas:
            balances.append(balances[-1] + d)
        return relevant, balances

    def chart_balance_movement(self, account_id,
                               filename="chart_balance.png"):
        self._ensure_mpl()
        account = self.bank._get_account(account_id)
        relevant, balances = self._balance_series(account)

        fig, ax = plt.subplots(figsize=(10, 6))
        x = list(range(len(balances)))
        y = [float(v) for v in balances]
        ax.plot(x, y, marker="o", color="#54A24B", linewidth=2, markersize=6)
        ax.axhline(y=0, color="gray", linewidth=0.8, linestyle="--")
        ax.set_title(
            f"Движение баланса: ...{account.account_id[-4:]} "
            f"({account.owner}, {account.currency.value})"
        )
        ax.set_xlabel("Индекс операции (0 = начальный)")
        ax.set_ylabel(f"Баланс, {account.currency.value}")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        if relevant:
            ax.annotate(
                f"Начальный: {balances[0]}\nТекущий: {balances[-1]}",
                xy=(0.02, 0.98), xycoords="axes fraction",
                ha="left", va="top", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3",
                          facecolor="lightyellow", alpha=0.9),
            )
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        return path

    def save_charts(self, account_id):
        self._ensure_mpl()
        return [
            self.chart_accounts_by_currency(),
            self.chart_transactions_by_type(),
            self.chart_balance_movement(account_id),
        ]


# ============================================================
# ДЕМОНСТРАЦИЯ ДНЯ 7
# ============================================================
def demo_day7():
    print("=" * 70)
    print("ДЕНЬ 7. ОТЧЁТЫ И ВИЗУАЛИЗАЦИЯ")
    print("=" * 70)

    demo = BankingDemo()
    demo.setup()
    print(f"\n Банк готов: {len(demo.bank.clients)} клиентов, "
          f"{len(demo.bank.accounts)} счетов")

    demo.simulate_routine()
    demo.simulate_suspicious()
    demo.simulate_errors()
    demo.simulate_queue()
    demo.simulate_delayed_and_cancel()

    reporter = ReportBuilder(demo.bank, demo.transactions,
                             demo.processor, output_dir="reports")

    print("\n" + "─" * 70)
    print("📄 ТЕКСТОВЫЙ ОТЧЁТ: КЛИЕНТ (Иван)")
    print("─" * 70)
    ivan = demo.clients["ivan"]
    print(reporter.client_report(ivan.client_id))

    print("\n" + "─" * 70)
    print(" ТЕКСТОВЫЙ ОТЧЁТ: БАНК")
    print("─" * 70)
    print(reporter.bank_report())

    print("\n" + "─" * 70)
    print(" ТЕКСТОВЫЙ ОТЧЁТ: РИСКИ")
    print("─" * 70)
    print(reporter.risk_report())

    print("\n" + "─" * 70)
    print(" ЭКСПОРТ")
    print("─" * 70)
    json_path = reporter.export_to_json()
    csv_path = reporter.export_to_csv()
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")

    print("\n" + "─" * 70)
    print("ГРАФИКИ")
    print("─" * 70)
    if not HAS_MPL:
        print("    matplotlib не установлен — графики пропущены")
        print("     Установи: pip install matplotlib")
    else:
        paths = reporter.save_charts(demo.accounts["ivan_rub"].account_id)
        for p in paths:
            print(f"  {p}")

    print("\n" + "=" * 70)
    print("ДЕНЬ 7 ЗАВЕРШЁН ")
    print("=" * 70)


if __name__ == "__main__":
    demo_day7()
