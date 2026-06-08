/* 警告：必須遵守 RULES_MINI.md 規範 */
// macOS 平台專屬指令模組

const os = require('os');

module.exports = {
  name: 'macOS',

  screenshot(tempPath) {
    return `screencapture -t jpg '${tempPath}'`;
  },

  shutdown() {
    return { cmd: 'sudo shutdown -h +1', cancel: 'sudo shutdown -c', msg: '電腦將在 1 分鐘內關機！執行 sudo shutdown -c 可取消。' };
  },

  listFiles(dir) {
    return `ls -la "${dir}"`;
  },

  networkCheck() {
    return 'ping -c 4 8.8.8.8 && ifconfig';
  },

  openBrowser(url) {
    return `open "${url}"`;
  },

  createFolder(folderPath) {
    return `mkdir -p "${folderPath}"`;
  },

  battery: null,
  camera: null,
  location: null,
  notify: null,
};
