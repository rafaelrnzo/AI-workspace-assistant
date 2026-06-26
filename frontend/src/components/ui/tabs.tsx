import * as React from 'react'

import { cn } from '@/lib/utils'

function TabsList({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('inline-flex h-10 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground', className)}
      {...props}
    />
  )
}

function TabsTrigger({
  className,
  active,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { active?: boolean }) {
  return (
    <button
      className={cn(
        'inline-flex h-8 items-center justify-center gap-1.5 whitespace-nowrap rounded-md px-3 text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4',
        active && 'bg-background text-foreground shadow-sm',
        className,
      )}
      {...props}
    />
  )
}

export { TabsList, TabsTrigger }
