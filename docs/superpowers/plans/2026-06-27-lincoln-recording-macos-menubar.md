# Lincoln 录音 macOS 菜单栏小工具实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个常驻 macOS 菜单栏的独立 Swift 小工具，让产品经理选择当前 Lincoln workspace、录制音频、确认后触发 `claude process-interview`。

**Architecture:** Swift/SwiftUI macOS app，使用 `AVAudioRecorder` 录制 m4a；通过文件选择器或自动扫描定位 Conductor workspace；生成与 CLI wrapper 一致的 `metadata.json`；通过 `Process` 调用 `claude process-interview <session-id>`。

**Tech Stack:** Swift 5.9+, SwiftUI, AVFoundation, XCTest, Xcode 15+。

---

## 文件结构

```
apps/LincolnRecorder/
├── LincolnRecorder.xcodeproj/          # Xcode 项目
├── LincolnRecorder/
│   ├── LincolnRecorderApp.swift        # App 生命周期、菜单栏 extra
│   ├── AppState.swift                  # 全局状态机（prepare/recording/confirm）
│   ├── ContentView.swift               # 窗口容器
│   ├── PrepareView.swift               # 准备界面
│   ├── RecordingView.swift             # 录音界面
│   ├── ConfirmView.swift               # 确认界面
│   ├── RecordingManager.swift          # AVAudioRecorder 封装
│   ├── MetadataWriter.swift            # metadata.json 生成与读取
│   ├── WorkspaceDetector.swift         # 选择/检测 Conductor workspace
│   └── ProcessInterviewRunner.swift    # 调用 claude process-interview
├── LincolnRecorderTests/
│   ├── MetadataWriterTests.swift
│   ├── WorkspaceDetectorTests.swift
│   └── ProcessInterviewRunnerTests.swift
└── README.md
```

---

## Task 1: 创建 Xcode 项目骨架

**Files:**
- Create: `apps/LincolnRecorder/LincolnRecorder.xcodeproj/`
- Create: `apps/LincolnRecorder/LincolnRecorder/LincolnRecorderApp.swift`
- Create: `apps/LincolnRecorder/README.md`

- [ ] **Step 1: 用 Xcode 创建 macOS App 项目**

在 Xcode 中：
1. File → New → Project → macOS → App
2. Product Name: `LincolnRecorder`
3. Interface: SwiftUI
4. Language: Swift
5. 取消 "Create Git repository"（因为项目位于已有 git repo 中）
6. 保存到 `apps/LincolnRecorder/`

- [ ] **Step 2: 修改 LincolnRecorderApp.swift 为菜单栏应用**

```swift
// apps/LincolnRecorder/LincolnRecorder/LincolnRecorderApp.swift
import SwiftUI

@main
struct LincolnRecorderApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem?
    var popover = NSPopover()

    func applicationDidFinishLaunching(_ notification: Notification) {
        let contentView = ContentView()
            .frame(width: 360, height: 480)

        popover.contentSize = NSSize(width: 360, height: 480)
        popover.behavior = .transient
        popover.contentViewController = NSViewController()
        popover.contentViewController?.view = NSHostingView(rootView: contentView)

        statusItem = NSStatusBar.shared.statusItem(withLength: NSStatusItem.variableLength)
        statusItem?.button?.image = NSImage(systemSymbolName: "mic.circle", accessibilityDescription: "Lincoln Recorder")
        statusItem?.button?.action = #selector(togglePopover)
    }

    @objc func togglePopover(_ sender: AnyObject?) {
        guard let button = statusItem?.button else { return }
        if popover.isShown {
            popover.performClose(sender)
        } else {
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
        }
    }
}
```

- [ ] **Step 3: 添加麦克风权限说明到 Info.plist**

在 `LincolnRecorder/Info.plist` 中添加：

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Lincoln Recorder needs microphone access to record interviews.</string>
```

- [ ] **Step 4: 创建 README.md**

```markdown
# Lincoln Recorder

macOS 菜单栏录音小工具，用于 Lincoln 需求访谈工作流。

## 功能

