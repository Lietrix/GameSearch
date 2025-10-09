import React from "react";

export function Calendar({
  mode,
  selected,
  onSelect,
  initialFocus,
}: {
  mode?: "range";
  selected?: any;
  onSelect?: (v: any) => void;
  initialFocus?: boolean;
}) {
  return (
    <div className="p-4 text-sm text-neutral-400 border border-neutral-800 rounded">
      <p>📅 Calendar placeholder</p>
      <button
        className="mt-2 px-2 py-1 bg-neutral-700 text-white rounded"
        onClick={() =>
          onSelect?.({
            from: new Date("2025-01-01"),
            to: new Date("2025-12-31"),
          })
        }
      >
        Set Sample Range
      </button>
    </div>
  );
}
