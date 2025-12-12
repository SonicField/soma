# # 11. Standard Library: Containers

Container data structures and their operations: linked lists, dictionaries, and AL draining utilities.

---

## ## Coding Principles

These principles apply specifically to stdlib code, where robustness and composability are critical.

**1. No Temp Namespace for Persistent State**

Never store state in the temp namespace that must survive nested calls. If a function's folder/callback might call the same function recursively, the temp storage will be clobbered. Instead, pass state through the iteration using context-passing.

```soma
) BAD:  _.folder !temp.fold_fn ... temp.fold_fn >^
) GOOD: Pass folder through: _.folder _.acc _.list then pop
```

**2. Private Helper Naming: x.#y**

Internal helper blocks local to a package use the `#` prefix convention. This signals "private/internal" and avoids polluting the public namespace. Example: `list.fold.#loop`, `dict.put.#fixup`.

**3. Context-Passing for Choose Branches**

Blocks inside choose branches cannot access the outer Register directly. Push the context reference before choose, then pop it inside each branch:

```soma
) Push context reference
_.
<condition>
) Pop context, access outer variables
{ !_. _.outer_var ... }
{ !_. _.other_var ... }
>choose >^
```

**4. Functional/Immutable Style**

Mutating operations return new containers rather than modifying in place. This matches SOMA's functional nature and enables safe composition.

---

## ## Linked Lists

Linked lists using CellRefs and context-passing style. Empty list is `Nil`, nodes have `.value` and `.next` fields.

### ### >list.new

**Signature:** `([...] -> [Nil, ...])`

Creates an empty list. An empty list is simply `Nil`.

**Definition:**

```soma
{ Nil } !list.new
```

**Example:**

```soma
>list.new    ; AL: [Nil]
```

---

### ### >list.cons

**Signature:** `([value, list, ...] -> [new_node, ...])`

Prepends a value to a list, creating a new node. The new node's `.value` is the given value, and `.next` points to the original list.

**Definition:**

```soma
{
  !_.list !_.value
  _.value !_.node.value
  _.list !_.node.next
  _.node.
} !list.cons
```

**Example:**

```soma
(a) Nil >list.cons          ; AL: [node] where node.value=(a), node.next=Nil
(b) >list.cons               ; AL: [node'] where node'.value=(b), node'.next=node
```

---

### ### >list.from_al

**Signature:** `([Void, items..., ...] -> [list, ...])`

Drains AL items until Void, building a linked list. Preserves order: `Void (a) (b) (c)` becomes list `(a,b,c)`.

**Definition:**

```soma
{
  >list.new { !_.persistent !_.current _.current _.persistent >list.cons } >al.drain
} !list.from_al
```

**Example:**

```soma
Void (first) (second) (third) >list.from_al
; AL: [list] containing (first), (second), (third)
```

---

### ### >list.to_al

**Signature:** `([list, ...] -> [items..., ...])`

Pushes list items onto AL. Preserves order: list `(a,b,c)` becomes AL `[(a), (b), (c)]`.

**Example:**

```soma
my_list >list.to_al
; Each item now on AL, head first
```

---

### ### >list.reverse

**Signature:** `([list, ...] -> [reversed_list, ...])`

Reverses a list by copying. Creates a new list with elements in reverse order.

**Example:**

```soma
Void (a) (b) (c) >list.from_al >list.reverse
; AL: [list] containing (c), (b), (a)
```

---

### ### >list.map

**Signature:** `([transform_block, list, ...] -> [mapped_list, ...])`

Applies a transform block to each element, returning a new list. The transform block receives `[value, ...]` and should leave `[new_value, ...]`. Order is preserved.

**Example:**

```soma
{ 2 >* } my_list >list.map
; Each element doubled
```

---

### ### >list.length

**Signature:** `([list, ...] -> [count, ...])`

Counts elements in the list by traversing until Nil.

**Example:**

```soma
Void (a) (b) (c) >list.from_al >list.length
; AL: [3]
```

---

### ### >list.fold

**Signature:** `([folder, init, list, ...] -> [result, ...])`

Reduces a list with an accumulator. The folder block receives `[current, acc, ...]` and returns the new accumulator. Processes from head to tail (left fold).

**Example:**

```soma
{ >+ } 0 my_number_list >list.fold
; Sum of all elements
```

---

### ### >list.append

**Signature:** `([list1, list2, ...] -> [concatenated, ...])`

Concatenates two lists. Result has list1 elements followed by list2 elements.

**Example:**

```soma
list_abc list_xyz >list.append
; AL: [list] containing a,b,c,x,y,z
```

---

### ### >list.filter

**Signature:** `([predicate, list, ...] -> [filtered, ...])`

Keeps elements matching the predicate. The predicate receives `[value, ...]` and returns a boolean. Order is preserved.

**Example:**

```soma
{ 0 >> } my_numbers >list.filter
; Keep only positive numbers
```

---

## ## AL Draining

### ### >al.drain

**Signature:** `([Void, item1, ..., itemN, persistent, action_block, ...] -> [result, ...])`

Drains AL until Void, applying an action to each item. The action block receives `[current, persistent, ...]` and should return the new persistent value. This is the core state transformer: AL -> AL'.

**Example:**

```soma
Void (a) (b) (c)    ) Items to process
Nil                   ) Initial accumulator
{ !_.acc !_.item _.item _.acc >list.cons }
>al.drain
) Builds a list from items
```

---

## ## Dictionaries

Key-value dictionary implemented as a Left-Leaning Red-Black (LLRB) tree. Supports any key type that works with `><` and `>==`.

**Red-Black Tree Invariants:**

