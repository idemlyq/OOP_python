#DAY 5 — АУДИТ И РИСК-АНАЛИЗ 
import uuid
import enum
import heapq
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


# БАЗА ДНЕЙ 1–4 (сжатая)
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
            raise InvalidOperationError("сумма должна быть > 0")
        return v

    def _ensure_active(self):
        if self._status == AccountStatus.FROZEN:
            raise AccountFrozenError(f"счёт {self.account_id} заморожен")
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(f"счёт {self.account_id} закрыт")

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
            raise InsufficientFundsError(f"превышен овердрафт {self.overdraft_limit}")
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
        return f"📊 {super().__str__()} (в портфеле: {invested})"


class ClientStatus(enum.Enum):
    ACTIVE = "активный"
    BLOCKED = "заблокирован"


class Client:
    def __init__(self, full_name, birth_year, contacts, pin, client_id=None):
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
        self.client_id = client_id or ("C" + uuid.uuid4().hex[:6].upper())
        self.status = ClientStatus.ACTIVE
        self.account_numbers: List[str] = []
        self.failed_attempts = 0
        self.suspicious_actions: List[str] = []


# ДЕНЬ 4. ТРАНЗАКЦИИ (сжатая версия)
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
            sender = self.bank._get_account(tx.sender_account_id)
            if sender._status == AccountStatus.FROZEN:
                raise AccountFrozenError("отправитель заморожен")
            if sender._status == AccountStatus.CLOSED:
                raise AccountClosedError("отправитель закрыт")
            if sender.currency != tx.currency:
                raise InvalidOperationError("валюта не совпадает")
            if tx.tx_type in (TransactionType.TRANSFER_INTERNAL,
                              TransactionType.TRANSFER_EXTERNAL):
                if not isinstance(sender, PremiumAccount) and sender._balance < 0:
                    raise InvalidOperationError("перевод при минусе запрещён")
        if (tx.recipient_account_id
                and tx.tx_type != TransactionType.TRANSFER_EXTERNAL):
            recipient = self.bank._get_account(tx.recipient_account_id)
            if recipient._status == AccountStatus.FROZEN:
                raise AccountFrozenError("получатель заморожен")
            if recipient._status == AccountStatus.CLOSED:
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
            total = tx.amount + tx.commission
            self.bank._get_account(tx.sender_account_id).withdraw(total)
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
        sender = self.bank._get_account(tx.sender_account_id)
        recipient = self.bank._get_account(tx.recipient_account_id)
        recipient_amount = self._convert(tx.amount, tx.currency, recipient.currency)
        sender.withdraw(tx.amount + tx.commission)
        recipient.deposit(recipient_amount)

    def _exchange(self, tx):
        sender = self.bank._get_account(tx.sender_account_id)
        recipient = self.bank._get_account(tx.recipient_account_id)
        converted = self._convert(tx.amount, tx.currency, recipient.currency)
        sender.withdraw(tx.amount)
        recipient.deposit(converted)

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


# ДЕНЬ 5. АУДИТ
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
        record = AuditRecord(level, category, message, metadata)
        self.records.append(record)
        return record

    def info(self, category, message, **metadata):
        return self.log(AuditLevel.INFO, category, message, metadata)

    def warning(self, category, message, **metadata):
        return self.log(AuditLevel.WARNING, category, message, metadata)

    def critical(self, category, message, **metadata):
        return self.log(AuditLevel.CRITICAL, category, message, metadata)

    def filter(self, level=None, category=None, since=None):
        result = []
        for r in self.records:
            if level and r.level != level:
                continue
            if category and r.category != category:
                continue
            if since and r.timestamp < since:
                continue
            result.append(r)
        return result

    def save_to_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for r in self.records:
                f.write(str(r) + "\n")

    def __len__(self):
        return len(self.records)


# ============================================================
# ДЕНЬ 5. РИСК-АНАЛИЗ
# ============================================================
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
        score = 0
        reasons = []

        threshold = self.LARGE_AMOUNT_THRESHOLD.get(tx.currency)
        if threshold and tx.amount >= threshold:
            score += 2
            reasons.append(f"Крупная сумма: {tx.amount} {tx.currency.value}")

        now = datetime.now()
        cutoff = now - timedelta(seconds=self.FREQUENCY_WINDOW)
        recent = [t for t in self.history.get(client_id, []) if t >= cutoff]
        if len(recent) >= self.FREQUENCY_MAX:
            score += 2
            reasons.append(f"Частые операции: {len(recent)} за "
                           f"{self.FREQUENCY_WINDOW}с")

        if tx.tx_type in (TransactionType.TRANSFER_INTERNAL,
                          TransactionType.TRANSFER_EXTERNAL):
            known = self.known_recipients.get(client_id, set())
            if tx.recipient_account_id and tx.recipient_account_id not in known:
                score += 1
                reasons.append(f"Новый получатель: ...{tx.recipient_account_id[-4:]}")

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
                tx.recipient_account_id
            )

    def client_risk_profile(self, client_id):
        history = self.history.get(client_id, [])
        return {
            "operations_count": len(history),
            "known_recipients": len(self.known_recipients.get(client_id, set())),
            "last_operation": max(history) if history else None,
        }


