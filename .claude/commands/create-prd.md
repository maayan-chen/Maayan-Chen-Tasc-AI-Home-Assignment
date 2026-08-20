---
description: Create a Product Requirements Document from conversation
argument-hint: [output-filename]
---

# Create PRD: Generate Product Requirements Document

## Overview

Generate a comprehensive PRD based on the current conversation context and
requirements discussed.

## Output File

Write the PRD to: `$ARGUMENTS` (default: `PRD.md`)

## PRD Structure

Adapt depth and detail based on available information. Sections that don't
apply to this product should be dropped, not padded.

**1. Executive Summary**
- Concise product overview (2-3 paragraphs)
- Core value proposition
- MVP goal statement

**2. Mission**
- Product mission statement
- Core principles (3-5)

**3. Target Users**
- Primary user personas
- Technical comfort level
- Key user needs and pain points

**4. MVP Scope**
- **In Scope:** Core functionality (✅ checkboxes)
- **Out of Scope:** Deferred features (❌ checkboxes)
- Group by category (Core Functionality, Technical, Integration, Deployment)

**5. User Stories**
- 5-8 stories: "As a [user], I want to [action], so that [benefit]"
- Concrete example for each
- Technical user stories if relevant

**6. Core Architecture & Patterns**
- High-level architecture approach
- Directory structure (if applicable)
- Key design patterns and principles

**7. Features**
- Detailed feature specifications

**8. Technology Stack**
- Technologies with versions
- Dependencies and libraries
- Third-party integrations

**9. Security & Configuration**
- Authentication/authorization approach
- Configuration management (environment variables, secrets)
- Security scope (in-scope and out-of-scope)
- Deployment considerations

**10. API Specification** (if applicable)
- Endpoints, request/response formats, auth requirements, example payloads

**11. Success Criteria**
- MVP success definition
- Functional requirements (✅ checkboxes)
- Quality indicators
- User experience goals

**12. Implementation Phases**
- 3-4 phases; each with Goal, Deliverables (✅), Validation criteria
- Realistic timeline estimates

**13. Future Considerations**
- Post-MVP enhancements

**14. Risks & Mitigations**
- 3-5 key risks with specific mitigation strategies

**15. Appendix** (if applicable)
- Related documents, key dependencies with links

## Instructions

### 1. Extract Requirements
- Review the entire conversation history
- Identify explicit requirements and implicit needs
- Note technical constraints and preferences
- Capture user goals and success criteria

### 2. Synthesize
- Organize requirements into sections
- Fill in reasonable assumptions where details are missing —
  **and list every one of them in the output report**
- Maintain consistency across sections
- Ensure technical feasibility

### 3. Write
- Clear, professional language
- Concrete examples over abstract descriptions
- Markdown formatting (headings, lists, code blocks, checkboxes)

### 4. Quality Checks
- ✅ All applicable sections present
- ✅ User stories have clear benefits
- ✅ MVP scope is realistic and well-defined
- ✅ Technology choices are justified
- ✅ Implementation phases are actionable
- ✅ Success criteria are measurable
- ✅ Consistent terminology throughout

## Style Guidelines

- **Tone:** Professional, clear, action-oriented
- **Checkboxes:** ✅ in-scope, ❌ out-of-scope
- **Specificity:** Concrete over abstract
- **Length:** Comprehensive but scannable

## Output Confirmation

After creating the PRD:
1. Confirm the file path
2. Brief summary of contents
3. **Highlight every assumption made due to missing information** — these are
   where the PRD is most likely to be wrong
4. Suggest next steps (review, refinement, planning)

## Notes

- If critical information is missing, ask before generating
- For highly technical products, emphasize architecture and stack
- For user-facing products, emphasize user stories and experience
- This command contains the complete template — no external references needed
