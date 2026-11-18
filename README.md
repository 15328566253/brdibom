# brd2ibom

将 Cadence Allegro `.brd` 文件转换为 InteractiveHtmlBom 焊接辅助 HTML。

工具使用本机 Cadence Allegro 的无图形批处理能力读取 BRD，再调用 `exportJson.il` 导出 iBOM JSON，最后调用 InteractiveHtmlBom 生成单文件 HTML。

## 依赖

- Windows
- Cadence Allegro 24.1 或兼容的 Allegro PCB Editor 安装
- Python 3.10 或更高版本
- `jsonschema`

安装 Python 依赖：

```powershell
python -m pip install -r requirements.txt
```

当前仓库已经包含两个上游依赖的源码和许可证文件：

- `vendor/exportJson`
- `vendor/InteractiveHtmlBom`

## 命令行

直接从 BRD 生成 HTML：

```powershell
python -m brd2ibom path\to\board.brd
```

如果源码目录尚未加入 Python 模块路径，可以使用：

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m brd2ibom path\to\board.brd
```

指定 Cadence 安装目录：

```powershell
python -m brd2ibom path\to\board.brd --cadence-root C:\Cadence\SPB_24.1
```

指定 `allegro.exe`：

```powershell
python -m brd2ibom path\to\board.brd --cadence-exe D:\Cadence\SPB_24.1\tools\bin\allegro.exe
```

指定输出目录并保留日志：

```powershell
python -m brd2ibom path\to\board.brd `
  --output-dir path\to\ibom `
  --keep-workspace `
  --no-browser
```

不经过 Allegro，直接测试 HTML 生成器：

```powershell
python -m brd2ibom --json vendor\exportJson\example\AD-FMComms3_revA.json --no-browser
```

不带参数运行会打开文件选择窗口：

```powershell
python -m brd2ibom
```

首次使用 GUI 时点击 `Cadence 设置`，可以使用“自动扫描”查找各磁盘下的 Cadence 安装，也可以选择安装根目录或直接选择 `allegro.exe`。设置会保存到当前用户的 `%APPDATA%\brd2ibom\config.json`。

## 构建便携 EXE

安装打包依赖并执行：

```powershell
python -m pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1 -Clean
```

输出文件位于：

```text
dist\brdibom.exe
```

这是一个单文件便携 EXE。Cadence Allegro 本身仍然需要安装在本机。

GUI 版本不会显示黑色命令窗口。Allegro 的实时输出会显示在窗口下方的“运行日志”区域，并同步保存到临时工作目录中的 `allegro.log`。

## 处理流程

1. EXE 查找 Cadence Allegro 安装。
2. 创建临时工作目录并复制输入 BRD。
3. 生成 Allegro `.scr` 批处理脚本。
4. 启动 `allegro.exe -s ... -nograph`。
5. 在 Allegro 中加载 `jsonDecode.il` 和 `exportJson.il`。
6. 将设计导出为 JSON。
7. 调用 InteractiveHtmlBom 生成 HTML。
8. 删除临时目录或按 `--keep-workspace` 保留日志。

Allegro 24.1 的主程序通常位于 `tools\bin\allegro.exe`。程序会以 PCB 模式启动它，并自动设置 `CDSROOT` 和 Cadence 工具目录。

当前版本读取磁盘中的已保存 BRD。Allegro 中尚未保存的修改不会包含在独立 EXE 的导出结果中。


## 项目目录

- `src/brd2ibom`：主程序和 GUI
- `skill`：Allegro SKILL bridge
- `config`：iBOM 导出配置
- `vendor/exportJson`：Allegro JSON 导出组件
- `vendor/InteractiveHtmlBom`：HTML BOM 生成组件
- `assets`：应用图标
- `tests`：基础测试
- `dist/brdibom.exe`：最新 Windows 单文件程序

第三方组件的许可证说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
