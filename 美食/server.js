const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const port = 3000;

// 創建或連接到 SQLite 資料庫
const db = new sqlite3.Database('./database.db', (err) => {
    if (err) {
        console.error('資料庫連接錯誤：', err.message);
    } else {
        console.log('已連接到 SQLite 資料庫');
    }
});

// 創建 contacts 表（如果不存在）
db.run(`CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL
)`);

// 使用 bodyParser 解析表單數據
app.use(bodyParser.urlencoded({ extended: true }));

// 服務靜態文件
app.use(express.static(path.join(__dirname, 'public')));

// 處理表單提交
app.post('/submit_contact_form', (req, res) => {
    const { name, email, message } = req.body;
    const sql = `INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)`;
    db.run(sql, [name, email, message], function(err) {
        if (err) {
            console.error('插入數據時出錯：', err.message);
            res.status(500).send('表單提交失敗');
        } else {
            console.log(`數據已插入：${this.lastID}`);
            res.send('表單提交成功');
        }
    });
});

app.listen(port, () => {
    console.log(`伺服器運行在 http://localhost:${port}`);
});
