//! Tauri backend for the M1 packaging spike.
//!
//! On launch: spawns the sigma-engine sidecar and stores its handle in
//! managed state. On window close: kills it. The frontend (src/App.tsx)
//! never talks to Rust via IPC for any of this -- it polls the sidecar's own
//! HTTP API directly at 127.0.0.1 -- so this file's only job is sidecar
//! lifecycle.

use std::sync::Mutex;

use tauri::Manager;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

// Must match sigma_engine.main.DEFAULT_PORT (engine/sigma_engine/main.py) and
// ENGINE_BASE_URL in desktop/src/App.tsx. Nothing shares this constant across
// the Rust/Python/TS boundary in this spike, so it's duplicated by hand in
// three places -- worth centralizing if the spike grows into the real app.
const SIDECAR_PORT: &str = "8756";

/// Holds the running sidecar's process handle so it can be killed later.
/// `Option` because it's taken (not just read) on shutdown -- `CommandChild::kill`
/// consumes `self`, so ownership has to move out of the Mutex to call it.
struct SidecarProcess(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let sidecar_command = app
                .shell()
                .sidecar("sigma-engine")
                .expect("sigma-engine sidecar not found for this platform/target-triple")
                .args(["--port", SIDECAR_PORT]);

            let (mut rx, child) = sidecar_command
                .spawn()
                .expect("failed to spawn sigma-engine sidecar");

            app.manage(SidecarProcess(Mutex::new(Some(child))));

            // Drain stdout/stderr so uvicorn's logging never blocks on a full
            // pipe buffer, and forward lines to this process's own stdout for
            // local debugging (`npm run tauri dev`).
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    if let CommandEvent::Stdout(line) | CommandEvent::Stderr(line) = event {
                        print!("[sigma-engine] {}", String::from_utf8_lossy(&line));
                    }
                }
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app_handle = window.app_handle();
                let state = app_handle.state::<SidecarProcess>();
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
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
