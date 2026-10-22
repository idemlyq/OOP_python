# ============================================================
# DAY 6 — ДЕМОНСТРАЦИОННАЯ ПРОГРАММА
# ============================================================
import uuid
import enum
import heapq
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


# ============================================================
# БАЗА ДНЕЙ 1–4 (сжатая)
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
        return f" {super().__str__()} (min={self.min_balance})"


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
    ALLOWED_ASSETS = {"stocks", "bonds", "etf"}

    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0):
        super().__init__(owner, account_id, currency, initial_balance)
        self.portfolio: Dict[str, Decimal] = {}

    def __str__(self):
        invested = sum(self.portfolio.values(), Decimal("0"))
        return f" {super().__str__()} (в портфеле: {invested})"


# ---- Транзакции (День 4) ----
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
        self.risk_level = None  # заполнит Bank

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
                    raise InvalidOperationError("нельзя отменить выполненную")
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
# ДЕНЬ 5. АУДИТ И РИСК (сжатая версия)
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

    def filter(self, level=None, category=None):
        return [r for r in self.records
                if (not level or r.level == level)
                and (not category or r.category == category)]

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
        self.history: List[Transaction] = []  # НОВОЕ в Дне 6

    def __str__(self):
        return (f" {self.full_name} (ID {self.client_id}, "
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
        self.audit.info("client", f"Зарегистрирован {c.full_name} ({c.client_id})")
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
        tx.risk_level = level  # НОВОЕ в Дне 6

        audit_level = {
            RiskLevel.LOW: AuditLevel.INFO,
            RiskLevel.MEDIUM: AuditLevel.WARNING,
            RiskLevel.HIGH: AuditLevel.CRITICAL,
        }[level]

        self.audit.log(
            audit_level, "risk",
            f"{tx.transaction_id}: риск «{level.value}»",
            {"client_id": client_id, "amount": str(tx.amount),
             "currency": tx.currency.value, "reasons": reasons},
        )

        if level == RiskLevel.HIGH:
            tx.status = TransactionStatus.CANCELLED
            tx.rejection_reason = "Заблокировано: " + "; ".join(reasons)
            self.blocked_operations.append({
                "transaction_id": tx.transaction_id,
                "client_id": client_id,
                "reasons": reasons,
                "timestamp": datetime.now(),
            })
            self.audit.critical(
                "security",
                f" Заблокирована {tx.transaction_id}",
                {"client_id": client_id, "reasons": reasons},
            )
            return False

        if level == RiskLevel.MEDIUM:
            self.audit.warning(
                "risk",
                f"  {tx.transaction_id} пропущена с пометкой",
                {"client_id": client_id, "reasons": reasons},
            )

        ok = processor.process(tx)
        if ok:
            self.risk_analyzer.record_operation(client_id, tx)
            client_obj = self._get_client(client_id)
            client_obj.history.append(tx)  # НОВОЕ в Дне 6
            self.audit.info(
                "operation",
                f" {tx.transaction_id} выполнена",
                {"client_id": client_id, "amount": str(tx.amount)},
            )
        else:
            self.audit.warning(
                "operation",
                f" {tx.transaction_id}: {tx.rejection_reason}",
                {"client_id": client_id},
            )
        return ok

    def get_client_accounts(self, client_id) -> List[AbstractAccount]:
        client = self._get_client(client_id)
        return [self.accounts[aid] for aid in client.account_numbers
                if aid in self.accounts]

    def get_client_history(self, client_id):
        return list(self._get_client(client_id).history)

    def get_suspicious_for_client(self, client_id):
        return [r for r in self.audit.records
                if r.metadata.get("client_id") == client_id
                and r.level in (AuditLevel.WARNING, AuditLevel.CRITICAL)]

    def get_clients_ranking(self):
        data = []
        for client in self.clients.values():
            total = sum(
                (self.accounts[aid]._balance
                 for aid in client.account_numbers
                 if aid in self.accounts),
                Decimal("0"),
            )
            data.append({
                "client_id": client.client_id,
                "full_name": client.full_name,
                "total_balance": total,
            })
        data.sort(key=lambda r: r["total_balance"], reverse=True)
        return data

    def get_top_clients(self, n=3):
        return self.get_clients_ranking()[:n]

    def get_total_balance(self):
        return sum((acc._balance for acc in self.accounts.values()),
                   Decimal("0"))


# ============================================================
# ДЕНЬ 6. СТАТИСТИКА
# ============================================================
class TransactionStats:
    @staticmethod
    def compute(transactions) -> dict:
        stats = {
            "total": len(transactions),
            "by_status": {}, "by_type": {}, "by_risk": {},
            "volume_by_currency": {}, "commission_by_currency": {},
            "successful": 0, "failed": 0, "blocked": 0,
        }
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
                stats["commission_by_currency"].get(cur, Decimal("0"))
                + tx.commission)

            if tx.status == TransactionStatus.COMPLETED:
                stats["successful"] += 1
            elif tx.status == TransactionStatus.FAILED:
                stats["failed"] += 1
            elif tx.status == TransactionStatus.CANCELLED:
                stats["blocked"] += 1
        return stats


