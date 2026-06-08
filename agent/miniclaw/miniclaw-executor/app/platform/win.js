/* 警告：必須遵守 RULES_MINI.md 規範 */
// Windows 平台專屬指令模組

const os = require('os');
const path = require('path');

module.exports = {
  name: 'Windows',

  screenshot(tempPath) {
    return `powershell -ExecutionPolicy Bypass -Command "[Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null; [Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; $b = New-Object Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $g = [Drawing.Graphics]::FromImage($b); $g.CopyFromScreen(0,0,0,0,$b.Size); $b.Save('${tempPath}', [Drawing.Imaging.ImageFormat]::Jpeg); $b.Dispose(); $g.Dispose();"`;
  },

  shutdown() {
    return { cmd: 'shutdown /s /t 60', cancel: 'shutdown /a', msg: '電腦將在 60 秒內關機！執行 shutdown /a 可取消。' };
  },

  listFiles(dir) {
    return `dir "${dir}"`;
  },

  networkCheck() {
    return 'ping -n 4 8.8.8.8 & ipconfig';
  },

  openBrowser(url) {
    return `start "" "${url}"`;
  },

  createFolder(folderPath) {
    return `mkdir "${folderPath}"`;
  },

  // Windows 不支援 termux-api 功能
  battery: null,
  camera: null,
  location: null,
  notify: null,
};
