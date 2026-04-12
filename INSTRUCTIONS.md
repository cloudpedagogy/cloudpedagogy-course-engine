# Course Engine — User Instructions

---
### 2. What This Tool Does
The Course Engine acts as a technical compiler, translating raw, disconnected curriculum resources into cohesive, portable outputs (like structured packages). It automates the technical assembly of curriculum maps into usable deployment formats.

---
### 3. Role in the Ecosystem
- **Phase:** Phase 5 — Infrastructure
- **Role:** Technical compiler for building structured, portable curriculum outputs.
- **Reference:** [../SYSTEM_OVERVIEW.md](../SYSTEM_OVERVIEW.md)

---
### 4. When to Use This Tool
- When a validated curriculum needs to be packaged for deployment to a Virtual Learning Environment (VLE) or Learning Management System (LMS).
- To execute a bulk generation of structured documentation files from a raw JSON map.

---
### 5. Inputs
- Primary input is a validated, complete JSON curriculum schema, typically finalized in the Mapping or Personalisation tools.

---
### 6. How to Use (Step-by-Step)
1. Point the engine to the final JSON specification document of the approved curriculum.
2. Select the target build format or output structure required by the institution.
3. Initiate the compilation routine.
4. Review the build logs for any missing assets or structural errors during assembly.
5. Retrieve the generated output packages from the designated build directory.

---
### 7. Key Outputs
- Compiled learning packages ready for deployment.
- Detailed build logs indicating compilation success or failure.

---
### 8. How It Connects to Other Tools
- **Upstream:** Consumes finished structural models from tools like the **Mapping Engine**.
- **Downstream:** Outputs might be further styled or prepared for publication via the **Research Object Template**.

---
### 9. Limitations
- It is a compiler, not an editor. If a curriculum has flaws, you must fix them in the upstream design tools, not here.
- Strictly requires fully compliant schema inputs to trigger a successful build.

---
### 10. Tips
- Always check the validation warnings in the Course Engine; it frequently catches subtle structural errors that humans missed during design.
