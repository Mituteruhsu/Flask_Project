// static/client/js/landing.js

/* LedgerMind AI - 沙盒體驗區邏輯 */

const demoScenarios = {
    office: {
        img: '/static/images/demo_office.jpg',
        title: '成功辨識 2 張收據！',
        amount: '$1,680',
        categories: [
            { name: '交通差旅', detail: '$1,200 (台灣高鐵)' },
            { name: '文具用品', detail: '$480 (辦公用紙)' }
        ],
        timeSaved: '約 3 分鐘！'
    },
    family: {
        img: '/static/images/demo_family.jpg',
        title: '成功辨識 3 張發票！',
        amount: '$3,250',
        categories: [
            { name: '餐飲伙食', detail: '$2,100 (牛肉、鮮乳)' },
            { name: '生活用品', detail: '$1,150 (日用品)' }
        ],
        timeSaved: '約 5 分鐘！'
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const imageWrapper = document.getElementById('imageWrapper');
    const dropzoneBox = document.getElementById('dropzoneBox');
    const demoImage = document.getElementById('demoImage');
    const laserLine = document.getElementById('laserLine');
    const statusText = document.getElementById('statusText');
    const resultTitle = document.getElementById('resultTitle');
    const resultAmount = document.getElementById('resultAmount');
    const categoryList = document.getElementById('categoryList');
    const timeSaved = document.getElementById('timeSaved');
    const fileInput = document.getElementById('invoiceFileInput');

    // 1. 頁籤切換處理
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const target = button.getAttribute('data-target');

            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            if (target === 'upload') {
                // 切換至真實上傳模式
                imageWrapper.style.display = 'none';
                dropzoneBox.style.display = 'flex';
                statusText.innerText = '等待上傳發票照片...';
            } else {
                // 切換回預設模式
                dropzoneBox.style.display = 'none';
                imageWrapper.style.display = 'block';

                const data = demoScenarios[target];
                triggerScanAnimation(() => {
                    demoImage.src = data.img;
                    resultTitle.innerText = data.title;
                    resultAmount.innerText = data.amount;
                    timeSaved.innerText = data.timeSaved;

                    categoryList.innerHTML = '';
                    data.categories.forEach(cat => {
                        const li = document.createElement('li');
                        li.innerHTML = `<span class="cat-tag">${cat.name}</span> ${cat.detail}`;
                        categoryList.appendChild(li);
                    });
                });
            }
        });
    });

    // 2. 模擬掃描動畫
    function triggerScanAnimation(callback) {
        statusText.innerText = 'AI 掃描辨識中...';
        laserLine.classList.add('scanning');
        demoImage.style.opacity = '0.4';

        setTimeout(() => {
            laserLine.classList.remove('scanning');
            demoImage.style.opacity = '1';
            callback();
            statusText.innerText = '辨識完成！數據已自動歸類';
        }, 1200);
    }

    // 3. 處理使用者真實上傳發票 (Drop & Select)
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files;
            if (file) {
                uploadAndProcessInvoice(file);
            }
        });
    }

    // 拖放事件監聽
    dropzoneBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzoneBox.style.borderColor = '#3bf6b8';
    });

    dropzoneBox.addEventListener('dragleave', () => {
        dropzoneBox.style.borderColor = '#335541';
    });

    dropzoneBox.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzoneBox.style.borderColor = '#335541';
        if (e.dataTransfer.files.length > 0) {
            uploadAndProcessInvoice(e.dataTransfer.files);
        }
    });

    // 4. AJAX 上傳至沙盒 API
    function uploadAndProcessInvoice(file) {
        const formData = new FormData();
        formData.append('file', file);

        statusText.innerText = '圖片上傳中，正在進行 AI OCR 分析...';

        fetch('/api/demo/scan', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(res => {
            if (res.success) {
                const data = res.data;
                resultTitle.innerText = `辨識成功：${data.title}`;
                resultAmount.innerText = `$${data.total_amount}`;
                timeSaved.innerText = `約 ${data.time_saved_seconds / 60} 分鐘！`;

                categoryList.innerHTML = '';
                const li = document.createElement('li');
                li.innerHTML = `<span class="cat-tag">${data.category}</span> 全數項目正確抓取`;
                categoryList.appendChild(li);

                statusText.innerText = '真實圖片辨識成功！';
            } else {
                alert(`辨識失敗: ${res.message}`);
                statusText.innerText = '請重試或上傳清晰照片';
            }
        })
        .catch(err => {
            console.error(err);
            alert('伺服器辨識發生錯誤');
            statusText.innerText = '系統忙碌中';
        });
    }
});