import type { ReactNode } from "react";

export type AlertProps = {
  tone?: "info" | "error";
  children: ReactNode;
  className?: string;
};

export function Alert({ tone = "info", children, className }: AlertProps) {
  return (
    <div className={className} role={tone === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}
