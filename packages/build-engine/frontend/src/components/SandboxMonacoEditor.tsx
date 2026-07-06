import { useRef, useCallback } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';

interface Props {
  value: string;
  language?: string;
  readOnly?: boolean;
  onChange?: (value: string) => void;
  onMount?: (editor: any) => void;
}

const EXT_LANG_MAP: Record<string, string> = {
  py: 'python',
  js: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  jsx: 'javascript',
  json: 'json',
  yaml: 'yaml',
  yml: 'yaml',
  md: 'markdown',
  html: 'html',
  css: 'css',
  sh: 'shell',
  bash: 'shell',
  sql: 'sql',
  toml: 'ini',
  cfg: 'ini',
  txt: 'plaintext',
};

export function getLanguage(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  return EXT_LANG_MAP[ext] || 'plaintext';
}

export default function SandboxMonacoEditor({ value, language, readOnly, onChange, onMount }: Props) {
  const editorRef = useRef<any>(null);

  const handleMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    // 设置 Tab 为 2 空格
    editor.getModel()?.updateOptions({ tabSize: 2, insertSpaces: true });
    onMount?.(editor);
  };

  const handleChange: OnChange = (val) => {
    if (val !== undefined) onChange?.(val);
  };

  return (
    <div className="h-full w-full">
      <Editor
        height="100%"
        defaultLanguage="plaintext"
        language={language}
        value={value}
        onChange={handleChange}
        onMount={handleMount}
        theme="vs"
        options={{
          readOnly: readOnly || false,
          minimap: { enabled: false },
          fontSize: 13,
          fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
          wordWrap: 'on',
          renderWhitespace: 'selection',
          bracketPairColorization: { enabled: true },
          padding: { top: 8 },
        }}
      />
    </div>
  );
}
