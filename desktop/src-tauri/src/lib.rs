//! Tauri backend for the packaging spike.
//!
//! On launch: opens a durable log file, spawns the sigma-engine sidecar, and
//! stores its handle in managed state. On window close: kills it. The
//! frontend (src/App.tsx) never talks to Rust via IPC for the lifecycle -- it
//! polls the sidecar's own HTTP API directly at 127.0.0.1 -- but it CAN ask
//! Rust for the sidecar log path/tail (the two commands below) so a failed
//! launch is self-diagnosing instead of a silent "Failed to fetch".
//!
//! Everything the sidecar writes to stdout/stderr, plus its spawn and exit,
//! is mirrored to `sidecar.log` in the app log dir. In an installed app the
//! old `print!`-only draining vanished into a detached process with no
//! console; the log file is the durable record we and the user can read.

use std::fs::File;
use std::io::Write;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use tauri::webview::DownloadEvent;
use tauri::{Manager, WebviewWindowBuilder};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

// Must match sigma_engine.main.DEFAULT_PORT (engine/sigma_engine/main.py) and
// the Tauri-sidecar base URL in desktop/src/api/runtime.ts. Nothing shares
// this constant across the Rust/Python/TS boundary in this spike, so it's
// duplicated by hand in three places -- worth centralizing if the spike grows
// into the real app.
const SIDECAR_PORT: &str = "8756";

/// Holds the running sidecar's process handle so it can be killed later.
/// `Option` because it's taken (not just read) on shutdown -- `CommandChild::kill`
/// consumes `self`, so ownership has to move out of the Mutex to call it.
struct SidecarProcess(Mutex<Option<CommandChild>>);

/// The resolved on-disk path of `sidecar.log`, managed so the two log
/// commands below can find the file no matter which fallback dir won.
struct SidecarLogPath(PathBuf);

/// Write `text` to the sidecar log (best-effort) and to this process's own
/// stdout (visible under `npm run tauri dev`). `text` is expected to already
/// carry its own newline; callers pass the full `[sigma-engine] ...` line so
/// the file and the console read identically. A `None` file (couldn't open)
/// or a poisoned lock just skips the file half -- logging never takes the app
/// down.
fn append_log(log: &Arc<Mutex<Option<File>>>, text: &str) {
    print!("{}", text);
    if let Ok(mut guard) = log.lock() {
        if let Some(file) = guard.as_mut() {
            let _ = file.write_all(text.as_bytes());
            let _ = file.flush();
        }
    }
}

/// Absolute path of the sidecar log file, for the frontend to show the user
/// where to look when the engine doesn't come up.
#[tauri::command]
fn sidecar_log_path(state: tauri::State<'_, SidecarLogPath>) -> String {
    state.0.to_string_lossy().to_string()
}

