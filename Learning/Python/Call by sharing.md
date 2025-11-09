## Understanding Call By Sharing (Pass By Object Reference)

The term **"call by sharing"** is often used interchangeably with **"pass by object reference"** to describe Python's argument passing mechanism. It's a precise way to describe how variables (which are #VariablesAsReferences) are handled when passed to functions.

Here's the core idea: When you pass an argument to a function, you're not passing a copy of the value itself (like "pass by value"), nor are you passing the memory address of the *variable* (like true "pass by reference" in C++). Instead, you're passing a copy of the **reference** to the object that the argument variable points to.

In simpler terms, the function's parameter variable becomes an **alias** for the original object. Both the variable outside the function and the parameter inside the function "share" a reference to the same object in memory.

### Key Aspects of Call By Sharing

1.  **#ObjectsInMemory:** In Python, all data lives in memory as objects. Variables are just names that point to these objects.
2.  **References are Copied:** When a function is called, the argument's reference to an object is copied to the function's local parameter. The parameter variable now points to the *exact same object* that the original argument points to.
3.  **Impact of Mutability:** The observable effects of #CallBySharing depend entirely on whether the shared object is #MutableObjects or #ImmutableObjects.

---

### How Call By Sharing Works with Mutability

#### 1. With Immutable Objects (#ImmutableObjects)

If you pass an immutable object (like a number, string, or tuple) to a function, and then try to "change" it inside the function, you'll find the original object outside the function is unaffected.

**Why?** Because immutable objects cannot be modified after creation. Any operation that *looks* like a modification (e.g., `num = num + 1`, `s = s + "world"`) actually creates a *new* object, and the local parameter inside the function will then refer to this new object. The original variable outside the function still refers to the old, unchanged object.

##### Example 1.1: Immutable Integer
`#Example/CallBySharingImmutable`

```python
def increment(value):
    print(f"Inside func - before change: value={value}, id={id(value)}") # value and original_num refer to the same object
    value = value + 1  # Creates a *new* integer object, 'value' now refers to this new object
    print(f"Inside func - after change: value={value}, id={id(value)}")   # id of value is now different

original_num = 10
print(f"Outside func - before call: original_num={original_num}, id={id(original_num)}")

increment(original_num) # 'value' receives a copy of the reference to the object '10'

print(f"Outside func - after call: original_num={original_num}, id={id(original_num)}") # original_num is still 10, refers to the original object
```
**Explanation:**
1.  `original_num` points to the integer object `10`.
2.  When `increment(original_num)` is called, `value` inside the function also points to the integer object `10`.
3.  `value = value + 1` does not change the object `10`. Instead, it calculates `10 + 1` (which is `11`), creates a *new* integer object `11`, and makes the *local* `value` variable point to this new `11` object.
4.  `original_num` outside the function continues to point to the original `10` object, which was never modified.

#### 2. With Mutable Objects (#MutableObjects)

If you pass a mutable object (like a list or dictionary) to a function, and then modify its *contents* inside the function, these changes *will be visible* outside the function.

**Why?** Because both the original variable and the function parameter are #Aliasing the *same mutable object*. When you modify the object's contents (e.g., `list.append()`, `dict[key] = value`), you're changing the shared object itself, which both references point to.

However, if you *reassign the parameter itself* (e.g., `my_list = [new_data]`), this breaks the link between the parameter and the original object, and the original variable remains unaffected.

##### Example 2.1: Modifying a Mutable List
`#Example/CallBySharingMutableModify`

```python
def add_element(my_list):
    print(f"Inside func - before change: my_list={my_list}, id={id(my_list)}") # my_list and data refer to the same list object
    my_list.append(4) # Modifies the *shared list object*
    print(f"Inside func - after change: my_list={my_list}, id={id(my_list)}")   # id of my_list is still the same

data = [1, 2, 3]
print(f"Outside func - before call: data={data}, id={id(data)}")

add_element(data) # 'my_list' receives a copy of the reference to the list object [1, 2, 3]

print(f"Outside func - after call: data={data}, id={id(data)}") # data is now [1, 2, 3, 4]
```
**Explanation:**
1.  `data` points to the list object `[1, 2, 3]`.
2.  When `add_element(data)` is called, `my_list` inside the function also points to the list object `[1, 2, 3]`.
3.  `my_list.append(4)` directly modifies the list object that *both* `my_list` and `data` are referring to. The object's identity (`id`) remains the same.
4.  Therefore, `data` outside the function sees the modification because it still points to the same object.

##### Example 2.2: Reassigning a Mutable List Parameter
`#Example/CallBySharingMutableReassign`

```python
def replace_list(my_list):
    print(f"Inside func - before change: my_list={my_list}, id={id(my_list)}") # my_list and data refer to the same list object
    my_list = ['a', 'b', 'c'] # Creates a *new* list object, 'my_list' now refers to this new object
    print(f"Inside func - after change: my_list={my_list}, id={id(my_list)}")   # id of my_list is now different

data = [1, 2, 3]
print(f"Outside func - before call: data={data}, id={id(data)}")

replace_list(data) # 'my_list' receives a copy of the reference to the list object [1, 2, 3]

print(f"Outside func - after call: data={data}, id={id(data)}") # data is still [1, 2, 3]
```
**Explanation:**
1.  `data` points to the list object `[1, 2, 3]`.
2.  When `replace_list(data)` is called, `my_list` inside the function also points to the list object `[1, 2, 3]`.
3.  `my_list = ['a', 'b', 'c']` creates a *new* list object `['a', 'b', 'c']` and makes the *local* `my_list` variable point to this new object. This breaks the #Aliasing between `my_list` and the original `data`'s object.
4.  `data` outside the function continues to point to the original `[1, 2, 3]` object, which was never modified or reassigned by any other reference.

---

### Summary of Call By Sharing

*   #CallBySharing (or #PassByObjectReference) means a copy of the *object's reference* is passed to the function.
*   The function parameter becomes an #Aliasing for the original object.
*   If you **modify the shared object** (e.g., `list.append()`, `dict[key] = value`), these changes are visible outside the function, provided the object is #MutableObjects.
*   If you **reassign the parameter variable itself** within the function (e.g., `param = new_value`), this only changes what the *local parameter* refers to. It does *not* affect the original variable outside the function, regardless of mutability.