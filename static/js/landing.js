// static/client/js/landing.js

/* LedgerMind AI - 沙盒體驗區邏輯 */
document.addEventListener("DOMContentLoaded", () => {
    initDemoTabs();
    initFileUpload();
    initDragDrop();
    loadDemoStatus();
});

/* ======================================================
   Demo Tabs
====================================================== */
function initDemoTabs() {
    const tabs = document.querySelectorAll(".tab-btn");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(item =>
                item.classList.remove("active")
            );
            tab.classList.add("active");
            const target = tab.dataset.target;
            if (target === "upload") {
                showUploadMode();
                setDemoStatus("請選擇或拖放發票圖片");
                return;
            }
            showPresetMode(target);
        });
    });
}

/* ======================================================
   Upload Mode
====================================================== */
function showUploadMode() {
    const imageWrapper = document.getElementById("imageWrapper");
    const dropzone = document.getElementById("dropzoneBox");
    if (imageWrapper)
        imageWrapper.style.display = "none";
    if (dropzone)
        dropzone.style.display = "flex";
}

function showPresetMode(target) {
    const imageWrapper = document.getElementById("imageWrapper");
    const dropzone = document.getElementById("dropzoneBox");
    if (imageWrapper)
        imageWrapper.style.display = "block";
    if (dropzone)
        dropzone.style.display = "none";
    if (target === "office") {
        setDemoStatus("上班族報帳 Demo，等待操作");
    }
    if (target === "family") {
        setDemoStatus("賣場大採購 Demo，等待操作");
    }
}

/* ======================================================
   File Upload
====================================================== */

function initFileUpload() {
    const input = document.getElementById("invoiceFileInput");
    const selectButton = document.getElementById("selectFileBtn");
    const changeButton = document.getElementById("changeFileBtn");
    if (!input) return;

    selectButton?.addEventListener("click", () => {
        input.click();
    });
    changeButton?.addEventListener("click", () => {
        input.click();
    });
    input.addEventListener("change", () => {
        const file = input.files?.[0];
        if (!file) return;
        handleFile(file);
    });
}

/* ======================================================
   Drag & Drop
====================================================== */
function initDragDrop() {
    const dropzone = document.getElementById("dropzoneBox");
    if (!dropzone) return;
    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(
            eventName,
            event => {
                event.preventDefault();
                dropzone.classList.add("dragover");
            }
        );
    });
    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(
            eventName,
            event => {
                event.preventDefault();
                dropzone.classList.remove("dragover");
            }
        );
    });

    dropzone.addEventListener("drop", event => {
        const file =
            event.dataTransfer.files?.[0];
        if (!file) return;
        handleFile(file);
    });
}

/* ======================================================
   File Processing
====================================================== */
function handleFile(file) {
    if (!isValidImage(file)) {
        setDemoStatus(
            "只允許 JPG、PNG、WEBP 圖片"
        );
        return;
    }
    previewImage(file);
    uploadDemo(file);
}

/* ======================================================
   Image Preview
====================================================== */
function previewImage(file) {
    const image = document.getElementById("demoImage");
    const imageWrapper = document.getElementById("imageWrapper");
    const dropzone = document.getElementById("dropzoneBox");
    const uploadActions = document.getElementById("uploadActions");
    if (!image) return;
    const url = URL.createObjectURL(file);
    image.src = url;
    if (imageWrapper)
        imageWrapper.style.display = "block";
    if (dropzone)
        dropzone.style.display = "none";
    if (uploadActions)
        uploadActions.style.display = "block";
}

/* ======================================================
   API
====================================================== */

async function uploadDemo(file) {
    setDemoStatus("正在上傳圖片...");
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
        const response =
            await fetch("/demo/scan", {
                method: "POST",
                body: formData
            });
        const data =
            await response.json();
        if (!response.ok) {
            throw new Error(
                data.message ||
                "Demo 辨識失敗"
            );
        }
        if (data.success === false) {
            throw new Error(
                data.message ||
                "Demo 辨識失敗"
            );
        }
        renderDemoResult(data);
    } catch (error) {
        console.error(
            "Demo upload error:",
            error
        );
        setDemoStatus(
            error.message ||
            "辨識失敗，請重新嘗試"
        );
    } finally {
        setLoading(false);
    }
}

/* ======================================================
   Render Result
====================================================== */

