<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KataGo围棋人机对弈</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            color: #333;
        }
        .board-container {
            margin: 20px 0;
        }
        .board {
            position: relative;
            width: 570px;
            height: 570px;
            background-color: #d4a76a;
            padding: 15px;
            border: 2px solid #8b4513;
        }
        .board-grid {
            position: absolute;
            top: 15px;
            left: 15px;
            width: 540px;
            height: 540px;
            background-image: 
                linear-gradient(rgba(139, 69, 19, 0.3) 1px, transparent 1px),
                linear-gradient(90deg, rgba(139, 69, 19, 0.3) 1px, transparent 1px);
            background-size: 30px 30px;
        }
        .cell {
            position: absolute;
            width: 30px;
            height: 30px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .stone {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        .stone-black {
            background-color: black;
        }
        .stone-white {
            background-color: white;
        }
        .controls {
            margin: 20px 0;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin: 0 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .status {
            margin: 10px 0;
            font-size: 18px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>KataGo围棋人机对弈</h1>
    <div class="status">
        当前回合: <span id="current-player">黑棋</span>
        <div class="difficulty-selector">
            难度: 
            <select id="difficulty" onchange="changeDifficulty()">
                <option value="easy">业余六级</option>
                <option value="medium" selected>业余三段</option>
                <option value="hard">业余一段</option>
                <option value="expert">职业初段</option>
                <option value="professional">职业九段</option>
            </select>
        </div>
    </div>
    <div class="board-container">
        <div class="board" id="board"></div>
    </div>
    <div class="controls">
        <button onclick="resetBoard()">重置棋盘</button>
    </div>

    <script>
        let board = [];
        let currentPlayer = 1;

        // 初始化棋盘
        function initBoard() {
            const boardElement = document.getElementById('board');
            boardElement.innerHTML = '';
            
            // 添加网格
            const grid = document.createElement('div');
            grid.classList.add('board-grid');
            boardElement.appendChild(grid);
            
            for (let i = 0; i < 19; i++) {
                board[i] = [];
                for (let j = 0; j < 19; j++) {
                    board[i][j] = 0;
                    const cell = document.createElement('div');
                    cell.classList.add('cell');
                    cell.dataset.x = i;
                    cell.dataset.y = j;
                    // 设置绝对定位，使交叉点位于网格线的交点
                    cell.style.left = `${j * 30}px`;
                    cell.style.top = `${i * 30}px`;
                    cell.addEventListener('click', () => makeMove(i, j));
                    boardElement.appendChild(cell);
                }
            }
        }

        // 绘制棋盘
        function drawBoard() {
            const cells = document.querySelectorAll('.cell');
            cells.forEach(cell => {
                const x = parseInt(cell.dataset.x);
                const y = parseInt(cell.dataset.y);
                cell.innerHTML = '';
                
                if (board[x][y] === 1) {
                    const stone = document.createElement('div');
                    stone.classList.add('stone', 'stone-black');
                    cell.appendChild(stone);
                } else if (board[x][y] === 2) {
                    const stone = document.createElement('div');
                    stone.classList.add('stone', 'stone-white');
                    cell.appendChild(stone);
                }
            });
        }

        // 落子
        function makeMove(x, y) {
            fetch('/make_move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({x, y})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    board = data.board;
                    // 始终显示为黑棋，因为AI落子后应该由人类继续落子
                    document.getElementById('current-player').textContent = '黑棋';
                    drawBoard();
                }
            });
        }

        // 重置棋盘
        function resetBoard() {
            fetch('/reset', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    board = data.board;
                    // 始终显示为黑棋，因为重置后应该由人类开始落子
                    document.getElementById('current-player').textContent = '黑棋';
                    initBoard();
                }
            });
        }

        // 更改难度级别
        function changeDifficulty() {
            const difficulty = document.getElementById('difficulty').value;
            fetch('/set_difficulty', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({difficulty: difficulty})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('难度级别已更改，将在新游戏中生效');
                }
            });
        }

        // 初始化
        initBoard();
    </script>
</body>
</html>
