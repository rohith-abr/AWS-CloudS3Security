const { app, BrowserWindow } = require('electron');
const { exec } = require('child_process');

let flaskProcess;

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  
  setTimeout(() => {
    win.loadURL('http://localhost:4030');
  }, 2000);

  win.on('closed', () => {
    if (flaskProcess) flaskProcess.kill();
  });
}

app.whenReady().then(() => {
  flaskProcess = exec('./venv/bin/python3 app.py', (error, stdout, stderr) => {
    if (error) {
      console.error(`❌ Flask Error: ${error.message}`);
      return;
    }
    if (stderr) console.error(`⚠️ Flask stderr: ${stderr}`);
    console.log(`✅ Flask stdout: ${stdout}`);
  });

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (flaskProcess) flaskProcess.kill();
    app.quit();
  }
});