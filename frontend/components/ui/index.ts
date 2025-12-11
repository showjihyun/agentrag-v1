/**
 * UI Components Index
 * 
 * Centralized exports for all UI components
 */

// Accessible components
export { AccessibleSelect } from './accessible-select';
export type { SelectOption, AccessibleSelectProps } from './accessible-select';

export { ConfirmDialog, useConfirmDialog } from './confirm-dialog';
export type { DialogVariant, ConfirmDialogProps } from './confirm-dialog';

// Re-export existing components
export { Button, buttonVariants } from './button';
export { Input } from './input';
export { Label } from './label';
export { Textarea } from './textarea';
export { Badge } from './badge';
export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';
export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
export { Switch } from './switch';
export { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
export { ScrollArea, ScrollBar } from './scroll-area';
export { Separator } from './separator';
export { Slider } from './slider';
export { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip';
export {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from './alert-dialog';
