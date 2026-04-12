# PROJECT_SPEC: course-engine

## 1. Repo Name
`course-engine`

## 2. One-Sentence Purpose
A Python-based, schema-driven engine for generating validated course manifests and static content from a single YAML source of truth.

## 3. Problem the App Solves
Hand-authoring complex curriculum manifests is error-prone; provides a deterministic "Syllabus-as-Code" approach where content, mapping, and governance scoping are declared in source and compiled.

## 4. Primary User / Audience
Content developers, instructional designers, and DevOps-oriented learning technologists.

## 5. Core Role in the CloudPedagogy Ecosystem
The "Authoring Engine"; creates the actual lesson content, metadata, and structured manifests that power the end-user learning experiences across the ecosystem.

## 6. Main Entities / Data Structures
- **RootModel**: The central configuration object parsing `course.yml`.
- **CourseMetaModel**: Basic identifiers (Title, Version, ID).
- **DesignIntent & AIScoping**: Governance declarations (Scope, position on AI use, decision boundaries).
- **FrameworkAlignment**: Connections to underlying capability frameworks.
- **Syllabus Structure**: Hierarchical collection of Modules, Lessons, and ContentBlocks.

## 7. Main User Workflows
1. **Source Authoring**: Write course content in Markdown and configuration in YAML (`course.yml`).
2. **Governance Declaration**: Define explicit AI-scoping and permitted uses within the course source.
3. **Build Execution**: Run the Python/Quarto build process to validate the schema and generate static artifacts.
4. **Manifest Publication**: Distribute the resulting `manifest.json` for ecosystem consumption.

## 8. Current Features
- Pydantic-based structural validation.
- "Shift-left" governance (Policy and Scoping defined in source).
- Hierarchical lesson-content mapping.
- Support for audience-specific content (Learner vs Instructor).
- Multiple content block types (Quiz, Reflection, Submission).

## 9. Stubbed / Partial / Incomplete Features
- Not explicitly listed.

## 10. Import / Export and Storage Model
- **Storage**: Purely file-system based (YAML/Markdown).
- **Output**: Generates static JSON manifests and HTML/PDF artifacts via Quarto.

## 11. Relationship to Other CloudPedagogy Apps
Implements the high-level capability and governance designs established in other tools; serves as a content source for refactoring and personalization engines.

## 12. Potential Overlap or Duplication Risks
Functionally overlaps with general Static Site Generators; distinguished by its deep, curriculum-specific Pydantic schemas.

## 13. Distinctive Value of This App
"Syllabus-as-Code"—enforces structural and governance integrity at the source-code level using software development best practices (version control, schema validation).

## 14. Recommended Future Enhancements
(Inferred) Direct export path to the `integration-sdk` format for seamless ecosystem sync; automated "Self-Audit" reports based on `ai_scoping` metadata.

## 15. Anything Unclear or Inferred from Repo Contents
The exact build-time transformation from `CourseModel` to final Quarto layouts is handled by internal Python scripts and templates.
