# GraphQL Schema Design Patterns Reference

## Relay Connection Spec (Cursor-Based Pagination)

```graphql
type Query {
  users(first: Int, after: String, last: Int, before: String): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

Cursors should be **opaque** (base64-encoded). Never expose raw IDs or offsets.

## Mutation Input/Payload Pattern

```graphql
input CreateUserInput {
  name: String!
  email: String!
  clientMutationId: String    # Optional Relay compat
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!       # Domain errors (not exceptions)
}

type UserError {
  field: [String!]!           # Path to problematic field
  message: String!
  code: UserErrorCode!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
}
```

Always return a **payload type** (never the entity directly) for extensibility.

## Subscription Filter Pattern

```graphql
type Subscription {
  orderUpdated(customerId: ID, status: OrderStatus): OrderEvent!
}

type OrderEvent {
  order: Order!
  previousStatus: OrderStatus
  timestamp: DateTime!
}
```

Filter at the resolver level — only push events matching subscription args.

## Nullability Philosophy

| Approach | Convention | Trade-off |
|----------|-----------|-----------|
| **Nullable by default** | `field: String` | Resilient — partial failures don't cascade |
| **Non-null by default** | `field: String!` | Strict — clients get guarantees |

**Recommendation**: Make fields non-null (`!`) when the value is *always* available.
Use nullable for fields that may fail independently (e.g., joined data from other services).

Lists: prefer `[Item!]!` (non-null list of non-null items) over `[Item]`.

## Interface vs Union

```graphql
# Interface: shared fields, subtypes add more
interface Node {
  id: ID!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Union: no shared fields, completely distinct types
union SearchResult = User | Post | Comment

type Query {
  search(query: String!): [SearchResult!]!
  node(id: ID!): Node          # Global object identification
}
```

Use **interface** when types share behavior. Use **union** for heterogeneous result sets.

## Custom Scalar Definitions

```graphql
scalar DateTime    # ISO 8601: "2024-01-15T10:30:00Z"
scalar Date        # "2024-01-15"
scalar JSON        # Escape hatch — use sparingly
scalar URL         # Validated URL string
scalar EmailAddress
scalar UUID
scalar BigInt      # For values exceeding JS Number.MAX_SAFE_INTEGER
```

Always document the format in schema description. Validate on input and serialize on output.

## N+1 Prevention (DataLoader Pattern)

```javascript
// Without DataLoader: N+1 queries
// users.map(u => db.getOrders(u.id))  — 1 query per user

// With DataLoader: batched into 1 query
const orderLoader = new DataLoader(async (userIds) => {
  const orders = await db.getOrdersByUserIds(userIds);
  return userIds.map(id => orders.filter(o => o.userId === id));
});

// Resolver
User: {
  orders: (user) => orderLoader.load(user.id)
}
```

**Hints for schema design**:
- Design resolvers around DataLoader batch keys
- Use `@defer` for expensive fields clients may not always need
- Avoid deeply nested types that trigger cascading N+1 chains

## @deprecated Directive

```graphql
type User {
  name: String! @deprecated(reason: "Use `displayName` instead")
  displayName: String!

  email: String!
  emailAddress: String! @deprecated(reason: "Use `email`. Removed in v4.")
}

type Query {
  user(id: ID!): User @deprecated(reason: "Use `node(id:)` with Node interface")
}
```

- Always provide a `reason` with migration path
- Deprecated fields still work but are hidden in introspection tools
- Monitor usage before removing (check query analytics)

## Schema Design Checklist

- [ ] Implement `Node` interface for global object identification
- [ ] Use Relay connection spec for all paginated lists
- [ ] Return payload types from mutations (not raw entities)
- [ ] Add `totalCount` to connections
- [ ] Define custom scalars for domain-specific types
- [ ] Use DataLoader in every list-of-related-entities resolver
- [ ] Mark obsolete fields `@deprecated` with reason before removal
