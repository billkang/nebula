import { useState } from 'react';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  modified?: boolean;
}

interface Props {
  files: FileNode[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
}

export default function FileTreePanel({ files, selectedPath, onSelect }: Props) {
  return (
    <div
      className="h-full overflow-auto border-r"
      style={{
        background: 'var(--color-bg-layout)',
        borderColor: 'var(--color-border)',
      }}
    >
      <div
        className="flex items-center border-b px-3 py-2 text-xs font-semibold uppercase tracking-wider"
        style={{
          color: 'var(--color-text-secondary)',
          borderColor: 'var(--color-border)',
        }}
      >
        文件
      </div>
      <div className="py-1">
        {files.map((node) => (
          <FileTreeNode
            key={node.path}
            node={node}
            depth={0}
            selectedPath={selectedPath}
            onSelect={onSelect}
          />
        ))}
        {files.length === 0 && (
          <div className="px-3 py-4 text-center text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            暂无文件
          </div>
        )}
      </div>
    </div>
  );
}

function FileTreeNode({ node, depth, selectedPath, onSelect }: {
  node: FileNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isDir = node.type === 'directory';
  const isSelected = selectedPath === node.path;

  if (node.name.startsWith('.')) return null;

  return (
    <div>
      <div
        className="flex cursor-pointer select-none items-center gap-1 px-2 py-1 text-sm"
        style={{
          paddingLeft: `${8 + depth * 16}px`,
          background: isSelected ? 'var(--sidebar-active-bg)' : 'transparent',
          color: isSelected ? 'var(--color-primary)' : 'var(--sidebar-text)',
        }}
        onMouseEnter={(e) => {
          if (!isSelected)
            e.currentTarget.style.background = 'var(--sidebar-active-bg)';
        }}
        onMouseLeave={(e) => {
          if (!isSelected)
            e.currentTarget.style.background = 'transparent';
        }}
        onClick={() => {
          if (isDir) {
            setExpanded(!expanded);
          } else {
            onSelect(node.path);
          }
        }}
      >
        {isDir ? (
          <span className="w-4 flex-shrink-0" style={{ color: 'var(--color-text-secondary)' }}>
            {expanded ? '▾' : '▸'}
          </span>
        ) : (
          <span className="w-4 flex-shrink-0" style={{ color: 'var(--color-text-secondary)' }}>{getFileIcon(node.name)}</span>
        )}
        <span className="flex-1 truncate">{node.name}</span>
        {node.modified && (
          <span
            className="h-2 w-2 flex-shrink-0 rounded-full"
            style={{ background: 'var(--color-warning)' }}
            title="已修改"
          />
        )}
      </div>
      {isDir && expanded && node.children?.map((child) => (
        <FileTreeNode
          key={child.path}
          node={child}
          depth={depth + 1}
          selectedPath={selectedPath}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

function getFileIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  switch (ext) {
    case 'py': return '🐍';
    case 'js':
    case 'jsx': return '🟨';
    case 'ts':
    case 'tsx': return '🔵';
    case 'json': return '📋';
    case 'yaml':
    case 'yml': return '📄';
    case 'md': return '📝';
    case 'html': return '🌐';
    case 'css': return '🎨';
    case 'sh':
    case 'bash': return '⚡';
    case 'toml':
    case 'cfg':
    case 'ini': return '⚙️';
    case 'sql': return '🗃️';
    case 'txt': return '📄';
    default: return '📄';
  }
}
