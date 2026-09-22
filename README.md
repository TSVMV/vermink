# j

零依赖终端美化引擎：把纯文本主题编译成 Zsh / Bash / PowerShell 的提示符与状态栏。

## 安装

```bash
pip install j
```

## 快速开始

```bash
# 生成默认 dark 主题并安装到当前 shell
j init

# 预览主题效果（不修改任何文件）
j preview dark

# 列出所有主题
j list
```

## 子命令

| 命令 | 说明 |
| --- | --- |
| `j init [--shell zsh\|bash\|pwsh]` | 生成默认 dark 主题并安装 |
| `j preview <主题名> [--plain]` | 终端预览渲染效果 |
| `j install <主题名> --shell zsh\|bash\|pwsh` | 安装到 shell 启动文件（自动备份） |
| `j uninstall --shell zsh\|bash\|pwsh` | 卸载并还原备份 |
| `j list [--shell zsh\|bash\|pwsh]` | 列出主题与当前生效主题 |
| `j show <主题名>` | 打印主题源配置 |

## 主题文件

主题文件使用 INI 格式，包含以下区块：

```ini
## j theme mytheme

[palette]
user = bright_green
host = bright_cyan
dir = bright_blue
git = bright_magenta
git_state = yellow
venv = bright_green
time = grey
exit_code = red

[prompt]
user
host
dir
git
git_state

[status]
venv
time
exit_code

[format]
user = user
host = host
dir = dir
git = git
git_state = git_state
venv = venv
time = time
exit_code = exit_code
```

### 区块说明

- **[palette]**：定义颜色名称，支持命名色（如 `red`、`bright_green`）、256 色（如 `208`）、HEX 色（如 `#ff8800`）、修饰符（如 `bold`、`dim`）
- **[prompt]**：左侧提示符显示的片段列表
- **[status]**：状态栏显示的片段列表（Zsh 为 RPROMPT，Bash/Pwsh 合并到主提示符）
- **[format]**：将片段映射到配色名，设为 `none` 表示不着色

### 可用片段

| 片段 | 说明 |
| --- | --- |
| `user` | 当前用户名 |
| `host` | 主机名 |
| `dir` | 当前目录（~ 缩写） |
| `git` | Git 分支名 |
| `git_state` | Git 状态（`*` 有修改，`+` 有未跟踪文件） |
| `venv` | 虚拟环境名 |
| `time` | 当前时间（HH:MM） |
| `exit_code` | 上一条命令的退出码（非零时显示） |

### 内置主题

- **dark**：深色终端主题（默认）
- **light**：浅色终端主题

## 自定义主题

```bash
# 保存主题到配置目录
j init --theme dark --name mytheme --no-install

# 编辑主题
vim ~/.config/j/themes/mytheme.conf

# 安装自定义主题
j install mytheme --shell zsh
```

## Shell 支持

| Shell | 提示符 | 状态栏 |
| --- | --- | --- |
| Zsh | PS1 | RPROMPT（右侧） |
| Bash | PS1（PROMPT_COMMAND） | 合并到主提示符 |
| PowerShell | prompt 函数 | 合并到主提示符 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[test]"

# 运行测试
pytest tests/

# 代码检查
ruff check .
```

## 许可证

MIT
