## Error Handling in Python

Error handling is a critical aspect of writing robust and reliable Python code. It allows you to gracefully manage unexpected situations that arise during program execution, preventing crashes and providing meaningful feedback or recovery mechanisms. Python distinguishes between two main categories of errors: #SyntaxErrors and #Exceptions.

### Types of Errors

#### 1. Syntax Errors

These are errors detected by the Python interpreter *before* the code even runs. They occur when your code violates Python's grammatical rules.
`#SyntaxErrors`

**Example:**
```python
# This is a syntax error because of the missing colon
if x > 10
    print("x is greater than 10")
```
Python will immediately stop and report a `SyntaxError`. You must fix these errors before your program can even start executing.

#### 2. Exceptions (Runtime Errors)

#Exceptions are errors that occur *during* the execution of a program. Unlike #SyntaxErrors, the code is syntactically correct but something unexpected happens at runtime. When an exception occurs, Python normally terminates the program and prints a traceback. Error handling mechanisms allow you to intercept these exceptions and decide how to respond.
`#RuntimeErrors` `#Traceback`

##### Built-in Exceptions
Python has a rich hierarchy of built-in exceptions for common error conditions.
`#BuiltInExceptions`

**Common Examples:**
*   `NameError`: A variable is not defined.
*   `TypeError`: An operation is performed on an inappropriate type (e.g., adding a number to a string).
*   `ValueError`: A function receives an argument of the correct type but an inappropriate value (e.g., `int('hello')`).
*   `IndexError`: An index is out of range for a sequence (list, tuple).
*   `KeyError`: A dictionary key is not found.
*   `FileNotFoundError`: An attempt to open a file that doesn't exist.
*   `ZeroDivisionError`: Division by zero.

##### Custom Exceptions
You can define your own #CustomExceptions to represent specific error conditions unique to your application logic. This enhances code readability and allows for more granular error handling.

### Basic Exception Handling (`try-except`)

The `try-except` block is the fundamental construct for handling exceptions in Python.

#### The `try` Block
Code that might raise an exception is placed inside the `try` block.
`#TryBlock`

#### The `except` Block
If an exception occurs within the `try` block, Python immediately jumps to the `except` block. The code inside the `except` block is executed to handle the specific exception(s) caught. If no exception occurs in the `try` block, the `except` block is skipped.
`#ExceptBlock`

##### General `except`
Catching any exception that occurs. This is generally discouraged because it can mask unexpected errors.
`#GeneralExcept`

**Example:**
```python
try:
    result = 10 / 0 # This will raise a ZeroDivisionError
except:
    print("An unknown error occurred!")
```

##### Specific Exceptions
It's best practice to catch specific exceptions you anticipate. This makes your error handling more precise and prevents catching unrelated errors.
`#SpecificExcept`

**Example:**
```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Error: You tried to divide by zero!")

print("Program continues after handling.")
```

##### Handling Multiple Specific Exceptions
You can catch multiple specific exceptions in two ways:
1.  **Multiple `except` blocks:** For different handling logic.
    `#MultipleExceptBlocks`
2.  **A single `except` block with a tuple:** For the same handling logic.
    `#ExceptWithTuple`

**Example (Multiple `except` blocks):**
```python
try:
    num = int("hello") # ValueError
    # my_list = [1, 2]
    # print(my_list[3]) # IndexError
except ValueError:
    print("Invalid input: Could not convert to an integer.")
except IndexError:
    print("Accessing a list index out of range.")
except ZeroDivisionError: # Will not be caught here if ValueError occurs
    print("Division by zero occurred.")
```

**Example (Single `except` block with tuple):**
```python
try:
    num = int("hello") # ValueError
    # my_list = [1, 2]
    # print(my_list[3]) # IndexError
except (ValueError, IndexError):
    print("A data conversion or list index error occurred.")
```

##### `except` with `as`
You can get access to the actual #ExceptionObject that was raised using the `as` keyword. This object often contains useful information about the error.
`#ExceptionObject`

**Example:**
```python
try:
    data = {"name": "Alice"}
    print(data["age"]) # KeyError
except KeyError as e:
    print(f"Key not found: {e}. Please check the dictionary key.")
```

### Optional `else` and `finally` Blocks

#### The `else` Block
The `else` block executes *only if no exception occurs* in the `try` block. It's useful for code that should run only when the `try` block's execution was successful.
`#ElseBlock`

**Example:**
```python
try:
    x = 10
    y = 2
    result = x / y
except ZeroDivisionError:
    print("Division by zero error!")
else:
    print(f"Division successful. Result: {result}") # This runs
```

#### The `finally` Block
The `finally` block executes *always*, regardless of whether an exception occurred in the `try` block or not. It's typically used for #CleanupActions, such as closing files, releasing network connections, or cleaning up resources.
`#FinallyBlock` `#CleanupActions`

**Example:**
```python
file = None
try:
    file = open("my_data.txt", "r")
    content = file.read()
    print(content)
except FileNotFoundError:
    print("The file was not found.")
finally:
    if file: # Always ensure the file is closed if it was opened
        file.close()
    print("Resource cleanup complete.")
```

### Raising Exceptions (`raise`)

You can explicitly #RaiseExceptions in your code using the `raise` statement. This is useful for signaling an error condition from a function or for enforcing constraints.

**Syntax:** `raise ExceptionType("Error message")`
`#RaiseStatement`

##### Raising Built-in Exceptions
```python
def check_age(age):
    if not isinstance(age, int):
        raise TypeError("Age must be an integer.")
    if age < 0:
        raise ValueError("Age cannot be negative.")
    print(f"Age is {age}")

try:
    check_age(-5)
except (TypeError, ValueError) as e:
    print(f"Error caught: {e}")
```