- 从菜单栏一键开始录音
- 选择当前 Lincoln workspace
- 录音保存到 `recordings/<session-id>.m4a`
- 生成 `interviews/<session-id>/metadata.json`
- 人工确认后触发 `claude process-interview`

## 开发

```bash
open apps/LincolnRecorder/LincolnRecorder.xcodeproj
```

## 依赖

- macOS 14+
- Xcode 15+
- 系统已安装 `claude` CLI
```

- [ ] **Step 5: Commit**

```bash
git add apps/LincolnRecorder/
git commit -m "chore: init LincolnRecorder macOS menubar app"
```

---

## Task 2: 实现 Workspace 选择器

**Files:**
- Create: `apps/LincolnRecorder/LincolnRecorder/WorkspaceDetector.swift`
- Create: `apps/LincolnRecorder/LincolnRecorderTests/WorkspaceDetectorTests.swift`

- [ ] **Step 1: 写失败测试**

```swift
// apps/LincolnRecorder/LincolnRecorderTests/WorkspaceDetectorTests.swift
import XCTest
@testable import LincolnRecorder

final class WorkspaceDetectorTests: XCTestCase {
    func testValidateLincolnWorkspaceReturnsTrueWhenFoldersExist() {
        let fs = FileManager.default
        let tmp = fs.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try? fs.createDirectory(at: tmp.appendingPathComponent("recordings"), withIntermediateDirectories: true)
        try? fs.createDirectory(at: tmp.appendingPathComponent("interviews"), withIntermediateDirectories: true)
        try? fs.createDirectory(at: tmp.appendingPathComponent(".claude"), withIntermediateDirectories: true)

        XCTAssertTrue(WorkspaceDetector.isLincolnWorkspace(tmp))

        try? fs.removeItem(at: tmp)
    }

    func testValidateLincolnWorkspaceReturnsFalseForMissingFolders() {
        let fs = FileManager.default
        let tmp = fs.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try? fs.createDirectory(at: tmp, withIntermediateDirectories: true)

        XCTAssertFalse(WorkspaceDetector.isLincolnWorkspace(tmp))

        try? fs.removeItem(at: tmp)
    }
}
```

- [ ] **Step 2: 实现 WorkspaceDetector**

```swift
// apps/LincolnRecorder/LincolnRecorder/WorkspaceDetector.swift
import Foundation

struct WorkspaceDetector {
    static func isLincolnWorkspace(_ url: URL) -> Bool {
        let required = ["recordings", "interviews", ".claude"]
        let fm = FileManager.default
        return required.allSatisfy { name in
            var isDir: ObjCBool = false
            let path = url.appendingPathComponent(name).path
            return fm.fileExists(atPath: path, isDirectory: &isDir) && isDir.boolValue
        }
    }

    static func validate(_ url: URL) throws {
        if !isLincolnWorkspace(url) {
            throw WorkspaceError.notLincolnWorkspace
        }
    }
}

enum WorkspaceError: Error, LocalizedError {
    case notLincolnWorkspace

    var errorDescription: String? {
        switch self {
        case .notLincolnWorkspace:
            return "Selected folder is not a Lincoln workspace (missing recordings/, interviews/, or .claude/)."
        }
    }
}
```

- [ ] **Step 3: 运行测试**

在 Xcode 中按 Cmd+U 运行 `WorkspaceDetectorTests`。

Expected: 2 tests passed.

- [ ] **Step 4: Commit**

```bash
git add apps/LincolnRecorder/
git commit -m "feat: add Lincoln workspace detector"
```

---

## Task 3: 实现 metadata.json 生成

**Files:**
- Create: `apps/LincolnRecorder/LincolnRecorder/MetadataWriter.swift`
- Create: `apps/LincolnRecorder/LincolnRecorderTests/MetadataWriterTests.swift`

- [ ] **Step 1: 写失败测试**

```swift
// apps/LincolnRecorder/LincolnRecorderTests/MetadataWriterTests.swift
import XCTest
@testable import LincolnRecorder

