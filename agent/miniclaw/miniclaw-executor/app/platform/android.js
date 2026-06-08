/* 警告：必須遵守 RULES_MINI.md 規範 */
// Android (Termux) 平台專屬指令模組
// 需要安裝：pkg install termux-api，並安裝 Termux:API app

module.exports = {
  name: 'Android',

  screenshot(tempPath) {
    // Android 截圖需要 termux-api
    return `termux-screenshot -f '${tempPath}'`;
  },

  shutdown() {
    // Android 無法直接關機（需 root），改為鎖定螢幕
    return { cmd: 'termux-torch off', cancel: null, msg: '⚠️ Android 無法直接關機，已關閉手電筒。如需關機請手動操作。' };
  },

  listFiles(dir) {
    return `ls -la "${dir}"`;
  },

  networkCheck() {
    return 'ping -c 4 8.8.8.8 && ifconfig';
  },

  // 用手機開瀏覽器查詢（核心功能）
  openBrowser(url) {
    return `termux-open-url "${url}"`;
  },

  createFolder(folderPath) {
    return `mkdir -p "${folderPath}"`;
  },

  // Android 專屬功能
  battery() {
    return 'termux-battery-status';
  },

  camera(outputPath) {
    return `termux-camera-photo -c 0 "${outputPath}"`;
  },

  location() {
    return 'termux-location';
  },

  notify(title, content) {
    return `termux-notification --title "${title}" --content "${content}"`;
  },

  sms(number, message) {
    return `termux-sms-send -n "${number}" "${message}"`;
  },
};
