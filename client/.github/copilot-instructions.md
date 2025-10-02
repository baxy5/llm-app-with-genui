# Copilot Instructions for LLM App with Generative UI

## Project Overview
This is a Next.js 15 application built for AI-powered generative UI interactions. The project features a comprehensive set of pre-built AI conversation components and follows modern React patterns with TypeScript.

## Key Architecture Patterns

### AI Elements Component Library
- **Location**: `src/components/ai-elements/`
- **Purpose**: Specialized components for AI chat interfaces and generative UI
- **Key Components**:
  - `conversation.tsx` - Chat container with auto-scroll using `use-stick-to-bottom`
  - `message.tsx` - Message bubbles with role-based styling (`user` vs `assistant`)
  - `prompt-input.tsx` - Complex input component with attachments and rich interactions
  - `artifact.tsx` - Containers for AI-generated content with headers and actions
  - `actions.tsx` - Reusable action buttons with tooltips
  - `code-block.tsx`, `image.tsx`, `web-preview.tsx` - Content display components

### Component Patterns
- **Variant-based styling**: Uses `class-variance-authority` (CVA) for component variants
- **Composition over configuration**: Components export multiple related components (e.g., `Artifact`, `ArtifactHeader`, `ArtifactClose`)
- **Accessibility-first**: All interactive components include `sr-only` labels and proper ARIA attributes
- **Utility-first CSS**: Tailwind with custom `cn()` utility function for conditional classes

### UI Foundation
- **shadcn/ui**: Base components in `src/components/ui/` using Radix UI primitives
- **Style**: "new-york" variant with zinc base color and CSS variables
- **Icons**: Lucide React throughout the codebase
- **Fonts**: Geist Sans and Geist Mono from `next/font/google`

## Tech Stack Specifics

### Dependencies to Know
- **AI SDK**: `ai` package (v5.0.41) - likely for AI model integration
- **Streaming**: `streamdown` for markdown streaming
- **Syntax Highlighting**: `react-syntax-highlighter` for code blocks
- **Token Analysis**: `tokenlens` for token counting/analysis
- **Auto-scroll**: `use-stick-to-bottom` for chat interfaces

### Development Commands
- `npm run dev` - Development server
- `npm run build` - Production build
- `npm run lint` - ESLint with Next.js config

## File Conventions

### Import Patterns
```tsx
// Always use @ alias for internal imports
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// External imports first, then internal
import { type ComponentProps } from "react";
import type { UIMessage } from "ai";
```

### Component Structure
```tsx
// Export types for all component props
export type ComponentNameProps = ComponentProps<"div"> & {
  customProp?: string;
};

// Use forwardRef patterns where appropriate
export const ComponentName = ({ className, ...props }: ComponentNameProps) => (
  <div className={cn("base-classes", className)} {...props} />
);
```

### CSS Class Patterns
- Use group modifiers for parent-child interactions: `group-[.is-user]:bg-primary`
- Role-based styling with semantic classes: `is-user`, `is-assistant`
- Responsive design with Tailwind breakpoints
- Consistent spacing with gap utilities

## Key Integration Points

### AI Message Flow
The app is structured around AI conversation patterns:
1. `conversation.tsx` manages the chat container and auto-scroll
2. `message.tsx` handles message display with role-based styling
3. `prompt-input.tsx` captures user input with rich attachment support
4. Various content components (`artifact`, `code-block`, etc.) display AI responses

### Styling System
- Global styles in `src/app/globals.css`
- Tailwind config uses CSS variables for theming
- `cn()` utility in `src/lib/utils.ts` merges Tailwind classes safely
- Dark mode support through CSS variables

## Common Tasks

### Adding New AI Elements
1. Create component in `src/components/ai-elements/`
2. Follow the established export pattern (component + props type)
3. Use CVA for variants if multiple styles needed
4. Include accessibility attributes and tooltips
5. Test with both user and assistant message contexts

### Extending UI Components
1. Check if shadcn/ui component exists in `src/components/ui/`
2. Use `npx shadcn@latest add component-name` for new shadcn components
3. Customize in place rather than wrapping (shadcn philosophy)

### Working with AI SDK
- The `ai` package is integrated but implementation details aren't visible in current files
- Look for usage patterns in main app files for AI integration examples
- Consider streaming patterns given `streamdown` dependency