# ============================================================
# ДЕНЬ 5. ОТЧЁТЫ
# ============================================================
class AuditReport:
    @staticmethod
    def suspicious_operations(bank, min_level=AuditLevel.WARNING):
        return [r for r in bank.audit.records
                if r.level.value >= min_level.value]

    @staticmethod
    def client_risk_profile(bank, client_id):
        client = bank._get_client(client_id)
        profile = bank.risk_analyzer.client_risk_profile(client_id)
        alerts = [r for r in bank.audit.records
                  if r.metadata.get("client_id") == client_id
                  and r.level in (AuditLevel.WARNING, AuditLevel.CRITICAL)]
        return {
            "client": client.full_name,
            "client_id": client.client_id,
            "status": client.status.value,
            "operations": profile["operations_count"],
            "known_recipients": profile["known_recipients"],
            "last_operation": profile["last_operation"],
            "alerts_count": len(alerts),
        }

    @staticmethod
    def error_statistics(processor):
        stats: Dict[str, int] = {}
        for err in processor.error_log:
            key = err["error_type"]
            stats[key] = stats.get(key, 0) + 1
        return stats

    @staticmethod
    def print_suspicious(bank):
        records = AuditReport.suspicious_operations(bank)
        print(f"  Всего подозрительных записей: {len(records)}")
        for r in records:
            print(f"  {r}")


# ============================================================
# БАНК (расширенный аудитом и риском)
# ============================================================
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

    def _get_client(self, client_id):
        if client_id not in self.clients:
            raise InvalidOperationError(f"клиент {client_id} не найден")
        return self.clients[client_id]

    def _get_account(self, account_id):
        if account_id not in self.accounts:
            raise InvalidOperationError(f"счёт {account_id} не найден")
        return self.accounts[account_id]

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
        self.audit.info("account",
                        f"Открыт {account_type} {acc.account_id} для {client.full_name}")
        return acc

    def freeze_account(self, client_id, account_id):
        self._get_client(client_id)
        self._get_account(account_id).freeze()
        self.audit.warning("account", f"Счёт {account_id} заморожен")

    def process_with_risk_check(self, processor, tx, client_id) -> bool:
        level, reasons = self.risk_analyzer.assess(client_id, tx)

        audit_level = {
            RiskLevel.LOW: AuditLevel.INFO,
            RiskLevel.MEDIUM: AuditLevel.WARNING,
            RiskLevel.HIGH: AuditLevel.CRITICAL,
        }[level]

        self.audit.log(
            audit_level, "risk",
            f"{tx.transaction_id}: риск «{level.value}»",
            {"client_id": client_id,
             "amount": str(tx.amount),
             "currency": tx.currency.value,
             "reasons": reasons},
        )

        if level == RiskLevel.HIGH:
            tx.status = TransactionStatus.CANCELLED
            tx.rejection_reason = "Заблокировано риск-анализом: " + "; ".join(reasons)
            self.blocked_operations.append({
                "transaction_id": tx.transaction_id,
                "client_id": client_id,
                "reasons": reasons,
                "timestamp": datetime.now(),
            })
            self.audit.critical(
                "security",
                f" Заблокирована {tx.transaction_id} клиента {client_id}",
                {"reasons": reasons},
            )
            return False

        if level == RiskLevel.MEDIUM:
            self.audit.warning(
                "risk",
                f"  Подозрительная {tx.transaction_id} пропущена с пометкой",
                {"reasons": reasons},
            )

        ok = processor.process(tx)
        if ok:
            self.risk_analyzer.record_operation(client_id, tx)
            self.audit.info(
                "operation",
                f" {tx.transaction_id} выполнена",
                {"amount": str(tx.amount), "commission": str(tx.commission)},
            )
        else:
            self.audit.warning(
                "operation",
                f" {tx.transaction_id} провалена: {tx.rejection_reason}",
            )
        return ok

    def search_accounts(self, owner=None, currency=None, status=None):
        result = []
        for acc in self.accounts.values():
            if owner and owner.lower() not in acc.owner.lower():
                continue
            if currency and acc.currency != currency:
                continue
            if status and acc._status != status:
                continue
            result.append(acc)
        return result


