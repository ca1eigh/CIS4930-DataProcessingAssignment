# CIS4930 Data Processing & Storage Assignment
Created by Caleigh Zaguirre

## Overview
This project provides an in-memory key-value database implementation in Python with support for single-level transactions (begin, commit, rollback).

## How to Run

1. Clone the repository

2. Open terminal and navigate to repo

3. Run the implementation file:
   ```
   python in_memory_db.py
   ```

4. The output will show each database operation, including successful gets, puts, commits, rollbacks, and the exceptions thrown when operations occur outside of an active transaction.

## Suggestions for Future Assignment Modifications

To convert this into a more robust and official assignment, two main changes are needed: complexity and clarity. To cover complexity, we could introduce support for nested transactions (transactions within transactions) to test students' understanding of state isolation and savepoints. As for clarity, we could require a new peek(key) function that only reads the committed state, regardless of an active transaction. This clarifies the isolation requirements and ambiguity in the original get() example. These changes would offer more effective ways to grade complexity and clarity in state management.
