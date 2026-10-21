# DAY 4 — СИСТЕМА ТРАНЗАКЦИЙ
import uuid
import enum
import heapq
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List


# БАЗА ДНЯ 1
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
        self.account_id = account_id or self._generate_id()
        self._balance = Decimal("0")
        self._status = AccountStatus.ACTIVE
        self.currency = currency

    @abstractmethod
    def deposit(self, amount) -> None: ...
    @abstractmethod
    def withdraw(self, amount) -> None: ...
    @abstractmethod
    def get_account_info(self) -> str: ...

    @staticmethod
    def _generate_id() -> str:
        return uuid.uuid4().hex[:8].upper()


class BankAccount(AbstractAccount):
    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0):
        if not owner or not isinstance(owner, str) or not owner.strip():
            raise InvalidOperationError("Имя владельца не может быть пустым")
        if not isinstance(currency, Currency):
            raise InvalidOperationError("Некорректная валюта")
        super().__init__(owner.strip(), account_id, currency)
        if initial_balance:
            self.deposit(initial_balance)

    @staticmethod
    def _validate_amount(amount) -> Decimal:
        if isinstance(amount, bool):
            raise InvalidOperationError("Сумма должна быть числом, не bool")
        try:
            value = Decimal(str(amount))
        except Exception:
            raise InvalidOperationError(f"Некорректная сумма: {amount!r}")
        if value <= 0:
            raise InvalidOperationError("Сумма должна быть больше нуля")
        return value

    def _ensure_active(self) -> None:
        if self._status == AccountStatus.FROZEN:
            raise AccountFrozenError(f"Счёт {self.account_id} заморожен")
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(f"Счёт {self.account_id} закрыт")

    def deposit(self, amount) -> None:
        self._ensure_active()
        self._balance += self._validate_amount(amount)

    def withdraw(self, amount) -> None:
        self._ensure_active()
        value = self._validate_amount(amount)
        if value > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств: {self._balance} < {value}"
            )
        self._balance -= value

    def freeze(self) -> None:
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError("Нельзя заморозить закрытый счёт")
        self._status = AccountStatus.FROZEN

    def activate(self) -> None:
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError("Нельзя активировать закрытый счёт")
        self._status = AccountStatus.ACTIVE

    def close(self) -> None:
        if self._balance != 0:
            raise InvalidOperationError("Нельзя закрыть счёт с балансом ≠ 0")
        self._status = AccountStatus.CLOSED

    def get_account_info(self) -> str:
        return (
            f"Владелец: {self.owner}\n"
            f"Счёт: ...{self.account_id[-4:]}\n"
            f"Статус: {self._status.value}\n"
            f"Баланс: {self._balance} {self.currency.value}"
        )

    def __str__(self) -> str:
        return (f"[{self.__class__.__name__}] {self.owner} | "
                f"...{self.account_id[-4:]} | {self._status.value} | "
                f"{self._balance} {self.currency.value}")


# ДЕНЬ 2
class SavingsAccount(BankAccount):
    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0, min_balance=0, monthly_rate=0.01):
        super().__init__(owner, account_id, currency, initial_balance)
        if min_balance < 0:
            raise InvalidOperationError("min_balance < 0")
        if not (Decimal("0") <= Decimal(str(monthly_rate)) <= Decimal("1")):
            raise InvalidOperationError("Ставка вне 0..1")
        self.min_balance = Decimal(str(min_balance))
        self.monthly_rate = Decimal(str(monthly_rate))

    def withdraw(self, amount) -> None:
        value = self._validate_amount(amount)
        self._ensure_active()
        if self._balance - value < self.min_balance:
            raise InsufficientFundsError(
                f"Остаток станет ниже минимума {self.min_balance}"
            )
        self._balance -= value

    def apply_monthly_interest(self) -> Decimal:
        self._ensure_active()
        interest = (self._balance * self.monthly_rate).quantize(Decimal("0.01"))
        self._balance += interest
        return interest

    def __str__(self) -> str:
        return f"💎 {super().__str__()} (min={self.min_balance})"


