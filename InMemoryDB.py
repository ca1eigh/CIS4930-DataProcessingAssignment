import typing

# Define a custom exception for when operations are called without an active transaction
class NoTransactionError(Exception):
    """Raised when a transactional operation (like put, commit, or rollback) is called
    without an active transaction."""
    def __init__(self, message="A transaction is not currently in progress."):
        self.message = message
        super().__init__(self.message)

class InMemoryDB:
    """
    An in-memory key-value database supporting single-level transactions (begin, commit, rollback).
    Keys are strings, and values are integers.
    """

    def __init__(self):
        # The main, committed state of the database.
        # This is what 'get()' reads from outside a transaction.
        # Format: {key: value}
        self.main_state: typing.Dict[str, int] = {}

        # The transactional state (the temporary changes).
        # This is a dict of changes made since the last begin_transaction().
        # If None, no transaction is currently active.
        # The transactional state shadows/overrides the main_state during a transaction.
        self.transaction_state: typing.Optional[typing.Dict[str, int]] = None

    def begin_transaction(self) -> None:
        """
        Starts a new transaction.
        Only a single transaction may exist at a time.
        """
        if self.transaction_state is not None:
            raise Exception("Another transaction is already in progress.")
        
        # We start the transaction state as a deep copy of the main state.
        # All changes (put) will modify this copy.
        # This ensures that 'get' during a transaction sees both committed and uncommitted changes,
        # and 'rollback' can simply discard this entire dictionary.
        self.transaction_state = self.main_state.copy()
        print("--- Transaction started ---")


    def put(self, key: str, value: int) -> None:
        """
        Sets the value for a given key.
        If a transaction is active, the change is applied only to the transaction state.
        If no transaction is active, an exception is thrown.
        Keys are strings, values must be integers.
        """
        if not isinstance(value, int):
            raise ValueError("Value must be an integer.")
            
        if self.transaction_state is None:
            raise NoTransactionError(
                f"Cannot put('{key}', {value}). A transaction is not in progress."
            )
        
        # Apply the change to the temporary transaction state
        self.transaction_state[key] = value
        print(f"Set '{key}' to {value} (uncommitted)")

    def get(self, key: str) -> typing.Optional[int]:
        """
        Returns the value for the given key.
        If a transaction is active, it first looks in the transaction state
        to see any uncommitted changes, then falls back to the main state.
        If no transaction is active, it only checks the main state.
        Returns None if the key does not exist.
        """
        if self.transaction_state is not None:
            # During a transaction, read from the temporary state which contains
            # all changes (committed + uncommitted).
            result = self.transaction_state.get(key)
            source = "transaction"
        else:
            # No transaction, read only from the main committed state.
            result = self.main_state.get(key)
            source = "main"
        
        # Handle the case where the key doesn't exist
        if result is None:
            print(f"Get '{key}': None (not found in {source} state)")
            return None
        else:
            print(f"Get '{key}': {result} (from {source} state)")
            return result

    def commit(self) -> None:
        """
        Applies all changes made within the current transaction to the main state.
        The transaction is then ended.
        """
        if self.transaction_state is None:
            raise NoTransactionError("Cannot commit. No open transaction to commit.")

        # Atomically update the main state with the changes from the transaction state
        self.main_state = self.transaction_state
        
        # End the transaction
        self.transaction_state = None
        print("--- Transaction committed successfully ---")

    def rollback(self) -> None:
        """
        Aborts the current transaction, discarding all uncommitted changes.
        The main state remains unchanged.
        The transaction is then ended.
        """
        if self.transaction_state is None:
            raise NoTransactionError("Cannot rollback. No open transaction to roll back.")

        # Discard the transaction state, effectively reverting all changes
        self.transaction_state = None
        print("--- Transaction rolled back successfully (changes discarded) ---")

# Optional: Add the interface definition as a type hint for clarity
# This is not runnable Python code but matches the spirit of the document's Fig 1
class InMemoryDBInterface(typing.Protocol):
    def get(self, key: str) -> typing.Optional[int]: ...
    def put(self, key: str, val: int) -> None: ...
    def begin_transaction(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