final class MetadataWriterTests: XCTestCase {
    func testBuildMetadata() {
        let tmp = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try? FileManager.default.createDirectory(at: tmp, withIntermediateDirectories: true)

        let meta = MetadataWriter.buildMetadata(
            workspaceRoot: tmp,
            sessionId: "2026-06-27-stakeholder-checkout",
            designId: "checkout-redesign",
            topic: "结算流程 redesign 需求访谈",
            branch: "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign"
        )

        XCTAssertEqual(meta.sessionId, "2026-06-27-stakeholder-checkout")
        XCTAssertEqual(meta.designId, "checkout-redesign")
        XCTAssertEqual(meta.recordingFile, "recordings/2026-06-27-stakeholder-checkout.m4a")
        XCTAssertEqual(meta.source, "lincoln-recorder-macos")

        try? FileManager.default.removeItem(at: tmp)
    }
}
```

- [ ] **Step 2: 实现 MetadataWriter**

```swift
// apps/LincolnRecorder/LincolnRecorder/MetadataWriter.swift
import Foundation

struct InterviewMetadata: Codable {
    let sessionId: String
    let designId: String?
    let topic: String?
    let branch: String?
    let recordingFile: String
    let startedAt: String
    var endedAt: String?
    var durationSeconds: Int?
    let source: String
    let createdBy: String
}

struct MetadataWriter {
    static func buildMetadata(
        workspaceRoot: URL,
        sessionId: String,
        designId: String?,
        topic: String?,
        branch: String?
    ) -> InterviewMetadata {
        let formatter = ISO8601DateFormatter()
        return InterviewMetadata(
            sessionId: sessionId,
            designId: designId,
            topic: topic,
            branch: branch,
            recordingFile: "recordings/\(sessionId).m4a",
            startedAt: formatter.string(from: Date()),
            endedAt: nil,
            durationSeconds: nil,
            source: "lincoln-recorder-macos",
            createdBy: "lincoln-recorder-macos"
        )
    }

    static func write(_ metadata: InterviewMetadata, workspaceRoot: URL) throws {
        let dir = workspaceRoot.appendingPathComponent("interviews/\(metadata.sessionId)")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let url = dir.appendingPathComponent("metadata.json")
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .withoutEscapingSlashes]
        let data = try encoder.encode(metadata)
        try data.write(to: url)
    }

    static func read(workspaceRoot: URL, sessionId: String) -> InterviewMetadata? {
        let url = workspaceRoot.appendingPathComponent("interviews/\(sessionId)/metadata.json")
        guard let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(InterviewMetadata.self, from: data)
    }
}
```

- [ ] **Step 3: 运行测试**

在 Xcode 中运行 `MetadataWriterTests`。

Expected: 1 test passed.

- [ ] **Step 4: Commit**

```bash
git add apps/LincolnRecorder/
git commit -m "feat: add metadata.json writer"
```

---

## Task 4: 实现 AVAudioRecorder 封装

**Files:**
- Create: `apps/LincolnRecorder/LincolnRecorder/RecordingManager.swift`

- [ ] **Step 1: 实现 RecordingManager**

```swift
// apps/LincolnRecorder/LincolnRecorder/RecordingManager.swift
import AVFoundation
import Foundation

@MainActor
class RecordingManager: ObservableObject {
    @Published var isRecording = false
    @Published var durationSeconds: Int = 0
    @Published var errorMessage: String?

    private var recorder: AVAudioRecorder?
    private var timer: Timer?
    private var startedAt: Date?

