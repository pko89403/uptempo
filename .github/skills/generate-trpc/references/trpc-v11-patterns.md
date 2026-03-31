# tRPC v11 Patterns Reference

## Router Composition

```typescript
import { router } from './trpc';
import { userRouter } from './routers/user';
import { postRouter } from './routers/post';

export const appRouter = router({
  user: userRouter,
  post: postRouter,
});

export type AppRouter = typeof appRouter;
```

Routers are infinitely composable — nest and merge freely.

## Procedure Builder Chain

```typescript
import { publicProcedure, router } from './trpc';
import { z } from 'zod';

export const userRouter = router({
  getById: publicProcedure
    .input(z.object({ id: z.string().uuid() }))
    .output(z.object({
      id: z.string(),
      name: z.string(),
      email: z.string().email(),
    }))
    .query(async ({ input, ctx }) => {
      return ctx.db.user.findUniqueOrThrow({ where: { id: input.id } });
    }),

  create: publicProcedure
    .input(z.object({
      name: z.string().min(1).max(100),
      email: z.string().email(),
    }))
    .mutation(async ({ input, ctx }) => {
      return ctx.db.user.create({ data: input });
    }),
});
```

Chain: `input()` → `output()` → `query()` | `mutation()` | `subscription()`

## Middleware Composition

```typescript
import { initTRPC, TRPCError } from '@trpc/server';

const t = initTRPC.context<Context>().create();

// Public — no auth required
export const publicProcedure = t.procedure;

// Authed — requires valid session
const isAuthed = t.middleware(({ ctx, next }) => {
  if (!ctx.session?.user) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  return next({ ctx: { user: ctx.session.user } });
});
export const authedProcedure = publicProcedure.use(isAuthed);

// Admin — requires admin role
const isAdmin = t.middleware(({ ctx, next }) => {
  if (ctx.user.role !== 'admin') {
    throw new TRPCError({ code: 'FORBIDDEN' });
  }
  return next({ ctx });
});
export const adminProcedure = authedProcedure.use(isAdmin);
```

Middleware stacks: `public → authed → admin` (each adds to context).

## Error Formatting with ZodError

```typescript
const t = initTRPC.context<Context>().create({
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        zodError:
          error.cause instanceof ZodError ? error.cause.flatten() : null,
      },
    };
  },
});
```

Client receives structured validation errors:
```json
{
  "data": {
    "zodError": {
      "fieldErrors": { "email": ["Invalid email"] },
      "formErrors": []
    }
  }
}
```

## React Query Integration

```typescript
// In a React component
import { trpc } from '~/utils/trpc';

function UserProfile({ id }: { id: string }) {
  // Query
  const { data, isLoading } = trpc.user.getById.useQuery({ id });

  // Mutation with optimistic updates
  const utils = trpc.useUtils();
  const updateUser = trpc.user.update.useMutation({
    onSuccess() {
      utils.user.getById.invalidate({ id });
    },
  });

  // Prefetch
  trpc.user.getById.usePrefetchQuery({ id: nextUserId });

  // Suspense query
  const [user] = trpc.user.getById.useSuspenseQuery({ id });
}
```

## Next.js App Router Integration

### Route Handler (app/api/trpc/[trpc]/route.ts)
```typescript
import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from '~/server/routers/_app';
import { createContext } from '~/server/context';

const handler = (req: Request) =>
  fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext,
  });

export { handler as GET, handler as POST };
```

### Server Actions / RSC with createCaller
```typescript
import { createCallerFactory } from '@trpc/server';
import { appRouter } from '~/server/routers/_app';

const createCaller = createCallerFactory(appRouter);

// In a Server Component
export default async function UserPage({ params }: { params: { id: string } }) {
  const caller = createCaller(await createContext());
  const user = await caller.user.getById({ id: params.id });
  return <div>{user.name}</div>;
}
```

### Server Actions
```typescript
'use server';
import { createCaller } from '~/server/caller';

export async function createUser(formData: FormData) {
  const caller = createCaller(await createContext());
  return caller.user.create({
    name: formData.get('name') as string,
    email: formData.get('email') as string,
  });
}
```

## Branded Types & Discriminated Unions with Zod

```typescript
const UserId = z.string().uuid().brand<'UserId'>();
const PostId = z.string().uuid().brand<'PostId'>();

// Discriminated union for polymorphic input
const NotificationInput = z.discriminatedUnion('type', [
  z.object({ type: z.literal('email'), to: z.string().email(), subject: z.string() }),
  z.object({ type: z.literal('sms'), phone: z.string(), body: z.string() }),
  z.object({ type: z.literal('push'), deviceToken: z.string(), title: z.string() }),
]);
```

## Subscription with Async Generators

```typescript
import { observable } from '@trpc/server/observable';

export const chatRouter = router({
  onMessage: authedProcedure
    .input(z.object({ roomId: z.string() }))
    .subscription(async function* ({ input, ctx }) {
      const channel = ctx.pubsub.subscribe(`room:${input.roomId}`);
      try {
        for await (const message of channel) {
          yield message;
        }
      } finally {
        channel.unsubscribe();
      }
    }),
});
```

v11 subscriptions use **async generators** (replacing the `observable()` API).
Connect via `httpSubscriptionLink` (SSE) or `wsLink` (WebSocket).

## Quick Checklist

- [ ] Use `createCallerFactory` for server-side calls (RSC, server actions)
- [ ] Define `output()` schemas for public API procedures
- [ ] Stack middleware for layered auth (public → authed → role)
- [ ] Use `useUtils()` for cache invalidation after mutations
- [ ] Brand IDs with Zod `.brand<>()` for type safety
- [ ] Prefer `httpSubscriptionLink` (SSE) over WebSocket for simpler infra
