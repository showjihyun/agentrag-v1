'use client';

import * as React from "react"
import { cn } from "@/lib/utils"

interface AccordionContextValue {
  value: string | string[]
  onValueChange: (value: string) => void
  type: "single" | "multiple"
}

const AccordionContext = React.createContext<AccordionContextValue | undefined>(undefined)

interface AccordionProps {
  type: "single" | "multiple"
  value?: string | string[]
  onValueChange?: (value: string | string[]) => void
  defaultValue?: string | string[]
  collapsible?: boolean
  children: React.ReactNode
  className?: string
}

const Accordion = ({ type, value: controlledValue, onValueChange, defaultValue, children, className }: AccordionProps) => {
  const [internalValue, setInternalValue] = React.useState<string | string[]>(defaultValue || (type === "multiple" ? [] : ""))
  const value = controlledValue ?? internalValue

  const handleValueChange = (itemValue: string) => {
    let newValue: string | string[]
    
    if (type === "multiple") {
      const currentArray = Array.isArray(value) ? value : []
      newValue = currentArray.includes(itemValue)
        ? currentArray.filter(v => v !== itemValue)
        : [...currentArray, itemValue]
    } else {
      newValue = value === itemValue ? "" : itemValue
    }

    if (controlledValue === undefined) {
      setInternalValue(newValue)
    }
    onValueChange?.(newValue as any)
  }

  return (
    <AccordionContext.Provider value={{ value: value as any, onValueChange: handleValueChange, type }}>
      <div className={cn("space-y-2", className)}>
        {children}
      </div>
    </AccordionContext.Provider>
  )
}

const AccordionItem = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value: string }
>(({ className, value, children, ...props }, ref) => (
  <div ref={ref} className={cn("border-b", className)} data-value={value} {...props}>
    {children}
  </div>
))
AccordionItem.displayName = "AccordionItem"

const AccordionTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, children, ...props }, ref) => {
  const context = React.useContext(AccordionContext)
  if (!context) throw new Error('AccordionTrigger must be used within Accordion')

  const item = (ref as any)?.current?.closest('[data-value]')
  const itemValue = item?.getAttribute('data-value') || ''
  const isOpen = context.type === "multiple" 
    ? Array.isArray(context.value) && context.value.includes(itemValue)
    : context.value === itemValue

  return (
    <button
      ref={ref}
      type="button"
      className={cn(
        "flex flex-1 items-center justify-between py-4 font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180",
        className
      )}
      data-state={isOpen ? "open" : "closed"}
      onClick={() => context.onValueChange(itemValue)}
      {...props}
    >
      {children}
      <svg
        className="h-4 w-4 shrink-0 transition-transform duration-200"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  )
})
AccordionTrigger.displayName = "AccordionTrigger"

const AccordionContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => {
  const context = React.useContext(AccordionContext)
  if (!context) throw new Error('AccordionContent must be used within Accordion')

  const item = (ref as any)?.current?.closest('[data-value]')
  const itemValue = item?.getAttribute('data-value') || ''
  const isOpen = context.type === "multiple"
    ? Array.isArray(context.value) && context.value.includes(itemValue)
    : context.value === itemValue

  if (!isOpen) return null

  return (
    <div
      ref={ref}
      className={cn("pb-4 pt-0", className)}
      {...props}
    >
      {children}
    </div>
  )
})
AccordionContent.displayName = "AccordionContent"

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }
