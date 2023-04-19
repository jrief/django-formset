import { Extension } from '@tiptap/core'

export interface FirstLineAlignOptions {
	HTMLAttributes: Record<string, any>,
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    firstLineAlign: {
      setIndent: () => ReturnType,
      unsetIndent: () => ReturnType,
      toggleIndent: () => ReturnType,
      setOutdent: () => ReturnType,
      unsetOutdent: () => ReturnType,
      toggleOutdent: () => ReturnType,
    }
  }
}

export const FirstLineAlign = Extension.create<FirstLineAlignOptions>({
  name: 'firstLineAlign',

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addCommands() {
    return {
      setIndent: () => ({ commands }) => {
        return commands.updateAttributes('style', { 'text-align': '3em' });
      },
      toggleIndent: () => ({ commands }) => {
        return commands.updateAttributes('style', { 'text-align': '3em' });
      },
      unsetIndent: () => ({ commands }) => {
        return commands.updateAttributes('style', { 'text-align': '3em' });
      },
      setOutdent: () => ({ commands }) => {
        return commands.updateAttributes('xyz', { textAlign: 'XYZ' });
      },
      toggleOutdent: () => ({ commands }) => {
        return commands.updateAttributes('xyz', { textAlign: 'XYZ' });
      },
      unsetOutdent: () => ({ commands }) => {
        return commands.updateAttributes('xyz', { textAlign: 'XYZ' });
      },
    }
  },
});
