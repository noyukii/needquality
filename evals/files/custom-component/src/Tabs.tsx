import type { ReactNode } from "react";

export type Tab = { id: string; label: string; panel: ReactNode };

export function Tabs({ tabs }: { tabs: Tab[] }) {
  return <div>{tabs.map((tab) => <div key={tab.id}>{tab.label}</div>)}</div>;
}