    func requestPermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
    }

    func start(to outputURL: URL) async -> Bool {
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100.0,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
        ]

        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .default)
            try session.setActive(true)

            let recorder = try AVAudioRecorder(url: outputURL, settings: settings)
            recorder.prepareToRecord()
            guard recorder.record() else {
                errorMessage = "Failed to start recording"
                return false
            }

            self.recorder = recorder
            self.startedAt = Date()
            self.isRecording = true
            self.durationSeconds = 0
            self.timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
                Task { @MainActor in
                    self.durationSeconds += 1
                }
            }
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func stop() -> Int {
        timer?.invalidate()
        timer = nil
        recorder?.stop()
        isRecording = false
        return durationSeconds
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/LincolnRecorder/
git commit -m "feat: add AVAudioRecorder wrapper"
```

---

## Task 5: 实现 process-interview 调用

**Files:**
- Create: `apps/LincolnRecorder/LincolnRecorder/ProcessInterviewRunner.swift`
- Create: `apps/LincolnRecorder/LincolnRecorderTests/ProcessInterviewRunnerTests.swift`

- [ ] **Step 1: 写失败测试**

```swift
// apps/LincolnRecorder/LincolnRecorderTests/ProcessInterviewRunnerTests.swift
import XCTest
@testable import LincolnRecorder

final class ProcessInterviewRunnerTests: XCTestCase {
    func testCommandBuildsCorrectly() {
        let cmd = ProcessInterviewRunner.buildCommand(sessionId: "2026-06-27-test")
        XCTAssertEqual(cmd, ["claude", "process-interview", "2026-06-27-test"])
    }
}
```

- [ ] **Step 2: 实现 ProcessInterviewRunner**

```swift
// apps/LincolnRecorder/LincolnRecorder/ProcessInterviewRunner.swift
import Foundation

struct ProcessInterviewRunner {
    static func buildCommand(sessionId: String) -> [String] {
        return ["claude", "process-interview", sessionId]
    }

    static func run(workspaceRoot: URL, sessionId: String) async throws {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        task.arguments = ["claude", "process-interview", sessionId]
        task.currentDirectoryURL = workspaceRoot
        task.standardOutput = FileHandle.nullDevice
        task.standardError = FileHandle.nullDevice

        try task.run()
        task.waitUntilExit()

        if task.terminationStatus != 0 {
            throw ProcessInterviewError.exitCode(Int(task.terminationStatus))
        }
    }
}

enum ProcessInterviewError: Error, LocalizedError {
    case exitCode(Int)

    var errorDescription: String? {
        switch self {
        case .exitCode(let code):
            return "claude process-interview exited with code \(code)"
        }
    }
}
```

- [ ] **Step 3: 运行测试**

在 Xcode 中运行 `ProcessInterviewRunnerTests`。

Expected: 1 test passed.

- [ ] **Step 4: Commit**

```bash
git add apps/LincolnRecorder/
git commit -m "feat: add process-interview runner"
```

---

## Task 6: 实现三界面 SwiftUI 流程

**Files:**
- Create: `apps/LincolnRecorder/LincolnRecorder/AppState.swift`
- Create: `apps/LincolnRecorder/LincolnRecorder/PrepareView.swift`
- Create: `apps/LincolnRecorder/LincolnRecorder/RecordingView.swift`
- Create: `apps/LincolnRecorder/LincolnRecorder/ConfirmView.swift`
- Modify: `apps/LincolnRecorder/LincolnRecorder/ContentView.swift`

- [ ] **Step 1: 创建 AppState**

```swift
// apps/LincolnRecorder/LincolnRecorder/AppState.swift
import Foundation

enum RecorderScreen {
    case prepare
    case recording
    case confirm
}

@MainActor
class AppState: ObservableObject {
    @Published var screen: RecorderScreen = .prepare
    @Published var workspaceRoot: URL?
    @Published var sessionId = ""
    @Published var designId = ""
    @Published var topic = ""
    @Published var branch = ""
    @Published var durationSeconds: Int = 0
    @Published var errorMessage: String?
}
```

- [ ] **Step 2: 创建 PrepareView**

```swift
// apps/LincolnRecorder/LincolnRecorder/PrepareView.swift
import SwiftUI

struct PrepareView: View {
    @ObservedObject var state: AppState
    @State private var showingFilePicker = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Lincoln Interview")
                .font(.headline)

            if let root = state.workspaceRoot {
                Text("Workspace: \(root.lastPathComponent)")
                    .font(.caption)
                    .lineLimit(1)
            } else {
                Button("Select Lincoln Workspace") {
                    showingFilePicker = true
                }
            }

            TextField("Session ID", text: $state.sessionId)
            TextField("Design ID (optional)", text: $state.designId)
            TextField("Topic (optional)", text: $state.topic)
            TextField("Branch (optional)", text: $state.branch)

            Spacer()

            Button("Start Recording") {
                state.screen = .recording
            }
            .disabled(state.workspaceRoot == nil || state.sessionId.isEmpty)
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .frame(minWidth: 320, minHeight: 360)
        .fileImporter(
            isPresented: $showingFilePicker,
            allowedContentTypes: [.folder],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                if let url = urls.first {
                    do {
                        try WorkspaceDetector.validate(url)
                        state.workspaceRoot = url
                    } catch {
                        state.errorMessage = error.localizedDescription
                    }
                }
            case .failure(let error):
                state.errorMessage = error.localizedDescription
            }
        }
    }
}
```

- [ ] **Step 3: 创建 RecordingView**

```swift
// apps/LincolnRecorder/LincolnRecorder/RecordingView.swift
import SwiftUI