# ============================================================
# ДЕМОНСТРАЦИЯ ДНЯ 5
# ============================================================
def demo_day5() -> None:
    print("=" * 70)
    print("ДЕНЬ 5. АУДИТ И РИСК-АНАЛИЗ")
    print("=" * 70)

    bank = Bank("Bank Day 5")
    ivan = bank.add_client("Иван Петров", 1990, {"phone": "+7-900"}, "1111")
    maria = bank.add_client("Мария Сидорова", 1985, {"phone": "+7-901"}, "2222")
    petr = bank.add_client("Пётр Новиков", 1988, {"phone": "+7-902"}, "3333")

    ivan_rub = bank.open_account(ivan.client_id, "basic",
                                 currency=Currency.RUB, initial_balance=500000)
    ivan_usd = bank.open_account(ivan.client_id, "premium",
                                 currency=Currency.USD, initial_balance=5000)
    maria_rub = bank.open_account(maria.client_id, "basic",
                                  currency=Currency.RUB, initial_balance=10000)
    petr_rub = bank.open_account(petr.client_id, "savings",
                                 currency=Currency.RUB,
                                 initial_balance=1000, min_balance=0)

    processor = TransactionProcessor(bank)

    def run(label, tx, client_id):
        print(f"\n{label}")
        ok = bank.process_with_risk_check(processor, tx, client_id)
        print(f"  {'ВЫПОЛНЕНА' if ok else 'ОТКЛОНЕНА'}: {tx}")

    print("\n--- 1. Обычные операции (LOW) ---")
    run("Обычный депозит 1000 RUB:",
        Transaction(TransactionType.DEPOSIT, 1000, Currency.RUB,
                    recipient_account_id=maria_rub.account_id),
        maria.client_id)

    run("Первый перевод Марии → Пётр (новый получатель, но маленький):",
        Transaction(TransactionType.TRANSFER_INTERNAL, 500, Currency.RUB,
                    sender_account_id=maria_rub.account_id,
                    recipient_account_id=petr_rub.account_id),
        maria.client_id)

    run("Повторный перевод Марии → Пётр (уже знакомый):",
        Transaction(TransactionType.TRANSFER_INTERNAL, 500, Currency.RUB,
                    sender_account_id=maria_rub.account_id,
                    recipient_account_id=petr_rub.account_id),
        maria.client_id)

    print("\n--- 2. Крупная сумма (MEDIUM) ---")
    run("Крупный перевод Ивана 200000 RUB → Мария:",
        Transaction(TransactionType.TRANSFER_INTERNAL, 200000, Currency.RUB,
                    sender_account_id=ivan_rub.account_id,
                    recipient_account_id=maria_rub.account_id),
        ivan.client_id)

    print("\n--- 3. Крупный + новый получатель (HIGH → блок) ---")
    run("Крупный перевод Ивана 300000 RUB → Пётр (первый раз):",
        Transaction(TransactionType.TRANSFER_INTERNAL, 300000, Currency.RUB,
                    sender_account_id=ivan_rub.account_id,
                    recipient_account_id=petr_rub.account_id),
        ivan.client_id)

    print("\n--- 4. Ночь + новый получатель (MEDIUM) ---")
    bank._current_hour = 3
    run("Ночной перевод Ивана → Мария (новый получатель для него):",
        Transaction(TransactionType.TRANSFER_INTERNAL, 1000, Currency.RUB,
                    sender_account_id=ivan_rub.account_id,
                    recipient_account_id=maria_rub.account_id),
        ivan.client_id)
    bank._current_hour = None

    print("\n--- 5. Частые операции (MEDIUM на 4-й) ---")
    for i in range(1, 5):
        run(f"Быстрая операция #{i} (Пётр, депозит 100):",
            Transaction(TransactionType.DEPOSIT, 100, Currency.RUB,
                        recipient_account_id=petr_rub.account_id),
            petr.client_id)

    print("\n--- 6. ОТЧЁТЫ ---")

    print("\n📊 Подозрительные операции:")
    AuditReport.print_suspicious(bank)

    print("\n👤 Риск-профиль Ивана:")
    profile = AuditReport.client_risk_profile(bank, ivan.client_id)
    for k, v in profile.items():
        print(f"  {k}: {v}")

    print("\n👤 Риск-профиль Петра:")
    profile = AuditReport.client_risk_profile(bank, petr.client_id)
    for k, v in profile.items():
        print(f"  {k}: {v}")

    print("\n Статистика ошибок процессора:")
    stats = AuditReport.error_statistics(processor)
    if not stats:
        print("  (ошибок нет)")
    for etype, cnt in stats.items():
        print(f"  {etype}: {cnt}")

    print(f"\n Заблокированных операций: {len(bank.blocked_operations)}")
    for b in bank.blocked_operations:
        print(f"  {b['transaction_id']} ({b['client_id']}): {b['reasons']}")

    print(f"\n Всего записей в аудите: {len(bank.audit)}")
    print(f"   INFO:     {len(bank.audit.filter(level=AuditLevel.INFO))}")
    print(f"   WARNING:  {len(bank.audit.filter(level=AuditLevel.WARNING))}")
    print(f"   CRITICAL: {len(bank.audit.filter(level=AuditLevel.CRITICAL))}")

    file_path = "audit_log.txt"
    bank.audit.save_to_file(file_path)
    print(f"\n Аудит сохранён в '{file_path}'")

    print("\n" + "=" * 70)
    print("ДЕНЬ 5 ЗАВЕРШЁН")
    print("=" * 70)


if __name__ == "__main__":
    demo_day5()
