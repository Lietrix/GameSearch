import React, { useState } from "react";

export function Popover({ children }: { children: React.ReactNode }) {
  return <div className="relative inline-block">{children}</div>;
}

export function PopoverTrigger({
  asChild,
  children,
}: {
  asChild?: boolean;
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

export function PopoverContent({
  className = "",
  align,
  children,
}: {
  className?: string;
  align?: string;
  children: React.ReactNode;
}) {
  const [open] = useState(true);
  return open ? (
    <div
      className={`absolute z-10 mt-2 rounded border border-neutral-700 p-2 ${className}`}
    >
      {children}
    </div>
  ) : null;
}