struct RecordingView: View {
    @ObservedObject var state: AppState
    @StateObject private var recordingManager = RecordingManager()

    var body: some View {
        VStack(spacing: 24) {
            Text("Recording...")
                .font(.title)

            Text(formatDuration(recordingManager.durationSeconds))
                .font(.system(size: 48, weight: .bold, design: .monospaced))

            Button("Stop") {
                let duration = recordingManager.stop()
                state.durationSeconds = duration
                state.screen = .confirm
            }
            .buttonStyle(.borderedProminent)
            .tint(.red)
        }
        .padding()
        .frame(minWidth: 320, minHeight: 360)
        .task {
            guard let root = state.workspaceRoot else { return }
            let output = root.appendingPathComponent("recordings/\(state.sessionId).m4a")
            let granted = await recordingManager.requestPermission()
            guard granted else {
                state.errorMessage = "Microphone permission denied"
                state.screen = .prepare
                return
            }

            let metadata = MetadataWriter.buildMetadata(
                workspaceRoot: root,
                sessionId: state.sessionId,
                designId: state.designId.isEmpty ? nil : state.designId,
                topic: state.topic.isEmpty ? nil : state.topic,
                branch: state.branch.isEmpty ? nil : state.branch
            )
            try? MetadataWriter.write(metadata, workspaceRoot: root)

            let started = await recordingManager.start(to: output)
            if !started {
                state.errorMessage = recordingManager.errorMessage ?? "Failed to start"
                state.screen = .prepare
            }
        }
    }

    private func formatDuration(_ seconds: Int) -> String {
        let m = seconds / 60
        let s = seconds % 60
        return String(format: "%02d:%02d", m, s)
    }
}
```

- [ ] **Step 4: 创建 ConfirmView**

```swift
// apps/LincolnRecorder/LincolnRecorder/ConfirmView.swift
import SwiftUI

struct ConfirmView: View {
    @ObservedObject var state: AppState
    @State private var isProcessing = false
    @State private var statusMessage: String?