- Root is always black
- No red node has a red child
- All paths from root to leaves have the same black count
- BST property: left.key < node.key < right.key

Structure: `Nil` | node where node has `.key`, `.value`, `.color` (True=red, False=black), `.left`, `.right`.

### ### >dict.new

**Signature:** `([...] -> [dict, ...])`

Creates an empty dictionary. An empty dictionary is `Nil`.

**Example:**

```soma
>dict.new    ; AL: [Nil]
```

---

### ### >dict.has

**Signature:** `([key, dict, ...] -> [bool, ...])`

Checks if a key exists in the dictionary. Returns `True` if found, `False` otherwise.

**Example:**

```soma
(name) my_dict >dict.has
; AL: [True] if "name" key exists
```

---

### ### >dict.get

**Signature:** `([key, dict, ...] -> [value, ...])`

Gets value by key. **Errors if key not found** (attempts Nil dereference).

**Example:**

```soma
(name) my_dict >dict.get
; AL: [value] associated with "name"
```

---

### ### >dict.get_or

**Signature:** `([key, default, dict, ...] -> [value, ...])`

Gets value by key, or returns default if not found. Safe alternative to `>dict.get`.

**Example:**

```soma
(name) (unknown) my_dict >dict.get_or
; AL: [value] or (unknown) if key missing
```

---

### ### >dict.put

**Signature:** `([key, value, dict, ...] -> [new_dict, ...])`

Inserts or updates a key-value pair. Returns a new dictionary; the original is unchanged. Uses LLRB tree insertion with automatic rebalancing to maintain invariants.

**Implementation notes:** New nodes are inserted as red. After insertion, three fixup cases are applied:

- Right child red, left child black: rotate left
- Left child red, left-left grandchild red: rotate right
- Both children red: flip colours

The root is always made black after insertion.

**Example:**

```soma
(name) (Alice) my_dict >dict.put
; AL: [new_dict] with name=Alice
```

---

### ### >dict.remove

**Signature:** `([key, dict, ...] -> [new_dict, ...])`

Removes a key from the dictionary. Returns a new dictionary. Implementation collects all entries, filters out the key, and rebuilds the tree.

**Example:**

```soma
(name) my_dict >dict.remove
; AL: [new_dict] without "name" key
```

---

### ### >dict.size

**Signature:** `([dict, ...] -> [count, ...])`

Counts entries in the dictionary via tree traversal.

**Example:**

```soma
my_dict >dict.size
; AL: [n] where n is number of key-value pairs
```

---

### ### >dict.keys

**Signature:** `([dict, ...] -> [list, ...])`

Gets a list of all keys via in-order traversal. Keys are returned in sorted order.

**Example:**

```soma
my_dict >dict.keys
; AL: [list of keys]
```

---

### ### >dict.values

**Signature:** `([dict, ...] -> [list, ...])`

Gets a list of all values via in-order traversal. Values are returned in key-sorted order.

**Example:**

```soma
my_dict >dict.values
; AL: [list of values]
```

---

### ### >dict.fold

**Signature:** `([folder, init, dict, ...] -> [result, ...])`

Folds over dictionary entries via in-order traversal. The folder receives `[key, value, acc, ...]` and returns the new accumulator.

**Example:**

```soma
{ !_.acc !_.val !_.key _.acc 1 >+ } 0 my_dict >dict.fold
; Count entries (equivalent to >dict.size)
```

---

## ## Reference Table

| Operation       | AL transformation                     | Description                   |
|-----------------|---------------------------------------|-------------------------------|
| `>list.new`     | [] -> [Nil]                           | Create empty list             |
| `>list.cons`    | [val, list] -> [node]                 | Prepend value                 |
| `>list.from_al` | [Void, items...] -> [list]            | Build list from AL            |
| `>list.to_al`   | [list] -> [items...]                  | Push list items to AL         |
| `>list.reverse` | [list] -> [reversed]                  | Reverse list                  |
| `>list.map`     | [fn, list] -> [mapped]                | Transform elements            |
| `>list.length`  | [list] -> [count]                     | Count elements                |
| `>list.fold`    | [fn, init, list] -> [result]          | Reduce with accumulator       |
| `>list.append`  | [list1, list2] -> [concatenated]      | Concatenate lists             |
| `>list.filter`  | [pred, list] -> [filtered]            | Keep matching elements        |
| `>al.drain`     | [Void, items..., acc, fn] -> [result] | Process AL items              |
| `>dict.new`     | [] -> [Nil]                           | Create empty dict             |
| `>dict.has`     | [key, dict] -> [bool]                 | Check key exists              |
| `>dict.get`     | [key, dict] -> [value]                | Get value (errors if missing) |
| `>dict.get_or`  | [key, default, dict] -> [value]       | Get value or default          |
| `>dict.put`     | [key, value, dict] -> [new_dict]      | Insert/update entry           |
| `>dict.remove`  | [key, dict] -> [new_dict]             | Remove entry                  |
| `>dict.size`    | [dict] -> [count]                     | Count entries                 |
| `>dict.keys`    | [dict] -> [list]                      | Get all keys                  |
| `>dict.values`  | [dict] -> [list]                      | Get all values                |
| `>dict.fold`    | [fn, init, dict] -> [result]          | Fold over entries             |

---

## ## Summary

The container library provides two primary data structures:

- **Linked lists** - Nil-terminated chains of nodes with `.value` and `.next` fields. Functional operations preserve immutability.
- **Dictionaries** - LLRB trees providing O(log n) lookup, insertion, and deletion. Keys must support `><` and `>==`.

Both follow functional/immutable style: operations return new structures rather than modifying in place.


