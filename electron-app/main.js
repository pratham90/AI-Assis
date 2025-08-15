const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
      show: false,  
    transparent: true,
    frame: false, // No OS window border
    backgroundColor: '#00000000', // Fully transparent
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true,
      // Enable experimental features for speech recognition (if available)
      experimentalFeatures: true
    }
  });

  // Load the React build (adjust path if needed)
  win.loadFile(path.join(__dirname, '../frontend/build/index.html'));

  // Optional: Always on top
  // win.setAlwaysOnTop(true);
    win.once('ready-to-show', () => win.show());

  // 2) Force CSS overrides at runtime (bulletproof against build quirks)
  win.webContents.on('did-finish-load', () => {
    win.webContents.insertCSS(`
      html, body, #root { background: transparent !important; }
      .cluely-widget    { background: transparent !important; }
    `);
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