class PremiumAccount(BankAccount):
    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0, overdraft_limit=50000, commission=0.005):
        super().__init__(owner, account_id, currency, initial_balance)
        if overdraft_limit < 0:
            raise InvalidOperationError("Овердрафт < 0")
        if not (Decimal("0") <= Decimal(str(commission)) < Decimal("1")):
            raise InvalidOperationError("Комиссия вне 0..1")
        self.overdraft_limit = Decimal(str(overdraft_limit))
        self.commission = Decimal(str(commission))

    def withdraw(self, amount) -> None:
        value = self._validate_amount(amount)
        self._ensure_active()
        commission = (value * self.commission).quantize(Decimal("0.01"))
        total = value + commission
        if self._balance - total < -self.overdraft_limit:
            raise InsufficientFundsError(
                f"Превышен овердрафт: доступно "
                f"{self._balance + self.overdraft_limit}, требуется {total}"
            )
        self._balance -= total

    def __str__(self) -> str:
        return f"🏆 {super().__str__()} (overdraft={self.overdraft_limit})"


class InvestmentAccount(BankAccount):
    ALLOWED_ASSETS = {"stocks", "bonds", "etf"}

    def __init__(self, owner, account_id=None, currency=Currency.RUB,
                 initial_balance=0):
        super().__init__(owner, account_id, currency, initial_balance)
        self.portfolio: Dict[str, Decimal] = {}

    def _add_to_portfolio(self, asset_type: str, amount: Decimal) -> None:
        if asset_type not in self.ALLOWED_ASSETS:
            raise InvalidOperationError(f"Актив {asset_type!r} не разрешён")
        self.portfolio[asset_type] = (
            self.portfolio.get(asset_type, Decimal("0")) + amount
        )

    def invest(self, asset_type: str, amount) -> None:
        value = self._validate_amount(amount)
        self._ensure_active()
        if value > self._balance:
            raise InsufficientFundsError(
                f"Свободно {self._balance}, запрошено {value}"
            )
        self._add_to_portfolio(asset_type, value)
        self._balance -= value

    def withdraw(self, amount) -> None:
        super().withdraw(amount)

    def project_yearly_growth(self, growth_rates) -> Dict[str, Decimal]:
        result, total = {}, Decimal("0")
        for asset, amount in self.portfolio.items():
            rate = Decimal(str(growth_rates.get(asset, 0)))
            growth = (amount * rate).quantize(Decimal("0.01"))
            result[asset] = growth
            total += growth
        result["TOTAL"] = total
        return result

    def __str__(self) -> str:
        invested = sum(self.portfolio.values(), Decimal("0"))
        return f"📊 {super().__str__()} (в портфеле: {invested})"


# ДЕНЬ 3
class ClientStatus(enum.Enum):
    ACTIVE = "активный"
    BLOCKED = "заблокирован"


