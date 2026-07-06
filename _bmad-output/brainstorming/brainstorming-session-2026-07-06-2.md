# Brainstorming Session：Phase 2 Docker 容器化编码执行

> 日期：2026-07-06
> 参与者：Bill、Claude
> Change：docker-executor

## 讨论主题

将 Nebula 平台的编码执行器和构建验证器从本地 subprocess 改造为 Docker 容器化执行，实现环境隔离和可复现性。

## 项目背景

当前 MVP v1 的编码执行流程是：
```
LangGraph Agent → ExecutorService.subprocess("claude code")  # 宿主机直接调
                 → BuildService.pytest + 打包                  # 宿主机直接跑
                 → nebula-runtime (docker-py 起容器预览)
```

问题：
- 编码和构建都在宿主机，`pip install` 会污染环境
- 测试结果依赖宿主机已安装的包，不可复现
- 无法限制资源（CPU/内存）
- 没有可扩展的抽象接口，未来 A2A 网关无法接入

## 决策：完整 Docker 容器化方案

### 做

| 组件 | 说明 |
|------|------|
| ① `CoderBackend` 抽象接口 | ABC，定义 `execute_development(spec, skill, project_dir) -> DevelopmentResult` |
| ② `DockerCoderBackend` | v1 实现：编码容器 + 构建容器双容器模式 |
| ③ 编码容器（大镜像） | 含 Python、Node.js、Claude Code SDK、开发工具链。挂载宿主机 Claude Code 授权 |
| ④ 构建容器（小镜像） | alpine + Python，pip install → pytest → 打包 tar.gz |
| ⑤ 重构 `ExecutorService` | 从 subprocess 硬编码 → 接入 CoderBackend 接口 |
| ⑥ 重构 `BuildService` | 构建阶段在构建容器内执行（接口可作为 CoderBackend 的一部分或单独抽象） |
| ⑦ 项目代码传递 | 通过挂载卷在宿主机、编码容器、构建容器之间传递源码和产物 |

### 不做（第一版）

- 多容器并行编排（每次只跑一个编码任务）
- Kubernetes 部署容器化编码执行
- A2A CoderBackend 实现（留 Phase 4 协议网关）
- 容器异地/分布式执行
- 编码容器的 UI 终端流式日志
- 容器镜像的 CI/CD 自动构建与推送

### `CoderBackend` 接口设计方向

```python
class CoderBackend(ABC):
    """编码执行后端抽象。v1 Docker, v2 A2A, ..."""

    @abstractmethod
    async def execute_development(
        self,
        spec: dict,
        skill: Skill,
        project_dir: str,
    ) -> DevelopmentResult:
        ...
```

平行实现：
| 后端 | 场景 |
|------|------|
| `DockerCoderBackend` | 本地/单机开发环境 |
| `A2ACoderBackend` | 远程集群，多 Agent 协作（Phase 4） |

## 依赖关系

```
Phase 2 docker-executor
  → 无前置依赖（但 Docker daemon 必须在宿主机可用）
  → 被 Phase 3 Skill 体系依赖（容器化后才能稳定执行 Skill 编码指令）
  → CoderBackend 抽象接口被 Phase 4 A2A Gateway 依赖
```

## 后续步骤

1. → openspec SDD 文档生成（proposal → specs → design → tasks）
2. openspec sync --change docker-executor
3. spec-hardener 审查
4. writing-plans 生成实现计划
5. 用户确认后进入 TDD 实现
