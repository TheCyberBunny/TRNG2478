# Day 1 — Notes
## Week 1, Wednesday: Modern Python, Syntax, Data Types, Functions, Flow Control, Classes & OOP, Pip & Virtual Environments, Python Modules

---

## Executive Summary

Today we laid the foundation of the RoboPulse Fleet Command Center: a
plain-Python domain model with no database and no API, just four
classes — `Facility`, `Robot`, `Mission`, `DiagnosticLog` — living
entirely in memory. That's a deliberate choice. Every day after this
one adds a layer on top (persistence on Thursday/Friday, then FastAPI,
then React) — but the *shape* of the data you defined today survives
mostly unchanged all the way to production. Getting comfortable with
Python's syntax, its data types, how functions and control flow work,
and how classes differ from Java classes, is the whole game today.

You come in with full-stack experience already, and many of you know
Java well. Good news: object-oriented thinking transfers directly.
What changes is syntax, some conventions, and a few genuinely different
design defaults (duck typing instead of static typing, no access
modifiers, everything is "public" by convention rather than by keyword).
This document leans on Java comparisons throughout for exactly that
reason — not because Python and Java are similar under the hood, but
because contrast is often the fastest way to make a new syntax feel
familiar.

---

## Deep Dive: Modern Python

"Modern Python" isn't a single feature — it's shorthand for the set of
conventions the language has converged on since Python 3.6+ that make
code both more readable and more robust:

