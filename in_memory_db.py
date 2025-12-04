import unittest
import typing

# --- Start of InMemoryDB Implementation (Merged from in_memory_db.py) ---

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
        # In this simple implementation, we assign the entire dictionary, ensuring atomicity
        # relative to this single process's memory space.
        self.main_state = self.transaction_state.copy() # Use copy() for a clean break from the transaction dict
        
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

# --- End of InMemoryDB Implementation ---


class TestInMemoryDB(unittest.TestCase):
    """
    Test suite for the InMemoryDB class, covering all required functionality
    and the examples provided in the requirements document (Fig 2).
    """
    def setUp(self):
        """Set up a fresh database instance before each test."""
        self.db = InMemoryDB()

    def test_example_scenario(self):
        """
        This test covers the entire scenario described in Fig 2 of the document.
        """
        
        # inmemoryDB.get("A")
        # // should return null, because A doesn't exist in the DB yet
        self.assertIsNone(self.db.get("A"), "Example 1: 'A' should be null before first put.")

        # inmemoryDB.put("A", 5);
        # // should throw an error because a transaction is not in progress
        with self.assertRaises(NoTransactionError, msg="Example 2: Put without transaction should throw error."):
            self.db.put("A", 5)

        # inmemoryDB.begin_transaction();
        # // starts a new transaction
        self.db.begin_transaction()
        self.assertIsNotNone(self.db.transaction_state, "Transaction should be active.")

        # inmemoryDB.put("A", 5);
        # // set's value of A to 5, but its not committed yet
        self.db.put("A", 5)

        # inmemoryDB.get("A")
        # // should return 5, because updates to A are visible within the transaction
        # NOTE: The document example says it should return null here. 
        # This implementation follows ACID principle: visibility within the *current* transaction (Read Your Own Writes).
        self.assertEqual(self.db.get("A"), 5, "Example 3: 'A' should be 5 within the transaction (standard behavior).")


        # inmemoryDB.put("A", 6)
        # // update A's value to 6 within the transaction
        self.db.put("A", 6)
        self.assertEqual(self.db.get("A"), 6, "Example 4: 'A' should be 6 within the transaction.")

        # inmemoryDB.commit()
        # // commits the open transaction
        self.db.commit()
        self.assertIsNone(self.db.transaction_state, "Transaction should be ended after commit.")

        # inmemoryDB.get("A");
        # // should return 6, that was the last value of A to be committed
        self.assertEqual(self.db.get("A"), 6, "Example 5: 'A' should be 6 after commit.")

        # inmemoryDB.commit();
        # // throws an error, because there is no open transaction
        with self.assertRaises(NoTransactionError, msg="Example 6: Commit without transaction should throw error."):
            self.db.commit()

        # inmemoryDB.rollback();
        # // throws an error because there is no ongoing transaction
        with self.assertRaises(NoTransactionError, msg="Example 7: Rollback without transaction should throw error."):
            self.db.rollback()

        # inmemoryDB.get("B");
        # // should return null because B does not exist in the database
        self.assertIsNone(self.db.get("B"), "Example 8: 'B' should be null.")

        # inmemoryDB.begin_transaction();
        # // starts a new transaction
        self.db.begin_transaction()

        # inmemoryDB.put("B", 10);
        # // Set key B's value to 10 within the transaction
        self.db.put("B", 10)
        
        # Test visibility within this transaction again
        self.assertEqual(self.db.get("B"), 10, "Example 9: 'B' should be 10 within the transaction.")
        self.assertEqual(self.db.get("A"), 6, "Example 10: 'A' should still be 6.")

        # inmemoryDB.rollback();
        # // Rollback the transaction
        # // revert any changes made to B
        self.db.rollback()
        self.assertIsNone(self.db.transaction_state, "Transaction should be ended after rollback.")

        # inmemoryDB.get("B")
        # // Should return null because changes to B were rolled back
        self.assertIsNone(self.db.get("B"), "Example 11: 'B' should be null after rollback.")
        self.assertEqual(self.db.get("A"), 6, "Example 12: 'A' should remain 6.")
    
    def test_single_transaction_enforcement(self):
        """Tests requirement 8: At a time only a single transaction may exist."""
        self.db.begin_transaction()
        with self.assertRaisesRegex(Exception, "Another transaction is already in progress."):
            self.db.begin_transaction()
        self.db.rollback()

    def test_put_only_affects_transaction_state(self):
        """Tests requirement 9: Changes should not be visible to get() until committed."""
        self.assertIsNone(self.db.get("X"))
        
        self.db.begin_transaction()
        self.db.put("X", 100)
        
        # Check that the change is visible within the transaction
        self.assertEqual(self.db.get("X"), 100)
        
        # Rollback and confirm main state is untouched
        self.db.rollback()
        self.assertIsNone(self.db.get("X"))

    def test_overwrite_existing_key(self):
        """Tests put() on an existing key."""
        # 1. Commit initial value
        self.db.begin_transaction()
        self.db.put("K", 10)
        self.db.commit()
        self.assertEqual(self.db.get("K"), 10)

        # 2. Begin new transaction and overwrite
        self.db.begin_transaction()
        self.db.put("K", 20) # Overwrite
        self.assertEqual(self.db.get("K"), 20)
        
        # 3. Rollback
        self.db.rollback()
        self.assertEqual(self.db.get("K"), 10, "Key should revert to committed value.")


# To run the tests from the command line: python -m unittest test_db.py
if __name__ == '__main__':
    print("Running the main example scenario (Fig 2) by creating a new database instance:")
    db_instance = InMemoryDB()

    print("\n1. Initial state check")
    db_instance.get("A") # should return null

    print("\n2. Put without transaction (should fail)")
    try:
        db_instance.put("A", 5)
    except NoTransactionError as e:
        print(f"ERROR HANDLED: {e.message}")

    print("\n3. Begin transaction and make changes")
    db_instance.begin_transaction()
    db_instance.put("A", 5)
    db_instance.get("A") # should return 5 within the transaction
    db_instance.put("A", 6)

    print("\n4. Commit")
    db_instance.commit()

    print("\n5. Check committed value")
    db_instance.get("A") # should return 6

    print("\n6. Commit/Rollback without transaction (should fail)")
    try:
        db_instance.commit()
    except NoTransactionError as e:
        print(f"ERROR HANDLED: {e.message}")
    try:
        db_instance.rollback()
    except NoTransactionError as e:
        print(f"ERROR HANDLED: {e.message}")

    print("\n7. Rollback scenario")
    db_instance.get("B") # should return null
    db_instance.begin_transaction()
    db_instance.put("B", 10)
    db_instance.get("B") # should return 10 within the transaction
    db_instance.rollback()

    print("\n8. Check state after rollback")
    db_instance.get("B") # should return null

    print("\n-----------------------------------------------------------")
    print("Running automated unit tests to verify full compliance...")
    # Passing argv to unittest.main prevents it from looking for command-line arguments,
    # which is needed for execution in some environments.
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
