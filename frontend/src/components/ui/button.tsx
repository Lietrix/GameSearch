import React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "outline" | "ghost";
  size?: "default" | "icon";
};

export function Button({
  variant = "default",
  size = "default",
  className = "",
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-md px-3 py-2 text-sm";
  const byVariant: Record<string, string> = {
    default: "bg-neutral-700 hover:bg-neutral-600 text-white",
    secondary: "bg-neutral-800 text-neutral-200",
    outline: "border border-neutral-700 bg-transparent",
    ghost: "bg-transparent hover:bg-neutral-800/40",
  };
  const bySize: Record<string, string> = {
    default: "",
    icon: "h-9 w-9 p-0",
  };
  return (
    <button
      className={`${base} ${byVariant[variant]} ${bySize[size]} ${className}`}
      {...props}
    />
  );
}