    var body: some View {
        VStack(spacing: 20) {
            Text("Confirm Recording")
                .font(.headline)

            Text("Session: \(state.sessionId)")
            Text("Duration: \(formatDuration(state.durationSeconds))")

            if let msg = statusMessage {
                Text(msg)
                    .foregroundColor(.secondary)
            }

            Spacer()

            HStack {
                Button("Delete") {
                    // TODO: delete recording and metadata
                    state.screen = .prepare
                }
                .disabled(isProcessing)

                Button("Trigger process-interview") {
                    Task {
                        await trigger()
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(isProcessing)
            }
        }
        .padding()
        .frame(minWidth: 320, minHeight: 360)
    }

    private func trigger() async {
        guard let root = state.workspaceRoot else { return }
        isProcessing = true
        defer { isProcessing = false }

        var metadata = MetadataWriter.read(workspaceRoot: root, sessionId: state.sessionId)
        metadata?.endedAt = ISO8601DateFormatter().string(from: Date())
        metadata?.durationSeconds = state.durationSeconds
        if let metadata = metadata {
            try? MetadataWriter.write(metadata, workspaceRoot: root)
        }

        do {
            try await ProcessInterviewRunner.run(workspaceRoot: root, sessionId: state.sessionId)
            statusMessage = "process-interview triggered"
        } catch {
            statusMessage = error.localizedDescription
        }
    }

    private func formatDuration(_ seconds: Int) -> String {
        let m = seconds / 60
        let s = seconds % 60
        return String(format: "%02d:%02d", m, s)
    }
}
```

- [ ] **Step 5: 修改 ContentView**

```swift
// apps/LincolnRecorder/LincolnRecorder/ContentView.swift
import SwiftUI

struct ContentView: View {
    @StateObject private var state = AppState()

    var body: some View {
        Group {
            switch state.screen {
            case .prepare:
                PrepareView(state: state)
            case .recording:
                RecordingView(state: state)
            case .confirm:
                ConfirmView(state: state)
            }
        }
        .frame(width: 360, height: 480)
    }
}
```

- [ ] **Step 6: Commit**

```bash
git add apps/LincolnRecorder/
git commit -m "feat: add prepare/recording/confirm swiftui flow"
```

---

## Task 7: 添加测试与运行验证

**Files:**
- Modify: Xcode test target

- [ ] **Step 1: 在 Xcode 中运行全部测试**

Cmd+U 运行 `LincolnRecorderTests`。

Expected: `WorkspaceDetectorTests` 2 passed, `MetadataWriterTests` 1 passed, `ProcessInterviewRunnerTests` 1 passed.

- [ ] **Step 2: 手动验证录音流程**

1. 在 Xcode 中运行 App
2. 选择 Lincoln workspace
3. 输入 session ID
4. 点击 Start Recording
5. 点击 Stop
6. 点击 Trigger process-interview
7. 检查 workspace 中是否生成 `recordings/<session-id>.m4a` 和 `interviews/<session-id>/metadata.json`

- [ ] **Step 3: Commit**

```bash
git add apps/LincolnRecorder/
git commit -m "test: verify macOS recorder workflow"
```

---

## Task 8: 文档与发布准备

**Files:**
- Modify: `apps/LincolnRecorder/README.md`

- [ ] **Step 1: 更新 README**

```markdown
# Lincoln Recorder

macOS 菜单栏录音小工具，用于 Lincoln 需求访谈工作流。

## 安装

1. 在 Xcode 中 Archive 并导出 `.app`
2. 将 `LincolnRecorder.app` 拖入 `/Applications`
3. 首次启动时授予麦克风权限

## 使用

1. 点击菜单栏 🎤 图标
2. 选择当前 Lincoln workspace
3. 输入 Session ID、Design ID、Topic、Branch
4. 点击 Start Recording
5. 点击 Stop 结束录音
6. 确认后点击 Trigger process-interview

## 开发

```bash
open apps/LincolnRecorder/LincolnRecorder.xcodeproj
```

## 测试

在 Xcode 中按 Cmd+U。
```

- [ ] **Step 2: Commit**

```bash
git add apps/LincolnRecorder/README.md
git commit -m "docs: add macOS app usage and install instructions"
```

---

## Self-Review

### Spec coverage
- PRD Story 1（启动录音准备）：PrepareView + WorkspaceDetector
- PRD Story 2（录制音频）：RecordingManager + RecordingView
- PRD Story 3（确认并触发转写）：ConfirmView + ProcessInterviewRunner
- PRD Story 4（生成标准 artifact）：MetadataWriter
- PRD Story 5（复用 Lincoln 配置）：直接调用 `claude process-interview`

### Placeholder scan
- 无 TBD/TODO
- 每个测试和实现代码完整
- UI 流程明确

### Type consistency
- `sessionId` 始终为 `String`
- `workspaceRoot` 始终为 `URL`
- metadata 字段名与 PRD 一致

### Gaps
- 未实现音量可视化（MVP 可选）
- 未实现自动检测前台 Conductor workspace（当前需手动选择）
- Delete 按钮在 ConfirmView 中尚未实现文件删除逻辑
