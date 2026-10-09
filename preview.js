const viewer = document.getElementById('mascot');
const play = document.getElementById('play');
const restart = document.getElementById('restart');
const reset = document.getElementById('reset');
const timeline = document.getElementById('timeline');
const time = document.getElementById('time');
const arButton = document.getElementById('launch-ar');
const arHelp = document.getElementById('ar-help');
const arPrompt = document.getElementById('ar-prompt');
let ready = false;
let arCheckTimer;
function syncAR() {
  arButton.disabled = !ready || !viewer.canActivateAR;
  arHelp.textContent = !ready ? '3Dアニメーションを読み込み中です。'
    : viewer.canActivateAR ? 'ARを開き、端末をゆっくり動かして床を認識させてください。うさぎとボールを空間に配置できます。'
    : 'この端末・ブラウザでは床認識ARを利用できません。対応端末でSafariまたはChromeを使ってください。3Dアニメーションは引き続き利用できます。';
}
function refreshAR() {
  clearInterval(arCheckTimer);
  syncAR();
  let attempts = 0;
  arCheckTimer = window.setInterval(() => {
    syncAR();
    if (viewer.canActivateAR || ++attempts >= 30) clearInterval(arCheckTimer);
  },500);
}
function arError() {
  const notice = document.getElementById('notice');
  notice.hidden = false;
  notice.textContent = 'ARを開始できませんでした。対応端末でSafariまたはChromeを使い、カメラの許可を確認してください。AndroidはGoogle Play開発者サービス（AR）も必要です。';
}
viewer.addEventListener('load', () => {
  ready = true;
  document.getElementById('loading').hidden = true;
  for (const control of [play, restart, reset, timeline]) control.disabled = false;
  viewer.play();
  refreshAR();
});
viewer.addEventListener('error', () => {
  ready = false;
  clearInterval(arCheckTimer);
  arButton.disabled = true;
  const notice = document.getElementById('notice');
  notice.hidden = false;
  notice.textContent = '3Dアニメーションを読み込めませんでした。ChromeまたはSafariでお試しください。';
  document.getElementById('loading').hidden = true;
  for (const control of [play,restart,reset,timeline]) control.disabled = true;
  arHelp.textContent = '3Dモデルを読み込めなかったため、ARを開始できません。';
});
arButton.addEventListener('click', async () => {
  if (!ready || !viewer.canActivateAR) return;
  document.getElementById('notice').hidden = true;
  viewer.play();
  play.textContent = '一時停止';
  try { await viewer.activateAR(); } catch { arError(); }
});
viewer.addEventListener('ar-status', event => {
  if (event.detail.status === 'failed') arError();
  if (event.detail.status === 'session-started') { viewer.play(); play.textContent = '一時停止'; }
  if (event.detail.status === 'not-presenting') refreshAR();
});
viewer.addEventListener('ar-tracking', event => {
  arPrompt.textContent = event.detail.status === 'not-tracking'
    ? '位置を確認しています。明るい場所で床を映し、端末をゆっくり動かしてください。'
    : '端末をゆっくり動かして、床やテーブルを映してください。';
});
window.addEventListener('pageshow',refreshAR);
play.addEventListener('click', () => {
  if (viewer.paused) { viewer.play(); play.textContent = '一時停止'; }
  else { viewer.pause(); play.textContent = '再生'; }
});
restart.addEventListener('click', () => { viewer.currentTime = 0; viewer.play(); play.textContent = '一時停止'; });
reset.addEventListener('click', () => {
  viewer.cameraOrbit = '0deg 78deg 3.1m';
  viewer.cameraTarget = '-.36m .76m 0m';
  viewer.fieldOfView = '36deg';
  viewer.jumpCameraToGoal();
});
timeline.addEventListener('input', () => {
  viewer.pause();
  viewer.currentTime = Number(timeline.value);
  play.textContent = '再生';
});
function updateTime() {
  if (ready) {
    timeline.value = viewer.currentTime;
    time.textContent = `${viewer.currentTime.toFixed(1)} / 10秒`;
  }
  requestAnimationFrame(updateTime);
}
requestAnimationFrame(updateTime);
