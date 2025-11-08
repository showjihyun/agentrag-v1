/**
 * WCAG AAA Accessibility Utilities
 * Implements Level AAA success criteria
 */

/**
 * Calculate contrast ratio between two colors
 */
export function getContrastRatio(color1: string, color2: string): number {
  const l1 = getRelativeLuminance(color1);
  const l2 = getRelativeLuminance(color2);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Get relative luminance of a color
 */
function getRelativeLuminance(color: string): number {
  const rgb = hexToRgb(color);
  if (!rgb) return 0;
  
  const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((val) => {
    const sRGB = val / 255;
    return sRGB <= 0.03928
      ? sRGB / 12.92
      : Math.pow((sRGB + 0.055) / 1.055, 2.4);
  });
  
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Convert hex color to RGB
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

/**
 * Check if contrast meets WCAG AAA standards
 * AAA requires 7:1 for normal text, 4.5:1 for large text
 */
export function meetsWCAG_AAA(
  foreground: string,
  background: string,
  isLargeText: boolean = false
): boolean {
  const ratio = getContrastRatio(foreground, background);
  return isLargeText ? ratio >= 4.5 : ratio >= 7;
}

/**
 * Sign language interpretation support
 */
export interface SignLanguageConfig {
  enabled: boolean;
  provider?: 'video' | 'avatar';
  language?: 'ASL' | 'BSL' | 'JSL';
}

/**
 * Extended audio description
 */
export interface AudioDescriptionConfig {
  enabled: boolean;
  extendedPauses: boolean;
  detailLevel: 'standard' | 'extended';
}

/**
 * Reading level checker
 * WCAG AAA requires lower secondary education level (approximately 9th grade)
 */
export function checkReadingLevel(text: string): {
  level: number;
  meetsAAA: boolean;
  suggestions: string[];
} {
  // Flesch-Kincaid Grade Level
  const sentences = text.split(/[.!?]+/).filter(Boolean).length;
  const words = text.split(/\s+/).filter(Boolean).length;
  const syllables = countSyllables(text);
  
  if (sentences === 0 || words === 0) {
    return { level: 0, meetsAAA: true, suggestions: [] };
  }
  
  const gradeLevel =
    0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59;
  
  const meetsAAA = gradeLevel <= 9; // Lower secondary education level
  
  const suggestions: string[] = [];
  if (!meetsAAA) {
    suggestions.push('Use shorter sentences');
    suggestions.push('Use simpler words');
    suggestions.push('Break complex ideas into multiple sentences');
  }
  
  return { level: Math.round(gradeLevel), meetsAAA, suggestions };
}

/**
 * Count syllables in text (simplified)
 */
function countSyllables(text: string): number {
  const words = text.toLowerCase().split(/\s+/);
  let count = 0;
  
  words.forEach((word) => {
    const vowels = word.match(/[aeiouy]+/g);
    count += vowels ? vowels.length : 0;
  });
  
  return count;
}

/**
 * Context-sensitive help
 */
export interface ContextHelp {
  trigger: 'hover' | 'focus' | 'click';
  content: string;
  position: 'top' | 'bottom' | 'left' | 'right';
  persistent?: boolean;
}

/**
 * Error prevention for legal/financial transactions
 */
export interface ErrorPreventionConfig {
  requireConfirmation: boolean;
  allowReview: boolean;
  allowUndo: boolean;
  confirmationSteps: number;
}

/**
 * Timing adjustable
 * AAA requires no timing or ability to turn off/adjust/extend
 */
export interface TimingConfig {
  hasTimeLimit: boolean;
  canDisable: boolean;
  canAdjust: boolean;
  canExtend: boolean;
  warningTime: number; // seconds before timeout
}

/**
 * No interruptions
 * AAA requires ability to postpone or suppress interruptions
 */
export interface InterruptionConfig {
  canPostpone: boolean;
  canSuppress: boolean;
  emergencyOnly: boolean;
}

/**
 * Re-authentication
 * AAA requires data preservation on re-authentication
 */
export function preserveDataOnReauth(data: any): void {
  sessionStorage.setItem('preserved_data', JSON.stringify(data));
}

export function restoreDataAfterReauth(): any {
  const data = sessionStorage.getItem('preserved_data');
  if (data) {
    sessionStorage.removeItem('preserved_data');
    return JSON.parse(data);
  }
  return null;
}

/**
 * Location-independent navigation
 */
export function provideMultipleWaysToNavigate(): {
  search: boolean;
  sitemap: boolean;
  tableOfContents: boolean;
  breadcrumbs: boolean;
} {
  return {
    search: true,
    sitemap: true,
    tableOfContents: true,
    breadcrumbs: true,
  };
}

/**
 * Section headings
 * AAA requires content to be organized with headings
 */
export function validateHeadingStructure(html: string): {
  valid: boolean;
  issues: string[];
} {
  const issues: string[] = [];
  
  // Check for h1
  if (!html.includes('<h1')) {
    issues.push('Missing h1 heading');
  }
  
  // Check for heading hierarchy
  const headings = html.match(/<h[1-6]/g) || [];
  let prevLevel = 0;
  
  headings.forEach((heading) => {
    const level = parseInt(heading.charAt(2));
    if (level > prevLevel + 1) {
      issues.push(`Heading level skipped: h${prevLevel} to h${level}`);
    }
    prevLevel = level;
  });
  
  return {
    valid: issues.length === 0,
    issues,
  };
}

/**
 * Link purpose from link text alone
 * AAA requires link purpose to be clear from link text
 */
export function validateLinkText(linkText: string): {
  valid: boolean;
  suggestion?: string;
} {
  const ambiguousTexts = ['click here', 'read more', 'here', 'more', 'link'];
  
  const isAmbiguous = ambiguousTexts.some((text) =>
    linkText.toLowerCase().includes(text)
  );
  
  return {
    valid: !isAmbiguous && linkText.length > 3,
    suggestion: isAmbiguous
      ? 'Use descriptive link text that explains the destination'
      : undefined,
  };
}

/**
 * Unusual words
 * AAA requires definitions for unusual words
 */
export interface UnusualWordConfig {
  word: string;
  definition: string;
  pronunciation?: string;
}

/**
 * Abbreviations
 * AAA requires expanded form for abbreviations
 */
export function expandAbbreviation(abbr: string): string | null {
  const abbreviations: Record<string, string> = {
    API: 'Application Programming Interface',
    LLM: 'Large Language Model',
    RAG: 'Retrieval-Augmented Generation',
    UI: 'User Interface',
    UX: 'User Experience',
    // Add more as needed
  };
  
  return abbreviations[abbr.toUpperCase()] || null;
}

/**
 * Pronunciation
 * AAA requires pronunciation for words where meaning is ambiguous
 */
export interface PronunciationGuide {
  word: string;
  pronunciation: string;
  audioUrl?: string;
}