class Client:
    def __init__(self, full_name, birth_year, contacts, pin, client_id=None):
        if not full_name or not full_name.strip():
            raise InvalidOperationError("ФИО не может быть пустым")
        age = datetime.now().year - birth_year
        if age < 18:
            raise InvalidOperationError(
                f"Клиент несовершеннолетний: {age} лет"
            )
        if not isinstance(pin, str) or not pin.isdigit() or len(pin) != 4:
            raise InvalidOperationError("PIN — 4 цифры")
        if not isinstance(contacts, dict):
            raise InvalidOperationError("contacts должен быть словарём")
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

    def mark_suspicious(self, reason: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.suspicious_actions.append(f"[{stamp}] {reason}")

    def __str__(self) -> str:
        accs = ", ".join(self.account_numbers) or "нет"
        return (f"👤 {self.full_name} (ID {self.client_id}, {self.age} лет, "
                f"{self.status.value}), счета: {accs}")


class Bank:
    MAX_FAILED_ATTEMPTS = 3
    NIGHT_START = 0
    NIGHT_END = 5

    ACCOUNT_TYPES = {
        "basic": BankAccount,
        "savings": SavingsAccount,
        "premium": PremiumAccount,
        "investment": InvestmentAccount,
    }

    def __init__(self, name: str):
        self.name = name
        self.clients: Dict[str, Client] = {}
        self.accounts: Dict[str, AbstractAccount] = {}
        self._current_hour: int | None = None

    def _get_client(self, client_id: str) -> Client:
        if client_id not in self.clients:
            raise InvalidOperationError(f"Клиент {client_id} не найден")
        return self.clients[client_id]

    def _get_account(self, account_id: str) -> AbstractAccount:
        if account_id not in self.accounts:
            raise InvalidOperationError(f"Счёт {account_id} не найден")
        return self.accounts[account_id]

    def _is_night(self) -> bool:
        hour = (self._current_hour if self._current_hour is not None
                else datetime.now().hour)
        return self.NIGHT_START <= hour < self.NIGHT_END

    def _check_night_restriction(self) -> None:
        if self._is_night():
            raise InvalidOperationError("Операции запрещены с 00:00 до 05:00")

    def add_client(self, full_name, birth_year, contacts, pin) -> Client:
        client = Client(full_name, birth_year, contacts, pin)
        self.clients[client.client_id] = client
        return client

    def open_account(self, client_id, account_type="basic",
                     **kwargs) -> AbstractAccount:
        client = self._get_client(client_id)
        if client.status == ClientStatus.BLOCKED:
            raise InvalidOperationError("Клиент заблокирован")
        cls = self.ACCOUNT_TYPES.get(account_type)
        if cls is None:
            raise InvalidOperationError(
                f"Неизвестный тип: {account_type!r}. "
                f"Доступны: {list(self.ACCOUNT_TYPES)}"
            )
        account = cls(client.full_name, **kwargs)
        self.accounts[account.account_id] = account
        client.account_numbers.append(account.account_id)
        return account

    def close_account(self, client_id, account_id) -> None:
        client = self._get_client(client_id)
        if account_id not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")
        self._get_account(account_id).close()
        client.account_numbers.remove(account_id)
        del self.accounts[account_id]

    def freeze_account(self, client_id, account_id) -> None:
        client = self._get_client(client_id)
        if account_id not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")
        self._get_account(account_id).freeze()

    def unfreeze_account(self, client_id, account_id) -> None:
        client = self._get_client(client_id)
        if account_id not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")
        self._get_account(account_id).activate()

    def authenticate_client(self, client_id: str, pin: str) -> bool:
        client = self._get_client(client_id)
        if client.status == ClientStatus.BLOCKED:
            raise InvalidOperationError(
                f"Клиент {client.full_name} заблокирован"
            )
        if pin == client.pin:
            client.failed_attempts = 0
            return True
        client.failed_attempts += 1
        client.mark_suspicious(
            f"Неверный PIN (попытка {client.failed_attempts})"
        )
        if client.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            client.status = ClientStatus.BLOCKED
            client.mark_suspicious(
                f"Заблокирован после {client.failed_attempts} попыток"
            )
            raise InvalidOperationError(
                f"Превышено число попыток. {client.full_name} заблокирован."
            )
        remaining = self.MAX_FAILED_ATTEMPTS - client.failed_attempts
        raise InvalidOperationError(
            f"Неверный PIN. Осталось попыток: {remaining}"
        )

    def deposit(self, client_id, account_id, amount) -> None:
        self._check_night_restriction()
        client = self._get_client(client_id)
        if client.status == ClientStatus.BLOCKED:
            raise InvalidOperationError("Клиент заблокирован")
        if account_id not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")
        self._get_account(account_id).deposit(amount)

    def withdraw(self, client_id, account_id, amount) -> None:
        self._check_night_restriction()
        client = self._get_client(client_id)
        if client.status == ClientStatus.BLOCKED:
            raise InvalidOperationError("Клиент заблокирован")
        if account_id not in client.account_numbers:
            raise InvalidOperationError("Счёт не принадлежит клиенту")
        self._get_account(account_id).withdraw(amount)

    def search_accounts(self, owner=None, currency=None,
                        status=None) -> List[AbstractAccount]:
        results = []
        for acc in self.accounts.values():
            if owner and owner.lower() not in acc.owner.lower():
                continue
            if currency and acc.currency != currency:
                continue
            if status and acc._status != status:
                continue
            results.append(acc)
        return results

    def get_total_balance(self) -> Decimal:
        return sum(
            (acc._balance for acc in self.accounts.values()),
            Decimal("0"),
        )

    def get_clients_ranking(self) -> List[Dict]:
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


# ДЕНЬ 4. ТРАНЗАКЦИИ
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
        self.rejection_reason: str | None = None
        self.created_at = datetime.now()
        self.scheduled_at: datetime | None = None
        self.processed_at: datetime | None = None
        self.retry_count = 0
        self.max_retries = max_retries
        self.priority = Priority.NORMAL

    def __str__(self) -> str:
        return (f"[{self.transaction_id}] {self.tx_type.value} "
                f"{self.amount} {self.currency.value} "
                f"({self.status.value})")


class TransactionQueue:
    def __init__(self):
        self._heap: list = []
        self._counter = 0

    def add(self, tx: Transaction, priority=None,
            delay_seconds: float = 0) -> None:
        if priority is not None:
            tx.priority = priority
        if not isinstance(tx.priority, Priority):
            tx.priority = Priority(tx.priority)

        now = datetime.now()
        if delay_seconds > 0:
            tx.scheduled_at = now + timedelta(seconds=delay_seconds)
            tx.status = TransactionStatus.DELAYED
        else:
            tx.scheduled_at = now
            tx.status = TransactionStatus.PENDING

        self._counter += 1
        heapq.heappush(self._heap, (-tx.priority.value, self._counter, tx))

    def get_ready(self) -> List[Transaction]:
        now = datetime.now()
        ready, not_ready = [], []
        all_items = []
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

    def cancel(self, tx_id: str) -> bool:
        for item in self._heap:
            tx = item[2]
            if tx.transaction_id == tx_id:
                if tx.status == TransactionStatus.COMPLETED:
                    raise InvalidOperationError(
                        "Нельзя отменить выполненную транзакцию"
                    )
                tx.status = TransactionStatus.CANCELLED
                return True
        return False

    def __len__(self) -> int:
        return sum(
            1 for item in self._heap
            if item[2].status in (TransactionStatus.PENDING,
                                  TransactionStatus.DELAYED)
        )


class TransactionProcessor:
    EXTERNAL_COMMISSION_RATE = Decimal("0.01")

    FX_RATES = {
        (Currency.RUB, Currency.USD): Decimal("0.011"),
        (Currency.USD, Currency.RUB): Decimal("90"),
        (Currency.RUB, Currency.EUR): Decimal("0.010"),
        (Currency.EUR, Currency.RUB): Decimal("100"),
        (Currency.USD, Currency.EUR): Decimal("0.92"),
        (Currency.EUR, Currency.USD): Decimal("1.09"),
        (Currency.RUB, Currency.CNY): Decimal("0.08"),
        (Currency.CNY, Currency.RUB): Decimal("12.5"),
        (Currency.RUB, Currency.KZT): Decimal("6"),
        (Currency.KZT, Currency.RUB): Decimal("0.17"),
    }

    def __init__(self, bank: Bank, retry_limit: int = 2):
        self.bank = bank
        self.retry_limit = retry_limit
        self.error_log: List[dict] = []

    def process(self, tx: Transaction) -> bool:
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

    def _pre_validate(self, tx: Transaction) -> None:
        if tx.amount <= 0:
            raise InvalidOperationError("Сумма должна быть > 0")

        if tx.sender_account_id:
            sender = self.bank._get_account(tx.sender_account_id)
            if sender._status == AccountStatus.FROZEN:
                raise AccountFrozenError(
                    f"Счёт отправителя ...{tx.sender_account_id[-4:]} заморожен"
                )
            if sender._status == AccountStatus.CLOSED:
                raise AccountClosedError("Счёт отправителя закрыт")
            if sender.currency != tx.currency:
                raise InvalidOperationError(
                    f"Валюта транзакции {tx.currency.value} не совпадает "
                    f"с валютой отправителя {sender.currency.value}"
                )
            if tx.tx_type in (TransactionType.TRANSFER_INTERNAL,
                              TransactionType.TRANSFER_EXTERNAL):
                if (not isinstance(sender, PremiumAccount)
                        and sender._balance < 0):
                    raise InvalidOperationError(
                        "Перевод при отрицательном балансе запрещён "
                        "(только Premium)"
                    )

        if (tx.recipient_account_id
                and tx.tx_type != TransactionType.TRANSFER_EXTERNAL):
            recipient = self.bank._get_account(tx.recipient_account_id)
            if recipient._status == AccountStatus.FROZEN:
                raise AccountFrozenError("Счёт получателя заморожен")
            if recipient._status == AccountStatus.CLOSED:
                raise AccountClosedError("Счёт получателя закрыт")

    def _calculate_commission(self, tx: Transaction) -> None:
        if tx.tx_type == TransactionType.TRANSFER_EXTERNAL:
            tx.commission = (tx.amount * self.EXTERNAL_COMMISSION_RATE
                             ).quantize(Decimal("0.01"))
        else:
            tx.commission = Decimal("0")

    def _execute(self, tx: Transaction) -> None:
        if tx.tx_type == TransactionType.DEPOSIT:
            self._execute_deposit(tx)
        elif tx.tx_type == TransactionType.WITHDRAW:
            self._execute_withdraw(tx)
        elif tx.tx_type == TransactionType.TRANSFER_INTERNAL:
            self._execute_transfer_internal(tx)
        elif tx.tx_type == TransactionType.TRANSFER_EXTERNAL:
            self._execute_transfer_external(tx)
        elif tx.tx_type == TransactionType.CURRENCY_EXCHANGE:
            self._execute_exchange(tx)

    def _execute_deposit(self, tx: Transaction) -> None:
        recipient = self.bank._get_account(tx.recipient_account_id)
        recipient.deposit(tx.amount)

    def _execute_withdraw(self, tx: Transaction) -> None:
        sender = self.bank._get_account(tx.sender_account_id)
        sender.withdraw(tx.amount)

    def _convert(self, amount: Decimal, from_cur: Currency,
                 to_cur: Currency) -> Decimal:
        if from_cur == to_cur:
            return amount
        rate = self.FX_RATES.get((from_cur, to_cur))
        if rate is None:
            raise InvalidOperationError(
                f"Нет курса {from_cur.value} → {to_cur.value}"
            )
        return (amount * rate).quantize(Decimal("0.01"))

    def _execute_transfer_internal(self, tx: Transaction) -> None:
        sender = self.bank._get_account(tx.sender_account_id)
        recipient = self.bank._get_account(tx.recipient_account_id)
        recipient_amount = self._convert(
            tx.amount, tx.currency, recipient.currency
        )
        total_out = tx.amount + tx.commission
        sender.withdraw(total_out)
        recipient.deposit(recipient_amount)

    def _execute_transfer_external(self, tx: Transaction) -> None:
        sender = self.bank._get_account(tx.sender_account_id)
        total_out = tx.amount + tx.commission
        sender.withdraw(total_out)

    def _execute_exchange(self, tx: Transaction) -> None:
        sender = self.bank._get_account(tx.sender_account_id)
        recipient = self.bank._get_account(tx.recipient_account_id)
        converted = self._convert(tx.amount, tx.currency, recipient.currency)
        sender.withdraw(tx.amount)
        recipient.deposit(converted)

    def _handle_failure(self, tx: Transaction, exc: AccountError) -> None:
        tx.retry_count += 1
        tx.rejection_reason = str(exc)
        self.error_log.append({
            "time": datetime.now(),
            "transaction_id": tx.transaction_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "retry_count": tx.retry_count,
        })
        if tx.retry_count <= tx.max_retries:
            tx.status = TransactionStatus.PENDING
        else:
            tx.status = TransactionStatus.FAILED

    def process_batch(self, queue: TransactionQueue) -> List[Transaction]:
        ready = queue.get_ready()
        for tx in ready:
            self.process(tx)
            if (tx.status == TransactionStatus.PENDING
                    and tx.retry_count > 0):
                queue.add(tx, delay_seconds=0)
        return ready


# ДЕМОНСТРАЦИЯ ДНЯ 4
def demo_day4() -> None:
    print("=" * 60)
    print("ДЕНЬ 4. СИСТЕМА ТРАНЗАКЦИЙ")
    print("=" * 60)

    bank = Bank("Bank Day 4")

    ivan = bank.add_client("Иван Петров", 1990, {"phone": "+7-900"}, "1111")
    maria = bank.add_client("Мария Сидорова", 1985, {"phone": "+7-901"}, "2222")

    ivan_rub = bank.open_account(ivan.client_id, "basic",
                                 currency=Currency.RUB, initial_balance=10000)
    ivan_usd = bank.open_account(ivan.client_id, "premium",
                                 currency=Currency.USD, initial_balance=100)
    maria_rub = bank.open_account(maria.client_id, "savings",
                                  currency=Currency.RUB,
                                  initial_balance=5000, min_balance=0)
    maria_usd = bank.open_account(maria.client_id, "basic",
                                  currency=Currency.USD, initial_balance=50)
    maria_frozen = bank.open_account(maria.client_id, "basic",
                                     currency=Currency.RUB,
                                     initial_balance=1000)
    bank.freeze_account(maria.client_id, maria_frozen.account_id)

    print("\n[Стартовые балансы]")
    print(f"  Иван RUB:       {ivan_rub._balance}")
    print(f"  Иван USD:       {ivan_usd._balance}")
    print(f"  Мария RUB:      {maria_rub._balance}")
    print(f"  Мария USD:      {maria_usd._balance}")
    print(f"  Замороженный:   {maria_frozen._balance} (заморожен)")

    processor = TransactionProcessor(bank)
    queue = TransactionQueue()

    tx1 = Transaction(TransactionType.DEPOSIT, 5000, Currency.RUB,
                      recipient_account_id=ivan_rub.account_id)
    tx2 = Transaction(TransactionType.WITHDRAW, 2000, Currency.RUB,
                      sender_account_id=ivan_rub.account_id)
    tx3 = Transaction(TransactionType.TRANSFER_INTERNAL, 1000, Currency.RUB,
                      sender_account_id=ivan_rub.account_id,
                      recipient_account_id=maria_rub.account_id)
    tx4 = Transaction(TransactionType.TRANSFER_EXTERNAL, 500, Currency.RUB,
                      sender_account_id=ivan_rub.account_id,
                      recipient_account_id="EXTERNAL-1")
    tx5 = Transaction(TransactionType.TRANSFER_INTERNAL, 5000, Currency.RUB,
                      sender_account_id=ivan_rub.account_id,
                      recipient_account_id=maria_usd.account_id)
    tx6 = Transaction(TransactionType.TRANSFER_INTERNAL, 100, Currency.RUB,
                      sender_account_id=ivan_rub.account_id,
                      recipient_account_id=maria_frozen.account_id)
    tx7 = Transaction(TransactionType.DEPOSIT, 10000, Currency.RUB,
                      recipient_account_id=ivan_rub.account_id)
    tx8 = Transaction(TransactionType.TRANSFER_INTERNAL, 999999, Currency.RUB,
                      sender_account_id=ivan_rub.account_id,
                      recipient_account_id=maria_rub.account_id)
    tx9 = Transaction(TransactionType.DEPOSIT, 100, Currency.USD,
                      recipient_account_id=ivan_usd.account_id)
    tx10 = Transaction(TransactionType.TRANSFER_EXTERNAL, 2000, Currency.RUB,
                       sender_account_id=maria_rub.account_id,
                       recipient_account_id="EXTERNAL-2")

    queue.add(tx1, priority=Priority.NORMAL)
    queue.add(tx2, priority=Priority.NORMAL)
    queue.add(tx3, priority=Priority.HIGH)
    queue.add(tx4, priority=Priority.NORMAL)
    queue.add(tx5, priority=Priority.LOW)
    queue.add(tx6, priority=Priority.NORMAL)
    queue.add(tx7, priority=Priority.HIGH)
    queue.add(tx8, priority=Priority.NORMAL)
    queue.add(tx9, priority=Priority.LOW)
    queue.add(tx10, priority=Priority.NORMAL, delay_seconds=2)

    print(f"\n[Очередь до обработки] В очереди: {len(queue)} транзакций")

    print("\n[Проход 1 — высокий приоритет первым, tx10 отложена]")
    for tx in processor.process_batch(queue):
        print(f"  {tx}")

    print("\n[Проход 2 — повторные попытки tx6, tx8]")
    for tx in processor.process_batch(queue):
        print(f"  {tx}")

    print("\n[Проход 3 — финальные попытки]")
    for tx in processor.process_batch(queue):
        print(f"  {tx}")

    print(f"\n[Отложенная tx10] статус: {tx10.status.value}, "
          f"scheduled_at: {tx10.scheduled_at.strftime('%H:%M:%S')}")

    print("\n[Симулируем прошедшее время для tx10]")
    tx10.scheduled_at = datetime.now() - timedelta(seconds=1)
    for tx in processor.process_batch(queue):
        print(f"  {tx}")

    print("\n[Отмена транзакции]")
    tx_cancel = Transaction(TransactionType.DEPOSIT, 100, Currency.RUB,
                            recipient_account_id=ivan_rub.account_id)
    queue.add(tx_cancel, priority=Priority.HIGH)
    ok = queue.cancel(tx_cancel.transaction_id)
    print(f"  Отмена: {'успешно' if ok else 'не найдено'}")
    print(f"  Статус: {tx_cancel.status.value}")

    print("\n[Финальные балансы]")
    print(f"  Иван RUB:       {ivan_rub._balance}")
    print(f"  Иван USD:       {ivan_usd._balance}")
    print(f"  Мария RUB:      {maria_rub._balance}")
    print(f"  Мария USD:      {maria_usd._balance}")
    print(f"  Замороженный:   {maria_frozen._balance}")

    print(f"\n[Лог ошибок процессора] Всего: {len(processor.error_log)}")
    for err in processor.error_log:
        print(f"  [{err['time'].strftime('%H:%M:%S')}] "
              f"{err['transaction_id']}: {err['error_type']} — {err['error']}")

    print("\n" + "=" * 60)
    print("ДЕНЬ 4 ЗАВЕРШЁН")
    print("=" * 60)

if __name__ == "__main__":
    demo_day4()