# ============================================================
# ДЕНЬ 6. ОРКЕСТРАТОР ДЕМО
# ============================================================
class BankingDemo:
    def __init__(self):
        self.bank = Bank("Демо-Банк")
        self.processor = TransactionProcessor(self.bank)
        self.queue = TransactionQueue()
        self.transactions: List[Transaction] = []
        self.clients: Dict[str, Client] = {}
        self.accounts: Dict[str, AbstractAccount] = {}

    # ---------- Setup ----------
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

        c = self.clients
        a = self.accounts
        a["ivan_rub"] = self.bank.open_account(c["ivan"].client_id, "basic",
            currency=Currency.RUB, initial_balance=50000)
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
        # Замороженный счёт — для теста ошибок
        a["petr_frozen"] = self.bank.open_account(c["petr"].client_id, "basic",
            currency=Currency.RUB, initial_balance=500)
        self.bank.freeze_account(c["petr"].client_id, a["petr_frozen"].account_id)

    # ---------- Одна операция ----------
    def _run(self, label, tx, client_key):
        self.transactions.append(tx)
        cid = self.clients[client_key].client_id
        level, reasons = self.bank.risk_analyzer.assess(cid, tx)
        ok = self.bank.process_with_risk_check(self.processor, tx, cid)
        marker = "+" if ok else "-"
        print(f"  {marker} {label} [риск: {level.value}]")
        if not ok and reasons:
            print(f"      └─ {'; '.join(reasons)}")

    # ---------- Сценарий 1: обычные ----------
    def simulate_routine(self):
        print("\n" + "─" * 70)
        print(" СЦЕНАРИЙ 1: Обычные операции")
        print("─" * 70)
        a, c = self.accounts, self.clients
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
        run("Иван → Мария: 500 RUB (первый перевод)",
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
        run("Иван: внешний перевод 100 USD (комиссия 1%)",
            Transaction(TransactionType.TRANSFER_EXTERNAL, 100, Currency.USD,
                        sender_account_id=a["ivan_usd"].account_id,
                        recipient_account_id="EXT-BANK-1"), "ivan")
        run("Анна: депозит 1000 RUB",
            Transaction(TransactionType.DEPOSIT, 1000, Currency.RUB,
                        recipient_account_id=a["anna_rub"].account_id), "anna")
        run("Сергей: депозит 500 RUB",
            Transaction(TransactionType.DEPOSIT, 500, Currency.RUB,
                        recipient_account_id=a["sergey_rub"].account_id), "sergey")

    # ---------- Сценарий 2: подозрительные ----------
    def simulate_suspicious(self):
        print("\n" + "─" * 70)
        print(" СЦЕНАРИЙ 2: Подозрительные операции (риск-анализ)")
        print("─" * 70)
        a, c = self.accounts, self.clients
        run = self._run

        # MEDIUM: крупная сумма, но получатель уже знаком
        run("Иван → Мария: 150000 RUB (крупная, но получатель знаком)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 150000, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["maria_rub"].account_id), "ivan")

        # HIGH: крупная + новый получатель → 3 балла → блок
        run("Иван → Елена: 200000 RUB (крупная + новый)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 200000, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["elena_rub"].account_id), "ivan")

        # HIGH: крупная + новый от другого клиента
        run("Пётр → Анна: 120000 RUB (крупная + новый)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 120000, Currency.RUB,
                        sender_account_id=a["petr_rub"].account_id,
                        recipient_account_id=a["anna_rub"].account_id), "petr")

        # MEDIUM: ночь + новый получатель
        self.bank._current_hour = 3
        run(" Сергей → Анна: 500 RUB (ночь + новый)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 500, Currency.RUB,
                        sender_account_id=a["sergey_rub"].account_id,
                        recipient_account_id=a["anna_rub"].account_id), "sergey")
        self.bank._current_hour = None

        # MEDIUM: частые операции (3-я, 4-я за минуту)
        for i in range(1, 5):
            run(f"Сергей: быстрый депозит #{i} 100 RUB",
                Transaction(TransactionType.DEPOSIT, 100, Currency.RUB,
                            recipient_account_id=a["sergey_rub"].account_id),
                "sergey")

    # ---------- Сценарий 3: ошибки ----------
    def simulate_errors(self):
        print("\n" + "─" * 70)
        print("📋 СЦЕНАРИЙ 3: Ошибочные операции")
        print("─" * 70)
        a, c = self.accounts, self.clients
        run = self._run

        run("Пётр: снять 999999 RUB (больше баланса)",
            Transaction(TransactionType.WITHDRAW, 999999, Currency.RUB,
                        sender_account_id=a["petr_rub"].account_id), "petr")

        run("Иван → Пётр(frozen): 100 RUB",
            Transaction(TransactionType.TRANSFER_INTERNAL, 100, Currency.RUB,
                        sender_account_id=a["ivan_rub"].account_id,
                        recipient_account_id=a["petr_frozen"].account_id), "ivan")

        run("Мария: снять 999999 RUB",
            Transaction(TransactionType.WITHDRAW, 999999, Currency.RUB,
                        sender_account_id=a["maria_rub"].account_id), "maria")

        run("Иван: RUB-транзакция с USD-счёта (валюта не совпадает)",
            Transaction(TransactionType.WITHDRAW, 100, Currency.RUB,
                        sender_account_id=a["ivan_usd"].account_id), "ivan")

        run("Анна → Елена: 100 EUR (у Елены нет EUR-счёта)",
            Transaction(TransactionType.TRANSFER_INTERNAL, 100, Currency.EUR,
                        sender_account_id=a["anna_eur"].account_id,
                        recipient_account_id=a["elena_usd"].account_id), "anna")

    # ---------- Сценарий 4: очередь ----------
    def simulate_queue(self):
        print("\n" + "─" * 70)
        print("📋 СЦЕНАРИЙ 4: Приоритетная очередь")
        print("─" * 70)
        a, c = self.accounts, self.clients

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
        print("  Порядок обработки (HIGH первым):")
        for tx in self.queue.get_ready():
            print(f"    {tx.priority.name:6} — {tx}")

        # Теперь исполняем их через риск-проверку
        for tx in [tx_high, tx_normal, tx_low]:
            cid = c["anna"].client_id
            ok = self.bank.process_with_risk_check(self.processor, tx, cid)
            print(f"    {'+' if ok else '-'} {tx}")

    # ---------- Сценарий 5: отложенные и отмена ----------
    def simulate_delayed_and_cancel(self):
        print("\n" + "─" * 70)
        print(" СЦЕНАРИЙ 5: Отложенная операция и отмена")
        print("─" * 70)
        a = self.accounts

        tx_delayed = Transaction(TransactionType.DEPOSIT, 200, Currency.RUB,
                                 recipient_account_id=a["anna_rub"].account_id)
        self.queue.add(tx_delayed, delay_seconds=60)
        self.transactions.append(tx_delayed)
        print(f"  Отложена на 60с: {tx_delayed}")
        print(f"      scheduled_at: {tx_delayed.scheduled_at.strftime('%H:%M:%S')}, "
              f"статус: {tx_delayed.status.value}")

        tx_cancel = Transaction(TransactionType.DEPOSIT, 300, Currency.RUB,
                                recipient_account_id=a["anna_rub"].account_id)
        self.queue.add(tx_cancel, priority=Priority.HIGH)
        self.transactions.append(tx_cancel)
        ok = self.queue.cancel(tx_cancel.transaction_id)
        print(f"  Отмена: {'успешно' if ok else 'не найдено'}, "
              f"статус: {tx_cancel.status.value}")

    # ---------- Пользовательские сценарии ----------
    def show_user_scenarios(self):
        print("\n" + "═" * 70)
        print(" СЦЕНАРИИ КЛИЕНТА: Иван Петров")
        print("═" * 70)
        client = self.clients["ivan"]

        print(f"\n {client}")

        print("\n Счета:")
        for acc in self.bank.get_client_accounts(client.client_id):
            print(f"  {acc}")

        print(f"\n История операций ({len(client.history)}):")
        for tx in client.history:
            print(f"  {tx}")

        print("\n Подозрительные записи аудита:")
        records = self.bank.get_suspicious_for_client(client.client_id)
        if not records:
            print("  (нет)")
        for r in records:
            print(f"  {r}")

    # ---------- Отчёты ----------
    def show_reports(self):
        print("\n" + "═" * 70)
        print("📊 ИТОГОВЫЕ ОТЧЁТЫ")
        print("═" * 70)

        print("\n🏆 Топ-3 клиента по общему балансу:")
        for i, row in enumerate(self.bank.get_top_clients(3), 1):
            print(f"  {i}. {row['full_name']}: {row['total_balance']}")

        stats = TransactionStats.compute(self.transactions)
        print(f"\n Транзакций: {stats['total']} "
              f"( {stats['successful']},  {stats['failed']}, "
              f" {stats['blocked']})")

        print("\n  По типам:")
        for k, v in stats["by_type"].items():
            print(f"    {k}: {v}")

        print("\n  По уровню риска:")
        for k, v in stats["by_risk"].items():
            print(f"    {k}: {v}")

        print("\n  Объёмы (в валюте операции) и комиссии:")
        for cur, vol in stats["volume_by_currency"].items():
            comm = stats["commission_by_currency"][cur]
            print(f"    {cur}: объём {vol}, комиссии {comm}")

        print("\n Заблокированных операций (HIGH): "
              f"{len(self.bank.blocked_operations)}")
        for b in self.bank.blocked_operations:
            print(f"  {b['transaction_id']} — {'; '.join(b['reasons'])}")

        print(f"\n Общий баланс всех счетов: {self.bank.get_total_balance()}")
        print("   (  условная сумма: разные валюты сложены без конвертации)")

        print(f"\n Всего записей в аудите: {len(self.bank.audit)}")

    # ---------- Точка входа ----------
    def run(self):
        print("=" * 70)
        print("ДЕНЬ 6. ДЕМОНСТРАЦИОННАЯ ПРОГРАММА")
        print("=" * 70)
        self.setup()
        print(f"\n Создано клиентов: {len(self.bank.clients)}")
        print(f" Открыто счетов:   {len(self.bank.accounts)}")

        self.simulate_routine()
        self.simulate_suspicious()
        self.simulate_errors()
        self.simulate_queue()
        self.simulate_delayed_and_cancel()
        self.show_user_scenarios()
        self.show_reports()

        print("\n" + "=" * 70)
        print("ДЕНЬ 6 ЗАВЕРШЁН ")
        print("=" * 70)


if __name__ == "__main__":
    BankingDemo().run()