/// The last ~4000 characters of the sidecar log, for the frontend to show the
/// failure reason inline. Best-effort: any error (missing file, read error)
/// returns an empty string rather than throwing across the IPC boundary.
#[tauri::command]
fn sidecar_log_tail(state: tauri::State<'_, SidecarLogPath>) -> String {
    match std::fs::read(&state.0) {
        Ok(bytes) => {
            let text = String::from_utf8_lossy(&bytes);
            let count = text.chars().count();
            if count <= 4000 {
                text.into_owned()
            } else {
                text.chars().skip(count - 4000).collect()
            }
        }
        Err(_) => String::new(),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![sidecar_log_path, sidecar_log_tail])
        .setup(|app| {
            // Resolve a durable log location, preferring the app log dir, then
            // the app data dir, then the OS temp dir. All three return a
            // PathBuf in Tauri v2; whichever resolves first is fine -- the
            // point is that a packaged app records its sidecar's output
            // somewhere readable after the fact.
            let log_dir = app
                .path()
                .app_log_dir()
                .or_else(|_| app.path().app_data_dir())
                .unwrap_or_else(|_| std::env::temp_dir());
            let _ = std::fs::create_dir_all(&log_dir);
            let log_path = log_dir.join("sidecar.log");

            // create() truncates: each launch starts a fresh log. Wrapped in an
            // Arc<Mutex<Option<File>>> so the async drain task can share the
            // same handle; `None` if the file couldn't be opened, in which case
            // append_log just skips the file half and keeps printing.
            let log: Arc<Mutex<Option<File>>> = Arc::new(Mutex::new(File::create(&log_path).ok()));

            // Managed before any early return below, so sidecar_log_path /
            // sidecar_log_tail always resolve even when the sidecar fails to
            // start (that failure is exactly when the frontend asks for them).
            app.manage(SidecarLogPath(log_path.clone()));

            // Create the main window ourselves (tauri.conf.json marks it
            // "create": false) for exactly one reason: to attach a download
            // handler.
            //
            // The charter's "Export PDF" button fetches the PDF as a blob
            // and clicks an <a download> (desktop/src/tools/charter/
            // CharterForm.tsx). On macOS that becomes a WKWebView navigation
            // with shouldPerformDownload = true, and wry's navigation
            // delegate answers WKNavigationActionPolicy::Cancel whenever no
            // download handler is registered (wry-0.55.1
            // src/wkwebview/navigation.rs) -- so the download is silently
            // dropped: no file, no error, no feedback. Tauri only registers
            // that handler when the window is built with .on_download(),
            // which a config-created window never is. Windows/WebView2 fell
            // back to its own default download UI, which is why this looked
            // fine on one platform and was dead on the other, and why no
            // browser-based test could see it (Chromium downloads happily).
            //
            // Returning true = allow, saving to the platform's default
            // download directory. Both events are mirrored into the sidecar
            // log so an export that goes wrong is diagnosable after the fact
            // like everything else here.
            let log_for_download = Arc::clone(&log);
            let window_config = app
                .config()
                .app
                .windows
                .first()
                .cloned()
                .expect("tauri.conf.json must define the main window");
            WebviewWindowBuilder::from_config(app.handle(), &window_config)?
                .on_download(move |_webview, event| {
                    match event {
                        DownloadEvent::Requested { url, destination } => append_log(
                            &log_for_download,
                            &format!("[sigma-engine] download requested {} -> {}\n", url, destination.display()),
                        ),
                        DownloadEvent::Finished { url, path, success } => append_log(
                            &log_for_download,
                            &format!(
                                "[sigma-engine] download finished success={} {} -> {:?}\n",
                                success, url, path
                            ),
                        ),
                        _ => {}
                    }
                    true
                })
                .build()?;

            append_log(
                &log,
                &format!(
                    "[sigma-engine] launching sidecar \"sigma-engine\" --port {} (log at {})\n",
                    SIDECAR_PORT,
                    log_path.display()
                ),
            );

            // Locate the sidecar for this platform/target-triple. On failure,
            // log it and let the window open anyway -- a clear "engine
            // unavailable" screen beats a silent hard crash on startup.
            let sidecar_command = match app.shell().sidecar("sigma-engine") {
                Ok(command) => command.args(["--port", SIDECAR_PORT]),
                Err(err) => {
                    append_log(
                        &log,
                        &format!(
                            "[sigma-engine] SIDECAR ERROR: sidecar not found for this platform/target-triple: {}\n",
                            err
                        ),
                    );
                    return Ok(());
                }
            };

            // Spawn it. Same graceful-failure contract as above.
            let (mut rx, child) = match sidecar_command.spawn() {
                Ok(pair) => pair,
                Err(err) => {
                    append_log(
                        &log,
                        &format!("[sigma-engine] SIDECAR ERROR: failed to spawn sidecar: {}\n", err),
                    );
                    return Ok(());
                }
            };

            app.manage(SidecarProcess(Mutex::new(Some(child))));

            // Drain stdout/stderr so uvicorn's logging never blocks on a full
            // pipe buffer, mirror every line to both the console and the log
            // file, and record termination/errors so a crash is unmistakable.
            let log_for_task = Arc::clone(&log);
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) | CommandEvent::Stderr(line) => {
                            append_log(
                                &log_for_task,
                                &format!("[sigma-engine] {}", String::from_utf8_lossy(&line)),
                            );
                        }
                        CommandEvent::Terminated(payload) => {
                            append_log(
                                &log_for_task,
                                &format!("[sigma-engine] SIDECAR TERMINATED code={:?}\n", payload.code),
                            );
                        }
                        CommandEvent::Error(err) => {
                            append_log(&log_for_task, &format!("[sigma-engine] SIDECAR ERROR: {}\n", err));
                        }
                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app_handle = window.app_handle();
                // `try_state` (not `state`): if the sidecar failed to spawn we
                // never managed SidecarProcess, and the plain `state::<T>()`
                // would panic on close. Nothing to kill in that case.
                if let Some(state) = app_handle.try_state::<SidecarProcess>() {
                    // `.take()` as its own statement so the MutexGuard temporary
                    // is dropped immediately, before `child` (now a plain owned
                    // value with no outstanding borrow of `state`) is used below.
                    let child = state.0.lock().unwrap().take();
                    if let Some(child) = child {
                        // Best-effort: the window is closing either way. A failed
                        // kill here would mean the OS already reaped the process.
                        let _ = child.kill();
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
