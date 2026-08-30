export type Invoice = {
  id: string
  ownerId: string
  total: string
}

const invoices: Invoice[] = [
  { id: "inv_1", ownerId: "u_ada", total: "10.00" },
  { id: "inv_2", ownerId: "u_other", total: "99.00" },
]

export function getSession(): { userId: string } {
  return { userId: "u_ada" }
}

export function findById(id: string): Invoice | undefined {
  return invoices.find((row) => row.id === id)
}

export function insertInvoice(row: Invoice): Invoice {
  invoices.push(row)
  return row
}
