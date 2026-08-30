export type Slot = {
  id: string
  reserved: boolean
}

const slots = new Map<string, Slot>([["s_1", { id: "s_1", reserved: false }]])

export function getSlot(id: string): Slot | undefined {
  const slot = slots.get(id)
  return slot ? { ...slot } : undefined
}

export function saveSlot(slot: Slot): void {
  slots.set(slot.id, { ...slot })
}

/** Compare-and-set. Returns false if the stored reserved flag !== expected. */
export function compareAndSetReserved(
  id: string,
  expected: boolean,
  next: boolean,
): boolean {
  const current = slots.get(id)
  if (!current || current.reserved !== expected) {
    return false
  }
  slots.set(id, { ...current, reserved: next })
  return true
}
