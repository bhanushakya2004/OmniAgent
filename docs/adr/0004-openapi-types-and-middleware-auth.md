# ADR 0004: OpenAPI-First Type Synchronization and Route Protection

## Status
Accepted

## Context
In a dual-sided phygital application involving diverse entities (shoppers, merchants, store inventory coordinates, multi-agent timelines), frontend and backend contracts risk drifting if types are manually written or synchronized ad-hoc. Furthermore, strict client-side and edge route protection is required to isolate shopper and merchant experiences.

## Decision
1. **Automated OpenAPI Type Generation:**
   - The FastAPI backend generates standard OpenAPI 3.1 specifications (`docs/openapi.json`).
   - `openapi-typescript` compiles the specification into strongly typed TypeScript schemas (`apps/web/src/lib/api-types.ts`).
   - The build process and CI verify that TypeScript types match the API schema (`make types`), preventing schema drift.
2. **Next.js Edge Middleware Route Protection:**
   - Next.js `middleware.ts` acts as a fast first-line defense before React components hydrate.
   - It checks session cookies (`omni_logged_in`, `omni_role`).
   - Redirects unauthenticated shoppers from `/app/*` to `/login?redirect=...`.
   - Isolates roles: Shoppers accessing `/merchant/*` are redirected to `/app`, and merchants accessing `/app/*` are redirected to `/merchant`.
   - The backend API independently validates every request with cryptographic JWT and RBAC dependencies (defense-in-depth).
3. **Single-Flight Refresh Token Interceptor:**
   - The frontend `apiClient` manages 401 Unauthorized responses with a mutex queue, rotating the refresh token via HttpOnly cookies and seamlessly replaying failed requests without user disruption.

## Consequences
- Complete compile-time type safety across both frontend and backend services.
- Seamless developer experience: backend schema changes propagate directly to frontend TypeScript components.
- Zero risk of unauthorized cross-persona data leakage between shoppers and merchants.
