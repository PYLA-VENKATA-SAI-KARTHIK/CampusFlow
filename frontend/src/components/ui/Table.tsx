import React, { forwardRef } from 'react';

export const TableContainer = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`w-full overflow-x-auto rounded-xl border border-slate-200/80 bg-white shadow-xs ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);
TableContainer.displayName = 'TableContainer';

export const Table = forwardRef<HTMLTableElement, React.TableHTMLAttributes<HTMLTableElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <table
        ref={ref}
        className={`w-full text-left text-xs text-slate-600 divide-y divide-slate-100 ${className}`}
        {...props}
      >
        {children}
      </table>
    );
  }
);
Table.displayName = 'Table';

export const TableHeader = forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <thead
        ref={ref}
        className={`bg-slate-50/90 text-slate-500 font-bold uppercase tracking-wider text-[11px] ${className}`}
        {...props}
      >
        {children}
      </thead>
    );
  }
);
TableHeader.displayName = 'TableHeader';

export const TableBody = forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <tbody
        ref={ref}
        className={`divide-y divide-slate-100 bg-white font-medium ${className}`}
        {...props}
      >
        {children}
      </tbody>
    );
  }
);
TableBody.displayName = 'TableBody';

export const TableRow = forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <tr
        ref={ref}
        className={`hover:bg-slate-50/80 transition-colors duration-100 ${className}`}
        {...props}
      >
        {children}
      </tr>
    );
  }
);
TableRow.displayName = 'TableRow';

export const TableHead = forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <th
        ref={ref}
        className={`px-4 py-3.5 font-bold text-slate-700 whitespace-nowrap ${className}`}
        {...props}
      >
        {children}
      </th>
    );
  }
);
TableHead.displayName = 'TableHead';

export const TableCell = forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <td
        ref={ref}
        className={`px-4 py-3.5 text-slate-700 whitespace-nowrap align-middle ${className}`}
        {...props}
      >
        {children}
      </td>
    );
  }
);
TableCell.displayName = 'TableCell';

export const TableEmpty: React.FC<{ colSpan: number; message?: string }> = ({
  colSpan,
  message = 'No records found',
}) => {
  return (
    <tr>
      <td colSpan={colSpan} className="px-6 py-12 text-center text-slate-400">
        <div className="flex flex-col items-center justify-center space-y-2">
          <svg
            className="w-8 h-8 text-slate-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <span className="text-xs font-semibold text-slate-500">{message}</span>
        </div>
      </td>
    </tr>
  );
};
