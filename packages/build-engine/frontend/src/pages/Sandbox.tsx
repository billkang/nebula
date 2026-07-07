import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import SandboxMonacoEditor, { getLanguage } from '../components/SandboxMonacoEditor';
import FileTreePanel, { FileNode } from '../components/FileTreePanel';
import SandboxHeader from '../components/SandboxHeader';
import SandboxDiffView from '../components/SandboxDiffView';
import SandboxSnapshotPanel from '../components/SandboxSnapshotPanel';

export default function SandboxPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [editorContent, setEditorContent] = useState<string>('');
  const [showDiffPanel, setShowDiffPanel] = useState(false);
  const [showSnapshotsPanel, setShowSnapshotsPanel] = useState(false);
  const [diffResult, setDiffResult] = useState<any>(null);
  const [diffLoading, setDiffLoading] = useState(false);
  const [buildStatus, setBuildStatus] = useState<string>('idle');
  const [buildResult, setBuildResult] = useState<any>(null);
  const unsavedContent = useRef<Map<string, string>>(new Map());

  // 获取项目信息
  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: () => api.projects.get(id!),
    enabled: !!id,
  });

  // 初始化沙箱
  const initMut = useMutation({
    mutationFn: () => api.sandbox.init(id!),
  });

  // 获取沙箱文件树
  const { data: sandboxData, isLoading: filesLoading, refetch: refetchFiles } = useQuery({
    queryKey: ['sandbox-files', id],
    queryFn: () => api.sandbox.files(id!),
    enabled: !!id,
  });

  // 沙箱初始化 + 自动选择第一个文件
  useEffect(() => {
    if (id && !initMut.isIdle) return;
    // 先 init 确保沙箱存在，不阻塞的话
    if (sandboxData?.data?.meta?.initialized) return;
    if (initMut.isIdle) {
      initMut.mutateAsync().then(() => refetchFiles()).catch(() => {});
    }
  }, [id]);

  // 自动选择第一个文件
  useEffect(() => {
    const files = sandboxData?.data?.files;
    if (files && files.length > 0 && !selectedPath) {
      const firstFile = findFirstFile(files);
      if (firstFile) setSelectedPath(firstFile);
    }
  }, [sandboxData]);

  // 选择文件后加载内容
  const fileQuery = useQuery({
    queryKey: ['sandbox-file', id, selectedPath],
    queryFn: () => api.sandbox.getFile(id!, selectedPath!),
    enabled: !!id && !!selectedPath,
  });

  useEffect(() => {
    if (fileQuery.data?.data?.content) {
      // 如果文件有未保存的内容，优先使用
      const key = fileQuery.data.data.path;
      if (unsavedContent.current.has(key)) {
        setEditorContent(unsavedContent.current.get(key)!);
      } else {
        setEditorContent(fileQuery.data.data.content);
      }
    }
  }, [fileQuery.data]);

  // 从原始 Artifact 恢复
  const restoreMut = useMutation({
    mutationFn: () => api.sandbox.restoreOriginal(id!),
    onSuccess: () => {
      setEditorContent('');
      setDiffResult(null);
      unsavedContent.current.clear();
      setShowDiffPanel(false);
      qc.invalidateQueries({ queryKey: ['sandbox-files', id] });
      qc.invalidateQueries({ queryKey: ['sandbox-file', id, selectedPath] });
    },
  });

  // 保存文件
  const saveMut = useMutation({
    mutationFn: ({ path, content }: { path: string; content: string }) =>
      api.sandbox.saveFile(id!, path, content),
    onSuccess: () => {
      const path = saveMut.variables?.path;
      if (path) unsavedContent.current.delete(path);
      qc.invalidateQueries({ queryKey: ['sandbox-files', id] });
    },
  });

  // 触发重建（异步）
  const rebuildMut = useMutation({
    mutationFn: () => api.sandbox.rebuild(id!, undefined, true),
    onSuccess: () => {
      setBuildStatus('running');
    },
    onError: () => setBuildStatus('failed'),
  });

  // 取消重建
  const cancelRebuildMut = useMutation({
    mutationFn: () => api.sandbox.cancelRebuild(id!),
    onSuccess: () => {
      setBuildStatus('idle');
      setBuildResult(null);
    },
  });

  // 轮询构建状态
  useEffect(() => {
    if (buildStatus !== 'running') return;
    const interval = setInterval(async () => {
      try {
        const res = await api.sandbox.rebuildStatus(id!);
        const data = res?.data;
        if (!data) return;
        const terminalStates = ['success', 'failed', 'cancelled'];
        if (terminalStates.includes(data.status)) {
          setBuildResult(data);
          setBuildStatus(data.status);
          qc.invalidateQueries({ queryKey: ['sandbox-files', id] });
          clearInterval(interval);
        }
      } catch {
        // 继续轮询
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [buildStatus, id, qc]);

  // 快照
  const { data: snapshotsData, refetch: refetchSnapshots } = useQuery({
    queryKey: ['sandbox-snapshots', id],
    queryFn: () => api.sandbox.snapshots.list(id!),
    enabled: !!id && showSnapshotsPanel,
  });

  const snapCreateMut = useMutation({
    mutationFn: (desc?: string) => api.sandbox.snapshots.create(id!, desc),
    onSuccess: () => refetchSnapshots(),
  });

  const snapRestoreMut = useMutation({
    mutationFn: (sid: string) => api.sandbox.snapshots.restore(id!, sid),
    onSuccess: () => {
      refetchSnapshots();
      refetchFiles();
      // 重新加载当前文件
      qc.invalidateQueries({ queryKey: ['sandbox-file', id, selectedPath] });
    },
  });

  // --- Event handlers ---

  const handleSaveAll = useCallback(async () => {
    // 保存当前编辑器的内容
    if (selectedPath) {
      await saveMut.mutateAsync({ path: selectedPath, content: editorContent });
    }
    // 保存所有未保存的内容
    const promises: Promise<any>[] = [];
    unsavedContent.current.forEach((content, path) => {
      if (path !== selectedPath) {
        promises.push(api.sandbox.saveFile(id!, path, content));
      }
    });
    await Promise.all(promises);
    unsavedContent.current.clear();
    qc.invalidateQueries({ queryKey: ['sandbox-files', id] });
  }, [id, selectedPath, editorContent]);

  const handleEditorChange = useCallback((value: string) => {
    setEditorContent(value);
    if (selectedPath) {
      unsavedContent.current.set(selectedPath, value);
    }
  }, [selectedPath]);

  const handleRebuild = useCallback(async () => {
    // 保存所有修改再重建
    await handleSaveAll();
    setBuildStatus('running');
    setBuildResult(null);
    rebuildMut.mutate();
  }, [handleSaveAll]);

  const handleCancelRebuild = useCallback(async () => {
    cancelRebuildMut.mutate();
  }, []);

  const handleViewDiff = useCallback(async () => {
    if (!selectedPath) return;
    setDiffLoading(true);
    setShowDiffPanel(true);
    try {
      const result = await api.sandbox.diff(id!, selectedPath);
      setDiffResult(result?.data);
    } catch {
      setDiffResult(null);
    }
    setDiffLoading(false);
  }, [id, selectedPath]);

  const handleRestoreAll = useCallback(async () => {
    if (!window.confirm('确定要恢复到原始 Artifact 版本吗？所有修改将丢失。')) return;
    await restoreMut.mutateAsync();
  }, [id]);

  const handleRestoreSnapshot = useCallback(async (sid: string) => {
    if (!window.confirm(`确定要恢复到快照 ${sid} 吗？当前修改将丢失。`)) return;
    await snapRestoreMut.mutateAsync(sid);
    unsavedContent.current.clear();
    setEditorContent('');
  }, [id]);

  const handleCreateSnapshot = useCallback(async (desc?: string) => {
    await snapCreateMut.mutateAsync(desc);
  }, [id]);

  // Ctrl+S 快捷键
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSaveAll();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleSaveAll]);

  // 当前文件信息
  const currentFileName = selectedPath?.split('/').pop();
  const currentLanguage = currentFileName ? getLanguage(currentFileName) : undefined;
  const modifiedCount = countModified(sandboxData?.data?.files || []);
  const fileCount = countFiles(sandboxData?.data?.files || []);
  const sandboxMeta = sandboxData?.data?.meta;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <SandboxHeader
        projectName={project?.name || ''}
        projectId={id || ''}
        modifiedCount={modifiedCount}
        fileCount={fileCount}
        buildStatus={buildStatus}
        showDiff={showDiffPanel}
        onSaveAll={handleSaveAll}
        onViewDiff={handleViewDiff}
        onRestoreAll={handleRestoreAll}
        onRebuild={handleRebuild}
        onCancelRebuild={handleCancelRebuild}
        onShowSnapshots={() => setShowSnapshotsPanel(!showSnapshotsPanel)}
        onToggleDiffPanel={() => setShowDiffPanel(!showDiffPanel)}
      />

      {/* Rebuild result banner */}
      {buildResult && buildStatus !== 'idle' && (
        <div
          className="flex items-center justify-between border-b px-4 py-2 text-sm"
          style={{
            background:
              buildStatus === 'success'
                ? 'rgba(34, 197, 94, 0.08)'
                : buildStatus === 'failed'
                  ? 'rgba(239, 68, 68, 0.08)'
                  : buildStatus === 'cancelled'
                    ? 'var(--color-bg-layout)'
                    : 'rgba(245, 158, 11, 0.08)',
            borderColor:
              buildStatus === 'success'
                ? 'rgba(34, 197, 94, 0.2)'
                : buildStatus === 'failed'
                  ? 'rgba(239, 68, 68, 0.2)'
                  : buildStatus === 'cancelled'
                    ? 'var(--color-border)'
                    : 'rgba(245, 158, 11, 0.2)',
          }}
        >
          <div className="flex items-center gap-2">
            {buildStatus === 'success' ? (
              <>
                <span>✅ 重建成功</span>
                <span style={{ color: 'var(--color-text-secondary)' }}>
                  — Artifact {buildResult.artifact_version || ''} 已创建
                </span>
                {buildResult.preview_url && (
                  <a
                    href={buildResult.preview_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 rounded px-2 py-0.5 text-xs text-white"
                    style={{ background: 'var(--color-primary)' }}
                  >
                    🚀 在 Runtime 中预览
                  </a>
                )}
                {buildResult.snapshot_id && (
                  <span className="ml-2 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                    快照: {buildResult.snapshot_id}
                  </span>
                )}
              </>
            ) : buildStatus === 'failed' ? (
              <>
                <span>❌ 重建失败</span>
                <span className="ml-1" style={{ color: 'var(--color-text-secondary)' }}>
                  {buildResult?.message || buildResult?.error || ''}
                </span>
              </>
            ) : buildStatus === 'cancelled' ? (
              <>
                <span>⏹️ 构建已取消</span>
                <span className="ml-1" style={{ color: 'var(--color-text-secondary)' }}>
                  未生成新的 Artifact
                </span>
              </>
            ) : (
              <>
                <span
                  className="inline-block h-3 w-3 animate-spin rounded-full border-2"
                  style={{
                    borderColor: 'var(--color-warning)',
                    borderTopColor: 'transparent',
                  }}
                />
                <span>重建中…</span>
              </>
            )}
          </div>
          <button
            onClick={() => { setBuildStatus('idle'); setBuildResult(null); }}
            className="text-xs transition-colors duration-150"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Runtime unavailable warning */}
      {buildResult?.runtime_status === 'runtime_unavailable' && (
        <div
          className="border-b px-4 py-1.5 text-xs"
          style={{
            color: 'var(--color-warning)',
            background: 'rgba(245, 158, 11, 0.08)',
            borderColor: 'rgba(245, 158, 11, 0.2)',
          }}
        >
          ⚠️ Runtime 未运行 — Artifact 已保存到本地
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* File tree panel */}
        <div className="w-56 flex-shrink-0" style={{ background: 'var(--color-bg-container)' }}>
          {filesLoading ? (
            <div className="flex h-full items-center justify-center" style={{ color: 'var(--color-text-secondary)' }}>
              <div className="text-sm">加载中…</div>
            </div>
          ) : !sandboxMeta?.initialized ? (
            <div className="flex h-full items-center justify-center" style={{ color: 'var(--color-text-secondary)' }}>
              <div className="px-3 text-center">
                <div className="mb-2 text-lg">📁</div>
                <button
                  onClick={() => initMut.mutate()}
                  style={{ color: 'var(--color-primary)' }}
                  className="text-xs underline"
                >
                  初始化沙箱
                </button>
              </div>
            </div>
          ) : (
            <FileTreePanel
              files={sandboxData?.data?.files || []}
              selectedPath={selectedPath}
              onSelect={setSelectedPath}
            />
          )}
        </div>

        {/* Editor / Diff panel */}
        {selectedPath && showDiffPanel ? (
          <div className="flex-1">
            <SandboxDiffView diff={diffResult} loading={diffLoading} />
          </div>
        ) : selectedPath ? (
          <div className="flex-1 flex flex-col">
            {/* 文件标签栏 */}
            <div
              className="flex items-center border-b px-2"
              style={{
                borderColor: 'var(--color-border)',
                background: 'var(--color-bg-layout)',
              }}
            >
              <div
                className="flex items-center gap-1 rounded-t border border-b-0 px-3 py-1.5 text-sm"
                style={{
                  background: 'var(--color-bg-container)',
                  borderColor: 'var(--color-border)',
                  color: 'var(--color-text-base)',
                }}
              >
                <span className="text-xs">{currentFileName}</span>
                {unsavedContent.current.has(selectedPath) && (
                  <span
                    className="inline-block h-1.5 w-1.5 rounded-full"
                    style={{ background: 'var(--color-warning)' }}
                  />
                )}
              </div>
            </div>
            {/* 编辑器 */}
            <div className="flex-1">
              <SandboxMonacoEditor
                value={editorContent}
                language={currentLanguage}
                onChange={handleEditorChange}
              />
            </div>
          </div>
        ) : (
          <div
            className="flex flex-1 items-center justify-center"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            <div className="text-center">
              <div className="mb-3 text-3xl">📝</div>
              <p className="text-sm">从左侧文件树选择一个文件开始编辑</p>
              <p className="mt-1 text-xs">修改后保存，点击"重新构建"生成新 Artifact</p>
            </div>
          </div>
        )}

        {/* Snapshot panel */}
        {showSnapshotsPanel && (
          <div className="w-56 flex-shrink-0">
            <SandboxSnapshotPanel
              snapshots={snapshotsData?.data || []}
              onRestore={handleRestoreSnapshot}
              onCreate={handleCreateSnapshot}
              loading={snapCreateMut.isPending || snapRestoreMut.isPending}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function findFirstFile(files: FileNode[]): string | null {
  for (const node of files) {
    if (node.type === 'file') return node.path;
    if (node.children) {
      const found = findFirstFile(node.children);
      if (found) return found;
    }
  }
  return null;
}

function countModified(files: FileNode[]): number {
  let count = 0;
  for (const node of files) {
    if (node.type === 'file' && node.modified) count++;
    if (node.children) count += countModified(node.children);
  }
  return count;
}

function countFiles(files: FileNode[]): number {
  let count = 0;
  for (const node of files) {
    if (node.type === 'file') count++;
    if (node.children) count += countFiles(node.children);
  }
  return count;
}
