/* 警告：必須遵守 RULES_MINI.md 規範 */
// Linux 平台專屬指令模組

module.exports = {
  name: 'Linux',

  screenshot(tempPath) {
    return `scrot '${tempPath}'`;
  },

  shutdown() {
    return { cmd: 'shutdown -h +1', cancel: 'shutdown -c', msg: '電腦將在 1 分鐘內關機！執行 shutdown -c 可取消。' };
  },

  listFiles(dir) {
    return `ls -la "${dir}"`;
  },

  networkCheck() {
    return 'ping -c 4 8.8.8.8 && ifconfig';
  },

  openBrowser(url) {
    return `xdg-open "${url}"`;
  },

  createFolder(folderPath) {
    return `mkdir -p "${folderPath}"`;
  },

  battery: null,
  camera: null,
  location: null,
  notify: null,
};
