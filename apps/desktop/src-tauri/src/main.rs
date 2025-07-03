#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{AppHandle, Manager, State, WindowEvent};
use tokio::time::{sleep, Duration};

struct BackendProcess(Mutex<Option<Child>>);

#[derive(serde::Serialize)]
struct BackendStatus {
    running: bool,
    url: String,
}

#[tauri::command]
async fn check_backend_health() -> Result<BackendStatus, String> {
    let backend_url = "http://localhost:8000/graphql";
    
    match reqwest::get(&backend_url).await {
        Ok(_) => Ok(BackendStatus {
            running: true,
            url: backend_url.to_string(),
        }),
        Err(_) => Ok(BackendStatus {
            running: false,
            url: backend_url.to_string(),
        }),
    }
}

#[tauri::command]
async fn start_backend(
    app_handle: AppHandle,
    backend_process: State<'_, BackendProcess>,
) -> Result<(), String> {
    let mut process_guard = backend_process.0.lock().unwrap();
    
    // Check if backend is already running
    if process_guard.is_some() {
        return Ok(());
    }
    
    // Get the path to the bundled backend executable
    let resource_path = app_handle
        .path()
        .resource_dir()
        .map_err(|e| e.to_string())?;
    
    let backend_exe = resource_path.join("dipeo-server.exe");
    
    if !backend_exe.exists() {
        return Err(format!("Backend executable not found at: {:?}", backend_exe));
    }
    
    // Start the backend process
    let child = Command::new(&backend_exe)
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;
    
    *process_guard = Some(child);
    
    // Wait for backend to be ready
    for _ in 0..30 {
        sleep(Duration::from_millis(500)).await;
        if check_backend_health().await.is_ok() {
            return Ok(());
        }
    }
    
    Err("Backend failed to start within 15 seconds".to_string())
}

#[tauri::command]
async fn stop_backend(backend_process: State<'_, BackendProcess>) -> Result<(), String> {
    let mut process_guard = backend_process.0.lock().unwrap();
    
    if let Some(mut child) = process_guard.take() {
        child.kill().map_err(|e| e.to_string())?;
    }
    
    Ok(())
}

fn main() {
    env_logger::init();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_http::init())
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            check_backend_health,
            start_backend,
            stop_backend
        ])
        .setup(|app| {
            let backend_process = app.state::<BackendProcess>();
            
            // Clone the app handle for the spawned task
            let app_handle = app.handle().clone();
            let backend_process_clone = backend_process.inner().clone();
            
            // Start backend when app starts
            tauri::async_runtime::spawn(async move {
                if let Err(e) = start_backend(app_handle, State(backend_process_clone)).await {
                    log::error!("Failed to start backend: {}", e);
                }
            });
            
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                // Stop backend when window closes
                let backend_process = window.state::<BackendProcess>();
                if let Err(e) = tauri::async_runtime::block_on(stop_backend(backend_process)) {
                    log::error!("Failed to stop backend: {}", e);
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}