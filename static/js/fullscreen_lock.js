function enterFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) el.requestFullscreen();
    else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    else if (el.msRequestFullscreen) el.msRequestFullscreen();
}

function createOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'fullscreen-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = 0;
    overlay.style.left = 0;
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0, 0, 0, 0.85)';
    overlay.style.zIndex = '9999';
    overlay.style.display = 'flex';
    overlay.style.flexDirection = 'column';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.color = '#fff';
    overlay.innerHTML = `
        <h3 class="mb-3">🔒 已退出全螢幕模式</h3>
        <p>請輸入密碼以繼續瀏覽</p>
        <input type="password" id="fs-password" class="form-control text-center" placeholder="輸入密碼" style="width: 200px;">
        <button onclick="verifyFullscreenPassword()" class="btn btn-light mt-3">確認</button>
    `;
    document.body.appendChild(overlay);
}

function removeOverlay() {
    const overlay = document.getElementById('fullscreen-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function verifyFullscreenPassword() {
    const pw = document.getElementById('fs-password').value;
    if (pw === 'hsu1952') {
        alert("✅ 密碼正確，已解除鎖定");
        removeOverlay();
    } else {
        alert("❌ 密碼錯誤，將重新進入全螢幕");
        enterFullscreen();
    }
}

function handleFullscreenChange() {
    if (!document.fullscreenElement) {
        createOverlay();  // 顯示遮罩並要求輸入密碼
    }
}

function setupFullscreenLock() {
    document.addEventListener('click', function once() {
        enterFullscreen();
        document.removeEventListener('click', once);
    });

    document.addEventListener('fullscreenchange', handleFullscreenChange);
}