function renderDemoResult(data) {

    setDemoStatus("AI 辨識完成");


    const title =
        document.getElementById("resultTitle");

    const amount =
        document.getElementById("resultAmount");


    if (title)
        title.textContent = "成功辨識發票";


    if (amount) {

        const total =
            data["推算總金額"] ||
            data["總金額"] ||
            data["銷售額"] ||
            0;

        amount.textContent =
            formatMoney(total);

    }


    setText(
        "invoiceNumber",
        data["發票號碼"]
    );

    setText(
        "invoiceDate",
        data["開立日期"]
    );

    setText(
        "invoiceRandom",
        data["隨機碼"]
    );

    setText(
        "sellerId",
        data["賣方統編"]
    );

    setText(
        "buyerId",
        data["買方統編"]
    );

    setText(
        "recognitionMethod",
        data["辨識方法"]
    );

    setText(
        "encodingType",
        data["編碼類型"]
    );


    renderItems(data);

    renderCategories(data);


    if (data.remaining !== undefined) {

        updateRemaining(
            data.remaining
        );

    }


    setText(
        "timeSaved",
        "約 3 分鐘"
    );


    document
        .getElementById("resultCard")
        ?.classList.add("result-success");

}


/* ======================================================
   Items
====================================================== */

function renderItems(data) {

    const container =
        document.getElementById("itemsResult");

    if (!container) return;


    const items =
        splitValues(data["品項明細"]);

    const quantities =
        splitValues(data["品項數量"]);

    const prices =
        splitValues(data["品項單價"]);


    if (!items.length) {

        container.innerHTML =
            '<div class="empty-result">未取得品項明細</div>';

        return;

    }


    container.innerHTML = "";


    items.forEach((item, index) => {

        const row =
            document.createElement("div");

        row.className = "item-row";


        const name =
            document.createElement("span");

        name.textContent = item;


        const quantity =
            document.createElement("span");

        quantity.textContent =
            quantities[index] || "-";


        const price =
            document.createElement("span");

        price.textContent =
            formatMoney(
                prices[index] || 0
            );


        row.append(
            name,
            quantity,
            price
        );


        container.appendChild(row);

    });

}


/* ======================================================
   Category
====================================================== */

function renderCategories(data) {

    const list =
        document.getElementById("categoryList");

    if (!list) return;


    /*
       AIParser 未來如果回傳：

       {
           "分類": [
               {
                   "category": "食品",
                   "amount": 1200,
                   "item": "牛奶"
               }
           ]
       }

       目前先兼容這種格式。
    */

    const categories =
        data["分類"] ||
        data["categories"] ||
        data["分類結果"];


    if (!Array.isArray(categories)) {

        list.innerHTML =
            '<li class="empty-result">目前尚未取得 AI 分類結果</li>';

        return;

    }


    list.innerHTML = "";


    categories.forEach(item => {

        const li =
            document.createElement("li");


        const category =
            item.category ||
            item["分類"] ||
            "未分類";


        const amount =
            item.amount ||
            item["金額"] ||
            0;


        const name =
            item.item ||
            item["品項"] ||
            "";


        li.innerHTML = `
            <span class="cat-tag">
                ${escapeHtml(category)}
            </span>
            ${formatMoney(amount)}
            ${name ? ` (${escapeHtml(name)})` : ""}
        `;


        list.appendChild(li);

    });

}


/* ======================================================
   Demo Status
====================================================== */

async function loadDemoStatus() {

    try {

        const response =
            await fetch("/demo/");


        if (!response.ok) return;


        const data =
            await response.json();


        updateRemaining(
            data.remaining
        );


    } catch (error) {

        console.error(
            "Demo status error:",
            error
        );

    }

}


/* ======================================================
   UI Helpers
====================================================== */

function setDemoStatus(message) {

    const element =
        document.getElementById("statusText");

    if (element)
        element.textContent = message;

}


function setLoading(loading) {

    const laser =
        document.getElementById("laserLine");

    if (laser) {

        laser.style.display =
            loading ? "block" : "none";

    }

}


function setText(id, value) {

    const element =
        document.getElementById(id);

    if (!element) return;

    element.textContent =
        value ?? "—";

}


function updateRemaining(count) {

    setText(
        "remainingScans",
        count ?? 0
    );

}


function splitValues(value) {

    if (!value) return [];

    return String(value)
        .trim()
        .split(/\s+/)
        .filter(Boolean);

}


function formatMoney(value) {

    const number =
        Number(
            String(value)
                .replace(/,/g, "")
        );


    if (Number.isNaN(number))
        return "$0";


    return "$" +
        number.toLocaleString("zh-TW");

}


function isValidImage(file) {

    const allowed = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];


    return allowed.includes(
        file.type
    );

}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


/* ======================================================
   Hero
====================================================== */

function scrollToDemo() {

    document
        .getElementById("demo-section")
        ?.scrollIntoView({
            behavior: "smooth"
        });

}
