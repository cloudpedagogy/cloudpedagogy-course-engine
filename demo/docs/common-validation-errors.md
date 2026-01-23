# Common Validation Errors  
**CloudPedagogy Course Engine v1.5**

This document explains the **most common schema validation errors**, what they *actually mean*, and **exactly how to fix them**.

It is written to help **end users** debug errors without needing to read the engine source code.

---

## How to Read Course Engine Errors

Most errors come from **Pydantic schema validation**.  
They usually follow this pattern:

```
ValidationError: X validation errors for RootModel
<section>.<field>
  Input should be a valid <type>
```

### Key principle

> **Almost all errors are caused by incorrect YAML *shape*, not incorrect content.**

---

## 1. `framework_alignment.domains` — “Input should be a valid list”

### ❌ Error message

```
framework_alignment.domains
Input should be a valid list
```

### ❌ Cause

You wrote a dictionary instead of a list.

```yaml
framework_alignment:
  domains:
    awareness: "AI Awareness & Orientation"
```

### ✅ Fix

Use a **list of strings** only:

```yaml
framework_alignment:
  domains:
    - "awareness"
    - "co-agency"
    - "practice"
```

---

## 2. `framework_alignment.domains.X` — “Input should be a valid string”

### ❌ Error message

```
framework_alignment.domains.0
Input should be a valid string
```

### ❌ Cause

You used objects inside the list:

```yaml
domains:
  - id: "awareness"
    name: "AI Awareness & Orientation"
```

### ✅ Fix

Use **plain strings only**:

```yaml
domains:
  - "awareness"
```

---

## 3. `capability_mapping.domains` — “Input should be a valid dict”

### ❌ Error message

```
capability_mapping.domains
Input should be a valid dictionary
```

### ❌ Cause

You supplied a list instead of a dictionary:

```yaml
capability_mapping:
  domains:
    - "awareness"
```

### ✅ Fix

Use a **dictionary of domain objects**:

```yaml
capability_mapping:
  domains:
    awareness:
      name: "AI Awareness & Orientation"
```

---

## 4. Confusing Alignment vs Mapping (Most Common Mistake)

Alignment = *declares*  
Mapping = *describes*

---

## 5. Markdown Source Not Found

### ❌ Error message

```
FileNotFoundError: lesson.md
```

### ✅ Fix

Ensure paths are relative to `content.root`.

---

## 6. Version Mismatch (1.4 vs 1.5)

### ❌ Symptom

```
Builder: course-engine 1.4.0
```

### ✅ Fix

```bash
pip uninstall -y course-engine
pip install -e .
```

Confirm both module and dist versions match.

---

## Final Advice

Start from a working template, change **values only**, and run `inspect` early and often.