- **Type hints** (`def f(x: int) -> str:`) — optional, not enforced at
  runtime, but read by editors, linters, and tools like FastAPI/Pydantic
  (which you'll meet in Week 2) to validate and auto-document your
  code. Contrast with Java, where types are mandatory and checked by
  the compiler; Python's hints are documentation and tooling support,
  not a language guarantee.
- **f-strings** (`f"{robot.serial_number} at {robot.battery_level}%"`)
  — the modern, preferred way to build strings, replacing older
  `%`-formatting and `.format()` calls. Directly comparable to Java's
  text blocks / `String.format`, but with the expression embedded
  inline rather than as a separate argument list.
- **The `enum` module** — as used in `enums.py` today. Python's `Enum`
  class gives you a fixed, named set of values, exactly like Java's
  `enum` keyword, though the mechanics differ: Python enums are regular
  classes under the hood, and by inheriting from `str` (as we did with
  `class RobotStatus(str, Enum)`), each member is *also* a string,
  which makes JSON serialization trivial later in FastAPI.

**Why it matters for RoboPulse:** the codebase you're building this
sprint needs to stay readable to a stranger (your Day 10/13 evaluators,
and future teammates). Type hints and f-strings aren't cosmetic — they
are how you keep a fast-moving, multi-day build legible.

---

## Deep Dive: Python Syntax

The syntactic differences from Java that trip people up fastest:

- **Indentation is structural, not stylistic.** In Java, `{ }` define a
  block and indentation is a style preference enforced by your linter.
  In Python, indentation *is* the block delimiter. Four spaces,
  consistently, is the convention (never tabs, never mixed).
- **No semicolons.** A newline ends a statement. Semicolons are legal
  but almost never used.
- **No parentheses required around conditions.** `if x > 5:` not
  `if (x > 5) {`.
- **Colons introduce blocks.** `if`, `for`, `while`, `def`, `class` all
  end their header line with `:` before the indented block begins.
- **`self` is explicit.** Every instance method's first parameter is
  `self`, written out by hand — Java's `this` is implicit and never
  appears in a method signature. You saw this constantly today:
  `def is_low_battery(self, threshold=None):`.

**Common Java habit to unlearn:** reaching for curly braces or a
semicolon out of muscle memory. Python will often *run* with a stray
semicolon (it's just a no-op statement separator) but will hard-fail on
inconsistent indentation — that's usually the first real error new
Python developers from Java hit.

---

## Deep Dive: Data Types

Python's built-in types map roughly like this against Java:

| Python | Rough Java equivalent | Notes |
|---|---|---|
| `int` | `int` / `long` | Arbitrary precision — no overflow, ever. |
| `float` | `double` | Used for `battery_level` today. |
| `str` | `String` | Immutable, like Java. |
| `bool` | `boolean` | `True`/`False`, capitalized. |
| `list` | `ArrayList` | Mutable, ordered, mixed types allowed. |
| `dict` | `HashMap` | Insertion-ordered since 3.7. |
| `tuple` | — (closest: an immutable fixed-size array) | Immutable, often used for fixed structured data. |
| `set` | `HashSet` | Unordered, unique elements. |
| `None` | `null` | But `None` is a singleton object, not a language keyword pointing at nothing. |

The RoboPulse models today used `int` (`id`, `capacity`), `float`
(`battery_level`), `str` (`name`, `serial_number`), and `Enum` members
(effectively a constrained `str`). Python is **dynamically typed**:
variables don't declare a type, values carry their type. `self.id = 1`
works whether `1` is an `int`, and nothing stops you from later writing
`self.id = "one"` — the language won't stop you, but your type hints
and a linter (or, in a few weeks, Pydantic) will flag the mismatch.

**Key mental model shift:** in Java, a variable *is* typed and holds a
reference to an object of that type. In Python, a name is just a label
pointing at an object — the object has the type, not the name.

---

## Deep Dive: Functions

```python
def find_low_battery_robots(robots: list[Robot], threshold: int = 20) -> list[Robot]:
    ...
```

Functions in Python are first-class, top-level citizens — they don't
have to live inside a class the way every Java method must live inside
some class. `find_low_battery_robots` in today's demo is a free-standing
function, not a `static` method on some utility class.

Notable features used today:

- **Default arguments** (`threshold: int = 20`) — comparable to Java's
  method overloading pattern, but done with a single signature instead
  of multiple overloads.
- **Keyword arguments** — `Robot(1, "RX-1001", "Sentinel-V2", battery_level=18.5, facility_id=1, status=RobotStatus.IN_MISSION)`
  mixes positional and keyword arguments. Once you use a keyword
  argument, everything after it must also be a keyword argument.
- **List comprehensions** as a functional, single-line alternative to a
  `for` loop with an `if` and an `append`:
  ```python
  [robot for robot in robots if robot.status != RobotStatus.OFFLINE and robot.is_low_battery(threshold)]
  ```
  This is roughly analogous to a Java Stream pipeline
  (`.filter(...).collect(...)`), compressed into a single expression.

**Pitfall to flag explicitly:** mutable default arguments. `def f(items=[]):`
is a famous Python trap — the empty list is created *once*, at function
definition time, and reused across every call that doesn't pass its
own `items`. We saw the same class of bug avoided today in
`DiagnosticLog.__init__` by using `created_at: Optional[datetime] = None`
and then `self.created_at = created_at or datetime.now()` inside the
body, rather than defaulting the parameter directly to `datetime.now()`.

---

## Deep Dive: Flow Control

`if` / `elif` / `else`, `for`, and `while` all work conceptually the
same as Java, with syntax differences already covered above. Two things
worth calling out from today's code specifically:

- **`for` loops iterate directly over collections**, not indices:
  `for robot in robots:` — no `for (int i = 0; i < robots.size(); i++)`
  equivalent needed. If you need the index too, `enumerate(robots)`
  gives you `(index, robot)` pairs.
- **Truthiness and `or` as a default-fallback idiom:**
  `self.created_at = created_at or datetime.now()` relies on Python
  evaluating `created_at or datetime.now()` left-to-right and returning
  the first "truthy" value. `None` is falsy, so if `created_at` wasn't
  passed, the expression falls through to `datetime.now()`. This
  pattern is idiomatic Python and has no direct one-line Java
  equivalent (Java would typically use a ternary or an explicit
  `if (created_at == null)`).

---

## Deep Dive: Classes & OOP

This is where the Java experience helps most, and where the syntax
differs most. Key points, tied directly to the `Robot` class:

```python
class Robot:
    registry: ClassVar[List["Robot"]] = []
    LOW_BATTERY_THRESHOLD: ClassVar[int] = 20

    def __init__(self, robot_id, serial_number, model, battery_level, facility_id, status=RobotStatus.IDLE):
        self.id = robot_id
        ...
```

- **`__init__` is the constructor.** The double underscores ("dunder")
  mark it as a special method Python calls automatically — comparable
  to a Java constructor matching the class name, but Python only ever
  has one `__init__` (no constructor overloading; you simulate it with
  default arguments instead).
- **`self` must be explicit** in every instance method's parameter
  list, and you use `self.attribute` to reference instance state —
  there's no implicit `this`.
- **Class attributes vs. instance attributes.** `registry` and
  `LOW_BATTERY_THRESHOLD` are declared directly inside the class body
  (outside `__init__`) — they're shared by every instance, the Python
  equivalent of Java's `static` fields. `self.id`, `self.battery_level`,
  etc. are set inside `__init__` and belong to each individual object,
  like normal (non-static) Java fields.
- **`@staticmethod` and `@classmethod`** — `_validate_battery` is a
  `@staticmethod` (no access to instance or class state, just organized
  inside the class, like a `private static` helper in Java).
  `find_by_id` is a `@classmethod` (receives `cls`, the class itself,
  so it can reach the shared `registry`) — closest Java equivalent is a
  `public static Robot findById(int id)` method.
- **`__repr__`** — a dunder method controlling how an object prints.
  Roughly equivalent to overriding `toString()` in Java, though Python
  distinguishes `__repr__` (developer-facing, unambiguous) from
  `__str__` (user-facing) — we only defined `__repr__` today, which
  Python falls back to for both if `__str__` is absent.
- **No access modifiers.** There's no `private`, `protected`, `public`
  keyword. Convention marks "internal" members with a leading
  underscore (`_validate_battery`) — it's a signal to other developers,
  not an enforced restriction. Anyone can still call `robot._validate_battery(50)`
  directly; Python trusts you not to.
- **Optional / union types** — `Optional[int]` (equivalent to
  `int | None`) mirrors Java's `Optional<Integer>` or a nullable
  `Integer`, but Python's `None` can be assigned to *any* variable
  regardless of its type hint; the hint is advisory, not enforced by
  the runtime.

---

## Deep Dive: Pip & Virtual Environments

- **`pip`** is Python's package manager — the rough equivalent of
  Maven/Gradle dependency management, though pip installs packages
  directly rather than managing a project's build lifecycle.
- **Virtual environments (`venv`)** solve the problem of every Python
  project on your machine wanting different (and possibly conflicting)
  package versions. `python -m venv .venv` creates an isolated
  interpreter + package directory scoped to just this project;
  activating it (`source .venv/bin/activate`) points your shell's
  `python` and `pip` commands at that isolated copy instead of the
  system-wide install. This is conceptually similar to how a Java
  project's `pom.xml`/`build.gradle` scopes dependencies to the
  project — except Python's isolation happens at the *interpreter*
  level via `venv`, not just a dependency manifest.
- **`requirements.txt`**, generated via `pip freeze > requirements.txt`,
  is Python's rough equivalent of a `pom.xml`'s dependency list — a
  reproducible record of exactly which packages (and versions) the
  project needs. `bin/setup.sh` (which we'll build out in later days)
  will run `pip install -r requirements.txt` to recreate this
  environment on any machine.

---

## Deep Dive: Python Modules

- A **module** is just a `.py` file. `robot.py` is the `robot` module.
- A **package** is a folder containing an `__init__.py` file — that
  file is what tells Python "treat this folder as an importable unit,"
  and it's also where we curate what the package exposes:
  ```python
  from .facility import Facility
  from .robot import Robot
  ```
  The leading dot (`.facility`) is a **relative import** — "from the
  current package." This is how `app/models/__init__.py` lets the rest
  of the codebase write `from app.models import Robot` instead of
  reaching into `app.models.robot` directly.
- **`if __name__ == "__main__":`** — every Python file has a hidden
  `__name__` variable. When you *run* a file directly, `__name__`
  equals `"__main__"`; when that same file is *imported* by another
  module, `__name__` equals the module's name instead. Guarding your
  script's entry point this way means `scripts/day1_demo.py` can be
  both run directly (`python -m scripts.day1_demo`) and safely imported
  elsewhere later without re-executing `main()`. There's no single Java
  equivalent — it's closest in spirit to Java's `public static void main`,
  except every Python file can potentially have one, and it's opt-in
  rather than a fixed entry-point contract.

---

## Architectural Analysis

Today's four classes are intentionally **not** persisted anywhere —
`registry` is a Python list living in process memory, wiped the moment
the script ends. That's the point. We're isolating "what does the data
look like" (today's question) from "how does it get stored" (Thursday's
question, when `Facility`, `Robot`, `Mission`, and `DiagnosticLog`
become SQLAlchemy models backed by PostgreSQL tables).

Look at how closely today's `__init__` parameters already mirror the
ERD from the problem statement:

```
Robot: id, serial_number, model, status, battery_level, facility_id
```

That's not a coincidence — it's deliberate scaffolding. When we
introduce SQLAlchemy, the *fields* won't change; only the base class
changes (from nothing, to `Base` from `sqlalchemy.orm`), and the
`registry` pattern gets replaced by an actual database session. Every
method you wrote today that operates on plain Python objects
(`is_low_battery`, `find_by_id`) has a near-identical shape once it
becomes a SQLAlchemy query later this week — you're not learning
throwaway code, you're learning the domain.

The `find_low_battery_robots` function is also your first hands-on
encounter with a **business question** from the problem statement,
answered in the cheapest possible way (a list comprehension over an
in-memory list) before you ever see it answered the "real" way (a SQL
`WHERE` clause, then a FastAPI endpoint, then a MUI dashboard card).
That progression — plain Python → SQL → API → UI — is the throughline
for all 13 days.

---

## Common Pitfalls & Anti-Patterns

- **Forgetting `self`.** Leaving `self` off an instance method
  signature (`def is_low_battery(threshold=None):`) causes a
  `TypeError` the moment it's called on an instance, because Python
  automatically passes the instance as the first argument regardless.
- **Mutable default arguments.** `def __init__(self, tags=[]):` shares
  one list across every instance that doesn't pass its own — always
  default to `None` and construct the mutable object inside the
  method body instead.
- **Confusing class attributes with instance attributes.** Writing
  `self.registry = []` inside `__init__` (instead of declaring
  `registry` at the class level) would silently break the pattern —
  every Robot would get its *own* empty registry instead of sharing
  one, and `Robot.registry` would still be an empty list.
- **Reassigning a class attribute through an instance.** `robot.LOW_BATTERY_THRESHOLD = 15`
  creates a *new instance attribute* that shadows the class attribute
  for that one object only — it does not change the shared value.
  Always mutate class-level state via the class itself
  (`Robot.LOW_BATTERY_THRESHOLD = 15`).
- **Circular imports inside a package.** As you add more cross-references
  between models (e.g., a future `Mission` importing `Operator`, which
  imports something from `Mission`), watch for `ImportError: cannot
  import name X from partially initialized module`. The fix is almost
  always to import inside the function that needs it, or to restructure
  so shared types live in a common module both sides import from.
- **Treating `Optional[X]` as a runtime guarantee.** A type hint of
  `Optional[float]` doesn't stop `None` from causing a `TypeError` if
  you then try `battery_level < 20` without checking for `None` first.
  Hints guide humans and tools; they don't guard your code at runtime
  the way Java's compiler does.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | Running a script from the wrong directory, so Python can't resolve the `app` package | Run commands from `backend/` (the directory containing `app/`), and use `python -m scripts.day1_demo` rather than `python scripts/day1_demo.py` |
| `IndentationError: unexpected indent` | Mixed tabs/spaces, or inconsistent indentation width | Configure your editor to insert spaces (4) for tabs; re-indent the offending block consistently |
| `TypeError: __init__() missing 1 required positional argument` | Forgot a required constructor argument, or accidentally used a keyword argument before a positional one | Check the parameter order against the class definition; supply all required positional args before any keyword args |
| `AttributeError: 'NoneType' object has no attribute '...'` | Called `.find_by_id()` and got `None` back (no match), then tried to use it directly | Always check `if result is not None:` before using a lookup's return value |
| Changing `Robot.LOW_BATTERY_THRESHOLD` on one robot doesn't affect others | Accidentally set it on the *instance* (`self.LOW_BATTERY_THRESHOLD = ...`) instead of the class | Set it via the class name directly: `Robot.LOW_BATTERY_THRESHOLD = 15` |
| `(venv) `doesn't appear in your shell prompt after activating | Wrong activation script for your shell/OS, or venv not actually created | Confirm `.venv/` exists; on Windows use `.venv\Scripts\activate`, on macOS/Linux `source .venv/bin/activate` |
| `pip install` succeeds but `import` still fails | venv not activated when `pip install` was run, so the package landed in the system Python instead | Activate the venv first, then reinstall; verify with `which pip` / `where pip` pointing into `.venv` |

---
*RoboPulse Fleet Command Center — Day 1 of 13*
