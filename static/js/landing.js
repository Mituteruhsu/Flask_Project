// static/client/js/landing.js

/* SmartLedger AI Landing Page 互動 logic */
// 關卡預設數據集 (模擬 AI 辨識結果)
const demoScenarios = {
    office: {
        img: '/static/images/demo_office.jpg',
        title: '成功辨識 2 張收據！',
        amount: '$1,680',
        categories: [
            { name: '交通差旅', detail: '$1,200 (台灣高鐵)' },
            { name: '文具用品', detail: '$480 (辦公用紙、筆)' }
        ],
        timeSaved: '約 3 分鐘！'
    },
    family: {
        img: '/static/images/demo_family.jpg',
        title: '成功辨識 3 張發票（含長發票）！',
        amount: '$3,250',
        categories: [
            { name: '餐飲伙食', detail: '$2,100 (牛肉、鮮乳)' },
            { name: '生活用品', detail: '$1,150 (衛生紙、洗髮精)' }
        ],
        timeSaved: '約 5 分鐘！'
    },
    multi: {
        img: '/static/images/demo_multi.jpg',
        title: '成功辨識 4 張感熱紙紙本發票！',
        amount: '$2,410',
        categories: [
            { name: '日常雜支', detail: '$810 (超商咖啡、餐包)' },
            { name: '娛樂消費', detail: '$1,600 (電影票)' }
        ],
        timeSaved: '約 6 分鐘！'
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const demoImage = document.getElementById('demoImage');
    const laserLine = document.getElementById('laserLine');
    const statusText = document.getElementById('statusText');
    const resultTitle = document.getElementById('resultTitle');
    const resultAmount = document.getElementById('resultAmount');
    const categoryList = document.getElementById('categoryList');
    const timeSaved = document.getElementById('timeSaved');

    // 切換頁籤與觸發 AI 辨識動畫
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetScenario = button.getAttribute('data-target');
            const data = demoScenarios[targetScenario];

            // 1. 更新按鈕 UI
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // 2. 開始模擬辨識狀態
            statusText.innerText = 'AI 掃描辨識中...';
            laserLine.classList.add('scanning');
            demoImage.style.opacity = '0.5';

            // 3. 模擬 1.5 秒後產出結果
            setTimeout(() => {
                // 更新圖片與內容
                demoImage.src = data.img;
                demoImage.style.opacity = '1';
                laserLine.classList.remove('scanning');

                resultTitle.innerText = data.title;
                resultAmount.innerText = data.amount;
                timeSaved.innerText = data.timeSaved;

                // 渲染動態分類清單
                categoryList.innerHTML = '';
                data.categories.forEach(cat => {
                    const li = document.createElement('li');
                    li.innerHTML = `<span class="cat-tag">${cat.name}</span> ${cat.detail}`;
                    categoryList.appendChild(li);
                });

                statusText.innerText = '辨識完成！數據已自動歸載';
            }, 1500);
        });
    });
});

// 平滑滾動至 Demo 區域
function scrollToDemo() {
    const demoSection = document.getElementById('demo-section');
    if (demoSection) {
        demoSection.scrollIntoView({ behavior: 'smooth' });
    }
}
