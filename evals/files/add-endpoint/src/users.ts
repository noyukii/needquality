export type User = {
  id: string
  email: string
  name: string
}

const users: User[] = [
  { id: "u_1", email: "ada@example.com", name: "Ada" },
]

const byEmail = new Map<string, User>()
for (const user of users) {
  byEmail.set(user.email.toLowerCase(), user)
}

export function listUsers(): User[] {
  return users.slice()
}

export function getUser(id: string): User | undefined {
  return users.find((user) => user.id === id)
}

export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

export function requireName(value: string): string {
  const name = value.trim()
  if (name.length === 0) {
    throw new Error("name required")
  }
  return name
}

export function findByEmail(email: string): User | undefined {
  return byEmail.get(email.toLowerCase())
}

/** Unique insert (email key). Throws if email already exists. */
export function insertUser(user: User): void {
  const key = user.email.toLowerCase()
  if (byEmail.has(key)) {
    throw new Error("email taken")
  }
  byEmail.set(key, user)
  users.push(user)
}
