/**
 * UI Components Index
 * Centralized exports for all reusable UI components
 */

// Basic Components
export { Button, buttonVariants } from './button';
export type { ButtonProps } from './button';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from './card';

export { Badge, badgeVariants } from './badge';
export type { BadgeProps } from './badge';

export { Progress } from './progress';

export { Textarea } from './textarea';
export type { TextareaProps } from './textarea';

export { Input } from './input';
export type { InputProps } from './input';

export { Label } from './label';

// Advanced Components
export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from './dialog';

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
} from './select';

export { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs';

export { Slider } from './slider';

export {
  Toast,
  ToastProvider,
  ToastViewport,
  ToastTitle,
  ToastDescription,
  ToastClose,
  ToastAction,
} from './toast';
export type { ToastProps, ToastActionElement } from './toast';

export { Toaster } from './toaster';