##### Re-raising Exceptions
You might catch an exception to log it or perform some partial handling, but then decide that the calling code should also be aware of the error. You can re-raise the exception.
`#ReRaiseException`

```python
def process_data(data):
    try:
        # Some operation that might fail
        result = data / 0
    except ZeroDivisionError as e:
        print(f"Logged error in process_data: {e}")
        raise # Re-raises the same exception

try:
    process_data(100)
except ZeroDivisionError:
    print("Caught re-raised error in main program.")
```

### Custom Exceptions

#CustomExceptions allow you to create your own specific error types that inherit from Python's base `Exception` class (or one of its subclasses).
`#CustomExceptionDefinition`

**Why use Custom Exceptions?**
*   **Clarity:** Make your code's error messages more descriptive and domain-specific.
*   **Granular Handling:** Allows calling code to catch and handle very specific error conditions without catching broader, less specific built-in exceptions.
*   **Maintainability:** Easier to understand and debug your application's error states.

**Defining a Custom Exception:**
```python
class InsufficientFundsError(Exception):
    """Exception raised when a bank account has insufficient funds."""
    def __init__(self, message="Insufficient funds for this transaction.", balance=0, amount=0):
        self.message = message
        self.balance = balance
        self.amount = amount
        super().__init__(self.message)

# Using the custom exception
def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientFundsError(balance=balance, amount=amount,
                                     message=f"Attempted to withdraw {amount}, but only {balance} available.")
    return balance - amount

try:
    account_balance = 500
    new_balance = withdraw(account_balance, 700)
    print(f"New balance: {new_balance}")
except InsufficientFundsError as e:
    print(f"Transaction failed: {e.message} (Balance: {e.balance}, Amount: {e.amount})")
```

### Assertions (`assert`)

The `assert` statement is a debugging aid that checks if a condition is true. If the condition is false, it raises an `AssertionError`.
`#AssertStatement` `#AssertionError` `#DebuggingTool`

**Purpose:**
*   To enforce conditions that *must* be true for the program to continue correctly.
*   Primarily for #InternalInvariants and sanity checks during development and debugging.
*   They can be disabled in optimized Python mode (`python -O`) for production, which means they should *not* be used for validation of external input or critical runtime logic.

**Example:**
```python
def divide_numbers(a, b):
    assert b != 0, "Denominator cannot be zero!" # This is a debugging check
    return a / b

try:
    print(divide_numbers(10, 2))
    print(divide_numbers(5, 0)) # This will raise an AssertionError
except AssertionError as e:
    print(f"Assertion failed: {e}")
```
**`assert` vs. `try-except`:**
*   Use `assert` for program invariants that, if violated, indicate a bug in your code.
*   Use `try-except` for handling foreseeable external conditions (e.g., user input errors, file not found) that are not necessarily bugs in your code but require graceful handling.

### Context Managers (`with` statement)

#ContextManagers, typically used with the `with` statement, provide a clean and reliable way to ensure that resources are properly acquired and released, even if errors occur. This implicitly handles cleanup actions that might otherwise go into a `finally` block.
`#ContextManagers` `#WithStatement` `#ResourceManagement`

**How it works:**
The object used with `with` must implement the `__enter__` and `__exit__` methods.
*   `__enter__` is called when entering the `with` block. Its return value (if any) is assigned to the variable after `as`.
*   `__exit__` is called when exiting the `with` block, regardless of whether it exited normally or due to an exception. It handles cleanup. If an exception occurred, details are passed to `__exit__`.

**Example:**
```python
# Working with files is the most common use case
try:
    with open("my_log.txt", "w") as f: # f is the object returned by f.__enter__()
        f.write("This is a log entry.\n")
        # f.write(123) # Uncommenting this line would raise a TypeError
    # f.close() is implicitly called by f.__exit__() here
except TypeError:
    print("Cannot write non-string data to file.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

Many Python objects that manage resources (files, locks, database connections) are designed to be used as #ContextManagers. You can also create your own using classes with `__enter__`/`__exit__` or the `contextlib` module.
`#ContextlibModule`

### Best Practices for Error Handling

*   **Be Specific with `except`:** Catch the most specific exceptions first. Avoid broad `except:` unless you truly intend to catch everything (and then, usually re-raise after logging).
    `#BestPractice/SpecificExcept`
*   **Don't Suppress Errors Silently:** Never catch an exception and do nothing. At a minimum, log the error. Silent failures are the hardest bugs to track down.
    `#BestPractice/NoSilentErrors`
*   **Log Errors:** Use Python's `logging` module to record exceptions. This is crucial for debugging production systems.
    `#BestPractice/LogError`
*   **Use `finally` for Cleanup:** If resource management isn't covered by a #ContextManagers, use `finally` to ensure resources are released.
    `#BestPractice/FinallyForCleanup`
*   **Use Custom Exceptions:** When your application has specific error conditions, define and raise #CustomExceptions for clarity and precise handling.
    `#BestPractice/CustomExceptions`
*   **Avoid Overly Broad `except Exception`:** Catching `Exception` will catch almost everything, including system-exit signals. This can hide bugs. If you must catch all exceptions, it's often better to catch `Exception as e` and log `e` thoroughly, potentially re-raising it.
    `#BestPractice/AvoidBroadExcept`
*   **Use `else` for Clear Logic:** The `else` block makes it clear what code runs only if the `try` block was successful, separating it from the `try` block's potentially problematic code.
    `#BestPractice/ElseBlockClarity`
*   **Don't Use `assert` for Runtime Validation:** Assertions are for developer mistakes/bugs, not for validating user input or external data that might legitimately be incorrect. For such cases, use `if` statements and #RaiseExceptions.
    `#BestPractice/AssertVsTryExcept`