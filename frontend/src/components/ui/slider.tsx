import React from "react";

export function Slider({
  value,
  onValueChange,
  max = 100,
  step = 1,
  className = "",
}: {
  value: number[];
  onValueChange: (v: number[]) => void;
  max?: number;
  step?: number;
  className?: string;
}) {
  return (
    <input
      type="range"
      value={value[0]}
      max={max}
      step={step}
      onChange={(e) => onValueChange([Number(e.target.value)])}
      className={`w-full ${className}`}
    />
  );
}
