// 主入口文件
document.addEventListener('DOMContentLoaded', () => {
  // 初始化各个模块
  initPowerModule();
  initPwmModule();
  initSensorDataModule();
  initAiAdviceModule();
  
  // 启动时间更新
  updateTime();
  setInterval(updateTime, 1000);
});