import React from "react";

type TProps = React.TableHTMLAttributes<HTMLTableElement>;
type THeadProps = React.HTMLAttributes<HTMLTableSectionElement>;
type TBodyProps = React.HTMLAttributes<HTMLTableSectionElement>;
type TRProps = React.HTMLAttributes<HTMLTableRowElement>;
type THProps = React.ThHTMLAttributes<HTMLTableCellElement>;
type TDProps = React.TdHTMLAttributes<HTMLTableCellElement>;

export function Table({ className = "", ...props }: TProps) {
  return (
    <table className={`w-full text-sm ${className}`} {...props} />
  );
}

export function TableHeader({ className = "", ...props }: THeadProps) {
  return <thead className={className} {...props} />;
}

export function TableBody({ className = "", ...props }: TBodyProps) {
  return <tbody className={className} {...props} />;
}

export function TableRow({ className = "", ...props }: TRProps) {
  return <tr className={className} {...props} />;
}

export function TableHead({ className = "", ...props }: THProps) {
  return (
    <th
      className={`text-left font-medium p-3 border-b border-neutral-800 ${className}`}
      {...props}
    />
  );
}

export function TableCell({ className = "", ...props }: TDProps) {
  return <td className={`p-3 ${className}`} {...props} />;
}
