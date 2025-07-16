#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{AppHandle, Manager, State, WindowEvent};
use tokio::time::{sleep, Duration};
use actix_web::{App, HttpServer};
use actix_files as fs;

struct BackendProcess(Mutex<Option<Child>>);
struct WebServerHandle(Mutex<Option<actix_web::dev::ServerHandle>>);

#[derive(serde::Serialize)]
struct BackendStatus {
    running: bool,
    url: String,
}

#[tauri::command]
async fn check_backend_health() -> Result<BackendStatus, String> {
    let backend_url = "http://localhost:8885/graphql";
    
    match reqwest::get(backend_url).await {
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
    // First check if backend is already running and get the child process if needed
    {
        let mut process_guard = backend_process.0.lock().unwrap();
        
        // Check if backend is already running
        if process_guard.is_some() {
            return Ok(());
        }
        
        // Get the installation directory
        let resource_path = app_handle
            .path()
            .resource_dir()
            .map_err(|e| e.to_string())?;
        
        // In production, the backend exe is in the same directory as the main exe
        let backend_exe = if cfg!(debug_assertions) {
            // Development mode - use the Python script
            resource_path.join("..").join("..").join("..").join("apps").join("server").join("run.py")
        } else {
            // Production mode - use the bundled exe
            resource_path.parent()
                .ok_or("Failed to get parent directory")?
                .join("dipeo-server.exe")
        };
        
        log::info!("Starting backend from: {:?}", backend_exe);
        
        let child = if cfg!(debug_assertions) {
            // Development mode - run with Python
            Command::new("python")
                .arg(&backend_exe)
                .spawn()
                .map_err(|e| format!("Failed to start backend: {}", e))?
        } else {
            // Production mode - run the exe directly
            if !backend_exe.exists() {
                return Err(format!("Backend executable not found at: {:?}", backend_exe));
            }
            
            Command::new(&backend_exe)
                .spawn()
                .map_err(|e| format!("Failed to start backend: {}", e))?
        };
        
        *process_guard = Some(child);
    } // Lock is dropped here
    
    // Wait for backend to be ready
    for i in 0..30 {
        sleep(Duration::from_millis(500)).await;
        if let Ok(status) = check_backend_health().await {
            if status.running {
                log::info!("Backend started successfully after {} attempts", i + 1);
                return Ok(());
            }
        }
    }
    
    Err("Backend failed to start within 15 seconds".to_string())
}

#[tauri::command]
async fn stop_backend(backend_process: State<'_, BackendProcess>) -> Result<(), String> {
    let mut process_guard = backend_process.0.lock().unwrap();
    
    if let Some(mut child) = process_guard.take() {
        child.kill().map_err(|e| e.to_string())?;
        log::info!("Backend stopped");
    }
    
    Ok(())
}

#[tauri::command]
async fn start_web_server(
    app_handle: AppHandle,
    web_server_handle: State<'_, WebServerHandle>,
) -> Result<(), String> {
    let mut server_guard = web_server_handle.0.lock().unwrap();
    
    // Check if server is already running
    if server_guard.is_some() {
        return Ok(());
    }
    
    // Get the web directory
    let resource_path = app_handle
        .path()
        .resource_dir()
        .map_err(|e| e.to_string())?;
    
    let web_dir = if cfg!(debug_assertions) {
        // Development mode - use the built web files
        resource_path.join("..").join("..").join("..").join("apps").join("web").join("dist")
    } else {
        // Production mode - use the installed web files
        resource_path.parent()
            .ok_or("Failed to get parent directory")?
            .join("web")
    };
    
    if !web_dir.exists() {
        return Err(format!("Web directory not found at: {:?}", web_dir));
    }
    
    log::info!("Serving web files from: {:?}", web_dir);
    
    // Start the web server
    let server = HttpServer::new(move || {
        App::new()
            .service(fs::Files::new("/", web_dir.clone())
                .index_file("index.html")
                .show_files_listing())
    })
    .bind(("127.0.0.1", 8871))
    .map_err(|e| format!("Failed to bind web server: {}", e))?
    .run();
    
    let handle = server.handle();
    *server_guard = Some(handle);
    drop(server_guard); // Release the lock
    
    // Spawn the server in a separate task
    tauri::async_runtime::spawn(async move {
        let _ = server.await;
    });
    
    log::info!("Web server started on http://localhost:8871");
    Ok(())
}

#[tauri::command]
async fn stop_web_server(web_server_handle: State<'_, WebServerHandle>) -> Result<(), String> {
    // Take the handle out of the mutex to avoid holding the lock across await
    let handle = {
        let mut server_guard = web_server_handle.0.lock().unwrap();
        server_guard.take()
    }; // Lock is dropped here
    
    if let Some(handle) = handle {
        handle.stop(true).await;
        log::info!("Web server stopped");
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
        .manage(WebServerHandle(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            check_backend_health,
            start_backend,
            stop_backend,
            start_web_server,
            stop_web_server
        ])
        .setup(|app| {
            // Clone handles for async block before moving into spawn
            let app_handle_backend = app.handle().clone();
            let app_handle_web = app.handle().clone();
            
            // Start servers in background
            tauri::async_runtime::spawn(async move {
                log::info!("Starting services...");
                
                // Get state inside the async block
                let backend_state = app_handle_backend.state::<BackendProcess>();
                let web_server_state = app_handle_web.state::<WebServerHandle>();
                
                // Start backend first
                if let Err(e) = start_backend(app_handle_backend.clone(), backend_state).await {
                    log::error!("Failed to start backend: {}", e);
                } else {
                    log::info!("Backend started successfully");
                }
                
                // Then start web server
                if let Err(e) = start_web_server(app_handle_web.clone(), web_server_state).await {
                    log::error!("Failed to start web server: {}", e);
                } else {
                    log::info!("Web server started successfully");
                }
            });
            
            // Set the window to load from our local server
            if let Some(window) = app.get_webview_window("main") {
                tauri::async_runtime::spawn(async move {
                    // Wait a bit for servers to start
                    sleep(Duration::from_secs(3)).await;
                    let _ = window.eval("window.location.href = 'http://localhost:8871'");
                });
            }
            
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                // Stop both processes when window closes
                let backend_process = window.state::<BackendProcess>();
                let web_server_handle = window.state::<WebServerHandle>();
                
                if let Err(e) = tauri::async_runtime::block_on(stop_backend(backend_process)) {
                    log::error!("Failed to stop backend: {}", e);
                }
                
                if let Err(e) = tauri::async_runtime::block_on(stop_web_server(web_server_handle)) {
                    log::error!("Failed to stop web server: {}", e);
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}