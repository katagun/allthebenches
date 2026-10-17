import * as React from 'react';
import { cn } from '@/lib/utils';
export function Table({ className, containerClassName, ...props }: React.ComponentProps<'table'> & { containerClassName?: string }) { return <div data-slot="table-container" className={cn('relative w-full overflow-auto', containerClassName)} tabIndex={containerClassName ? 0 : undefined}><table data-slot="table" className={cn('w-full caption-bottom text-sm', className)} {...props} /></div>; }
export function TableHeader({ className, ...props }: React.ComponentProps<'thead'>) { return <thead className={cn('[&_tr]:border-b', className)} {...props} />; }
export function TableBody({ className, ...props }: React.ComponentProps<'tbody'>) { return <tbody className={cn('[&_tr:last-child]:border-0', className)} {...props} />; }
export function TableFooter({ className, ...props }: React.ComponentProps<'tfoot'>) { return <tfoot className={cn('bg-muted/50 border-t font-medium [&>tr]:last:border-b-0', className)} {...props} />; }
export function TableRow({ className, ...props }: React.ComponentProps<'tr'>) { return <tr className={cn('hover:bg-muted/40 data-[state=selected]:bg-muted border-b transition-colors', className)} {...props} />; }
export function TableHead({ className, ...props }: React.ComponentProps<'th'>) { return <th className={cn('text-muted-foreground h-12 px-3 text-left align-middle font-medium whitespace-nowrap [&:has([role=checkbox])]:pr-0', className)} {...props} />; }
export function TableCell({ className, ...props }: React.ComponentProps<'td'>) { return <td className={cn('p-3 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0', className)} {...props} />; }
