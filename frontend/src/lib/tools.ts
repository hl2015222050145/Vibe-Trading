/**
 * Single source of truth for tool name -> user-facing label.
 */
export const TOOL_LABELS: Record<string, string> = {
  load_skill: "加载策略知识",
  write_file: "生成代码",
  edit_file: "编辑代码",
  read_file: "读取文件",
  run_backtest: "运行回测",
  bash: "执行命令",
  read_url: "读取网页",
  read_document: "读取文档",
  compact: "压缩上下文",
  create_task: "创建任务",
  update_task: "更新任务",
  spawn_subagent: "启动子智能体",
};

export function localizeToolName(tool: string, fallback?: string): string {
  if (tool in TOOL_LABELS) {
    return TOOL_LABELS[tool];
  }
  if (fallback !== undefined) {
    return fallback;
  }
  return tool;
}
