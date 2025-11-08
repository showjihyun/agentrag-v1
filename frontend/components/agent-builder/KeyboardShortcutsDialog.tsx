'use client';

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Keyboard } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

const shortcuts = [
  {
    category: 'Navigation',
    items: [
      { keys: ['Tab'], description: 'Move to next interactive element' },
      { keys: ['Shift', 'Tab'], description: 'Move to previous interactive element' },
      { keys: ['Enter'], description: 'Activate button or link' },
      { keys: ['Esc'], description: 'Close dialog or cancel action' },
    ],
  },
  {
    category: 'Agent Builder',
    items: [
      { keys: ['Ctrl', 'K'], description: 'Quick search' },
      { keys: ['Ctrl', 'N'], description: 'Create new agent' },
      { keys: ['Ctrl', 'S'], description: 'Save current work' },
      { keys: ['Ctrl', '/'], description: 'Show keyboard shortcuts' },
    ],
  },
  {
    category: 'Editor',
    items: [
      { keys: ['Ctrl', 'Space'], description: 'Trigger autocomplete' },
      { keys: ['Ctrl', 'Z'], description: 'Undo' },
      { keys: ['Ctrl', 'Y'], description: 'Redo' },
      { keys: ['Ctrl', 'F'], description: 'Find in editor' },
    ],
  },
  {
    category: 'Accessibility',
    items: [
      { keys: ['Alt', '1'], description: 'Skip to main content' },
      { keys: ['?'], description: 'Show help' },
    ],
  },
];

export function KeyboardShortcutsDialog() {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon"
          aria-label="Show keyboard shortcuts"
          title="Keyboard shortcuts (Ctrl+/)"
        >
          <Keyboard className="h-5 w-5" aria-hidden="true" />
        </Button>
      </DialogTrigger>
      <DialogContent 
        className="max-w-2xl dark:bg-gray-900"
        aria-labelledby="shortcuts-title"
      >
        <DialogHeader>
          <DialogTitle id="shortcuts-title">Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Use these keyboard shortcuts to navigate faster
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-6">
            {shortcuts.map((section) => (
              <div key={section.category}>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground">
                  {section.category}
                </h3>
                <div className="space-y-2">
                  {section.items.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-accent transition-colors"
                    >
                      <span className="text-sm">{item.description}</span>
                      <div className="flex gap-1">
                        {item.keys.map((key, keyIndex) => (
                          <React.Fragment key={keyIndex}>
                            <Badge 
                              variant="outline" 
                              className="font-mono text-xs px-2 py-1 dark:bg-gray-800"
                            >
                              {key}
                            </Badge>
                            {keyIndex < item.keys.length - 1 && (
                              <span className="text-muted-foreground mx-1">+</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
