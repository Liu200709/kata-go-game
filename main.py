import http.server
import socketserver
import json
import subprocess
import time
import urllib.parse

# 全局变量存储棋盘状态
board = [[0 for _ in range(19)] for _ in range(19)]  # 0: 空, 1: 黑, 2: 白
current_player = 1  # 1: 黑, 2: 白
katago_process = None
difficulty = "medium"  # 难度级别: easy, medium, hard, expert, professional
previous_board = None  # 用于打劫检测
game_over = False  # 棋局是否结束
komi = 7.5  # 黑棋贴目（中国围棋协会标准：7.5目）

# 中国围棋协会官方规则 - 棋盘规格
BOARD_SIZE = 19
STAR_POINTS = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]  # 星位
TENGEN = (9, 9)  # 天元

# 检查位置是否在棋盘范围内
def is_valid_position(x, y):
    return 0 <= x < 19 and 0 <= y < 19

# 获取相邻位置
def get_neighbors(x, y):
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if is_valid_position(nx, ny):
            neighbors.append((nx, ny))
    return neighbors

# 获取一个位置的 liberties（气）
def get_liberties(x, y):
    if not is_valid_position(x, y) or board[x][y] == 0:
        return 0

    visited = set()
    stack = [(x, y)]
    visited.add((x, y))
    liberties = 0

    while stack:
        cx, cy = stack.pop()
        for nx, ny in get_neighbors(cx, cy):
            if (nx, ny) not in visited:
                if board[nx][ny] == 0:
                    liberties += 1
                elif board[nx][ny] == board[cx][cy]:
                    visited.add((nx, ny))
                    stack.append((nx, ny))

    return liberties

# 移除没有气的棋子
def remove_dead_stones(player):
    removed = []
    visited = set()

    for i in range(19):
        for j in range(19):
            if board[i][j] == player and (i, j) not in visited:
                # 检查这个棋子是否有气
                if get_liberties(i, j) == 0:
                    # 移除所有相连的同色棋子
                    stack = [(i, j)]
                    group = []
                    while stack:
                        cx, cy = stack.pop()
                        if (cx, cy) not in visited and board[cx][cy] == player:
                            visited.add((cx, cy))
                            group.append((cx, cy))
                            for nx, ny in get_neighbors(cx, cy):
                                if board[nx][ny] == player:
                                    stack.append((nx, ny))
                    # 移除这个 group
                    for cx, cy in group:
                        board[cx][cy] = 0
                        removed.append((cx, cy))

    return removed

# 检查落子是否合法（根据中国围棋协会规则）
def is_valid_move(x, y, player):
    # 检查位置是否为空
    if board[x][y] != 0:
        return False

    # 模拟落子
    board[x][y] = player

    # 检查是否有气（中国围棋协会规则第3条）
    if get_liberties(x, y) > 0:
        # 检查是否会提掉对方的棋子
        opponent = 1 if player == 2 else 2
        remove_dead_stones(opponent)

        # 检查是否是打劫（中国围棋协会规则第6条）
        global previous_board
        if previous_board:
            if board == previous_board:
                # 恢复棋盘
                board[x][y] = 0
                return False

        # 恢复棋盘
        board[x][y] = 0
        return True
    else:
        # 检查是否会提掉对方的棋子
        opponent = 1 if player == 2 else 2
        removed = remove_dead_stones(opponent)

        # 如果提掉了对方的棋子，那么这个落子是合法的
        if removed:
            # 恢复棋盘
            board[x][y] = 0
            # 恢复被提掉的棋子
            for rx, ry in removed:
                board[rx][ry] = opponent
            return True
        else:
            # 恢复棋盘
            board[x][y] = 0
            return False

# 执行落子
def make_move(x, y, player):
    global game_over
    if not is_valid_move(x, y, player):
        return False

    # 保存当前棋盘状态用于打劫检测
    global previous_board
    previous_board = [row[:] for row in board]

    # 执行落子
    board[x][y] = player

    # 提掉对方没有气的棋子
    opponent = 1 if player == 2 else 2
    remove_dead_stones(opponent)

    # 检查是否终局
    if is_game_over():
        game_over = True

    return True

# 计算某一方围住的目数（中国围棋协会规则第9条）
def count_territory(player):
    """计算player围住的目数"""
    visited = set()
    territory = 0

    for i in range(19):
        for j in range(19):
            if board[i][j] == 0 and (i, j) not in visited:
                # 使用BFS/DFS遍历确定这片空地的归属
                group_visited = set()
                stack = [(i, j)]
                group_visited.add((i, j))
                is_black_territory = True
                is_white_territory = True

                while stack:
                    cx, cy = stack.pop()
                    for nx, ny in get_neighbors(cx, cy):
                        if (nx, ny) not in group_visited:
                            if board[nx][ny] == 0:
                                group_visited.add((nx, ny))
                                stack.append((nx, ny))
                            elif board[nx][ny] == 1:
                                is_white_territory = False
                            elif board[nx][ny] == 2:
                                is_black_territory = False

                # 更新visited
                visited.update(group_visited)

                # 统计目数
                if is_black_territory and not is_white_territory:
                    territory += len(group_visited)
                elif is_white_territory and not is_black_territory:
                    territory += len(group_visited)

    return territory

# 检查棋局是否结束（中国围棋协会规则第7条）
def is_game_over():
    """检查棋局是否结束"""
    # 检查棋盘是否为空（棋局刚开始）
    has_stones = any(board[i][j] != 0 for i in range(19) for j in range(19))
    if not has_stones:
        return False

    # 检查是否可以继续下棋
    for i in range(19):
        for j in range(19):
            if board[i][j] == 0:
                # 检查黑棋是否可以落子
                if is_valid_move(i, j, 1):
                    return False
                # 检查白棋是否可以落子
                if is_valid_move(i, j, 2):
                    return False

    return True

# 计算胜负（中国围棋协会规则第9条 - 数子法）
def calculate_winner():
    """使用数子法计算胜负（中国围棋协会标准）"""
    # 统计双方棋子数
    black_stones = sum(board[i][j] == 1 for i in range(19) for j in range(19))
    white_stones = sum(board[i][j] == 2 for i in range(19) for j in range(19))

    # 统计双方围住的目数
    black_territory = count_territory(1)
    white_territory = count_territory(2)

    # 计算双方总得点数
    black_total = black_stones + black_territory
    white_total = white_stones + white_territory + komi  # 白棋加上贴目

    # 判断胜负
    if black_total > 180.5:
        return {"winner": "black", "black_total": black_total, "white_total": white_total, "margin": black_total - 180.5}
    elif white_total > 180.5:
        return {"winner": "white", "black_total": black_total, "white_total": white_total, "margin": white_total - 180.5}
    else:
        return {"winner": "tie", "black_total": black_total, "white_total": white_total, "margin": 0}

# 检查是否是打劫
def is_ko():
    """检查当前局面是否是打劫"""
    global previous_board
    if previous_board:
        return board == previous_board
    return False

# 初始化KataGo进程
def init_katago():
    global katago_process
    try:
        # 根据难度级别设置不同的搜索参数
        search_params = ""
        if difficulty == "easy":
            search_params = "-override-config searchFactor=0.5"
        elif difficulty == "medium":
            search_params = "-override-config searchFactor=1.0"
        elif difficulty == "hard":
            search_params = "-override-config searchFactor=1.5"
        elif difficulty == "expert":
            search_params = "-override-config searchFactor=2.0"
        elif difficulty == "professional":
            search_params = "-override-config searchFactor=3.0"
        
        # 使用真实的KataGo进程
        katago_process = subprocess.Popen(
            ['katago.exe', 'gtp', '-model', 'default_model.bin.gz', '-config', 'default_gtp.cfg'] + (search_params.split() if search_params else []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # 等待KataGo启动
        time.sleep(2)
        print(f"KataGo初始化完成，难度级别: {difficulty}")
    except Exception as e:
        print(f"KataGo启动失败: {e}")
        # 使用模拟的KataGo进程
        print("使用模拟KataGo进程")

# 发送GTP命令到KataGo
def send_gtp_command(command):
    global katago_process
    if katago_process:
        try:
            katago_process.stdin.write(command + '\n')
            katago_process.stdin.flush()
            response = ''
            while True:
                line = katago_process.stdout.readline()
                if not line:
                    break
                response += line
                if line.strip() == '':
                    break
            return response
        except Exception as e:
            print(f"GTP命令发送失败: {e}")
            # 模拟KataGo的响应
            if command.startswith('genmove'):
                # 根据难度级别生成不同质量的落子
                import random
                # 简单模式：完全随机
                if difficulty == "easy":
                    while True:
                        x = random.randint(0, 18)
                        y = random.randint(0, 18)
                        if board[x][y] == 0:
                            return '= ' + chr(ord('A') + y) + str(19 - x)
                # 中等模式：优先选择中心和边缘
                elif difficulty == "medium":
                    best_moves = []
                    # 中心区域
                    for i in range(7, 12):
                        for j in range(7, 12):
                            if board[i][j] == 0:
                                best_moves.append((i, j))
                    # 边缘区域
                    for i in range(19):
                        for j in range(19):
                            if (i < 3 or i > 15 or j < 3 or j > 15) and board[i][j] == 0:
                                best_moves.append((i, j))
                    # 随机选择
                    if best_moves:
                        x, y = random.choice(best_moves)
                        return '= ' + chr(ord('A') + y) + str(19 - x)
                    # 如果没有合适的位置，随机选择
                    while True:
                        x = random.randint(0, 18)
                        y = random.randint(0, 18)
                        if board[x][y] == 0:
                            return '= ' + chr(ord('A') + y) + str(19 - x)
                # 困难及以上模式：模拟更好的落子
                else:
                    # 优先选择有己方棋子的附近
                    best_moves = []
                    for i in range(19):
                        for j in range(19):
                            if board[i][j] == 0:
                                # 检查周围是否有己方棋子
                                has_ally = False
                                for di in [-1, 0, 1]:
                                    for dj in [-1, 0, 1]:
                                        if 0 <= i + di < 19 and 0 <= j + dj < 19:
                                            if board[i + di][j + dj] == 2:  # 白棋
                                                has_ally = True
                                                break
                                    if has_ally:
                                        break
                                if has_ally:
                                    best_moves.append((i, j))
                    # 如果没有合适的位置，选择中心
                    if not best_moves:
                        for i in range(7, 12):
                            for j in range(7, 12):
                                if board[i][j] == 0:
                                    best_moves.append((i, j))
                    # 如果还是没有，随机选择
                    if best_moves:
                        x, y = random.choice(best_moves)
                        return '= ' + chr(ord('A') + y) + str(19 - x)
                    while True:
                        x = random.randint(0, 18)
                        y = random.randint(0, 18)
                        if board[x][y] == 0:
                            return '= ' + chr(ord('A') + y) + str(19 - x)
            return '= ok'
    else:
        # 模拟KataGo的响应
        if command.startswith('genmove'):
            # 根据难度级别生成不同质量的落子
            import random
            
            # 1. 检查是否有提子的机会（所有难度级别都优先考虑）
            for i in range(19):
                for j in range(19):
                    if board[i][j] == 0:
                        # 模拟落子
                        test_board = [row.copy() for row in board]
                        test_board[i][j] = 2  # 假设白棋落子
                        # 检查是否能提黑棋
                        if has_captures(test_board, 1):
                            return '= ' + chr(ord('A') + j) + str(19 - i)
            
            # 2. 检查是否需要防守（所有难度级别都优先考虑）
            for i in range(19):
                for j in range(19):
                    if board[i][j] == 0:
                        # 模拟黑棋落子
                        test_board = [row.copy() for row in board]
                        test_board[i][j] = 1  # 假设黑棋落子
                        # 检查是否会提白棋
                        if has_captures(test_board, 2):
                            return '= ' + chr(ord('A') + j) + str(19 - i)
            
            # 3. 根据难度级别选择策略
            if difficulty == "easy":
                # 简单模式：完全随机
                while True:
                    x = random.randint(0, 18)
                    y = random.randint(0, 18)
                    if board[x][y] == 0:
                        return '= ' + chr(ord('A') + y) + str(19 - x)
            
            elif difficulty == "medium":
                # 中等模式：优先选择星位和边角
                star_points = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]
                for i, j in star_points:
                    if board[i][j] == 0:
                        return '= ' + chr(ord('A') + j) + str(19 - i)
                # 边角区域
                for i in [2, 3, 4, 14, 15, 16]:
                    for j in [2, 3, 4, 14, 15, 16]:
                        if board[i][j] == 0:
                            return '= ' + chr(ord('A') + j) + str(19 - i)
                # 随机选择
                while True:
                    x = random.randint(0, 18)
                    y = random.randint(0, 18)
                    if board[x][y] == 0:
                        return '= ' + chr(ord('A') + y) + str(19 - x)
            
            elif difficulty == "hard":
                # 困难模式：优先选择中心和星位
                star_points = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]
                for i, j in star_points:
                    if board[i][j] == 0:
                        return '= ' + chr(ord('A') + j) + str(19 - i)
                # 中心区域
                for i in range(6, 13):
                    for j in range(6, 13):
                        if board[i][j] == 0:
                            return '= ' + chr(ord('A') + j) + str(19 - i)
                # 随机选择
                while True:
                    x = random.randint(0, 18)
                    y = random.randint(0, 18)
                    if board[x][y] == 0:
                        return '= ' + chr(ord('A') + y) + str(19 - x)
            
            elif difficulty == "expert":
                # 专家模式：优先选择靠近己方棋子的位置
                for i in range(19):
                    for j in range(19):
                        if board[i][j] == 2:  # 己方棋子（白棋）
                            # 检查周围的空位
                            directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                            for dx, dy in directions:
                                ni, nj = i + dx, j + dy
                                if 0 <= ni < 19 and 0 <= nj < 19 and board[ni][nj] == 0:
                                    return '= ' + chr(ord('A') + nj) + str(19 - ni)
                # 中心区域
                for i in range(6, 13):
                    for j in range(6, 13):
                        if board[i][j] == 0:
                            return '= ' + chr(ord('A') + j) + str(19 - i)
                # 随机选择
                while True:
                    x = random.randint(0, 18)
                    y = random.randint(0, 18)
                    if board[x][y] == 0:
                        return '= ' + chr(ord('A') + y) + str(19 - x)
            
            elif difficulty == "professional":
                # 专业模式：综合考虑各种因素
                # 优先选择攻击位置（靠近对方棋子）
                for i in range(19):
                    for j in range(19):
                        if board[i][j] == 1:  # 对方棋子（黑棋）
                            # 检查周围的空位
                            directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                            for dx, dy in directions:
                                ni, nj = i + dx, j + dy
                                if 0 <= ni < 19 and 0 <= nj < 19 and board[ni][nj] == 0:
                                    return '= ' + chr(ord('A') + nj) + str(19 - ni)
                # 寻找己方棋子周围的空位
                for i in range(19):
                    for j in range(19):
                        if board[i][j] == 2:  # 己方棋子（白棋）
                            # 检查周围的空位
                            directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                            for dx, dy in directions:
                                ni, nj = i + dx, j + dy
                                if 0 <= ni < 19 and 0 <= nj < 19 and board[ni][nj] == 0:
                                    return '= ' + chr(ord('A') + nj) + str(19 - ni)
                # 中心区域
                for i in range(6, 13):
                    for j in range(6, 13):
                        if board[i][j] == 0:
                            return '= ' + chr(ord('A') + j) + str(19 - i)
                # 随机选择
                while True:
                    x = random.randint(0, 18)
                    y = random.randint(0, 18)
                    if board[x][y] == 0:
                        return '= ' + chr(ord('A') + y) + str(19 - x)
            
            # 默认模式：随机选择
            while True:
                x = random.randint(0, 18)
                y = random.randint(0, 18)
                if board[x][y] == 0:
                    return '= ' + chr(ord('A') + y) + str(19 - x)
        return '= ok'

# 坐标转换：棋盘坐标转GTP坐标
def board_to_gtp(x, y):
    gtp_x = chr(ord('A') + y)
    gtp_y = str(19 - x)
    return gtp_x + gtp_y

# 坐标转换：GTP坐标转棋盘坐标
def gtp_to_board(gtp_coord):
    if len(gtp_coord) < 2:
        return None, None
    gtp_x = gtp_coord[0]
    gtp_y = gtp_coord[1:]
    try:
        y = ord(gtp_x.upper()) - ord('A')
        x = 19 - int(gtp_y)
        if x < 0 or x >= 19 or y < 0 or y >= 19:
            return None, None
        return x, y
    except:
        return None, None

# 自定义请求处理器
class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # 提供index.html
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('templates/index.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def do_POST(self):
        # 声明全局变量
        global board, current_player
        
        if self.path == '/make_move':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            x = data['x']
            y = data['y']
            
            # 使用围棋规则检查落子是否合法
            if make_move(x, y, current_player):
                # 如果当前是人类玩家（黑棋），则让KataGo（白棋）落子
                if current_player == 1:
                    # 发送落子命令到KataGo
                    gtp_coord = board_to_gtp(x, y)
                    send_gtp_command(f'play B {gtp_coord}')
                    
                    # 让KataGo生成下一步
                    response = send_gtp_command('genmove W')
                    print(f"KataGo response: {response}")
                    
                    # 解析KataGo的落子位置
                    if response.startswith('= '):
                        katago_move = response[2:].strip()
                        kx, ky = gtp_to_board(katago_move)
                        if kx is not None and ky is not None:
                            # 使用围棋规则执行KataGo的落子
                            make_move(kx, ky, 2)
                
                # 保持当前玩家为黑棋，因为AI落子后应该由人类继续落子
                # 只有当人类玩家选择让AI先手时，才需要切换
                # 这里我们默认人类执黑，所以始终保持current_player为1
                current_player = 1
                
                # 返回响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True, 
                    'board': board, 
                    'current_player': current_player
                }).encode())
            else:
                # 返回错误响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'message': '该位置落子不合法'
                }).encode())
        elif self.path == '/reset':
            board = [[0 for _ in range(19)] for _ in range(19)]
            current_player = 1  # 确保重置后始终是人类执黑
            # 重置打劫状态
            global previous_board
            previous_board = None
            # 重置游戏结束状态
            global game_over
            game_over = False
            # 重置KataGo
            send_gtp_command('clear_board')

            # 返回响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True, 
                'board': board, 
                'current_player': 1  # 始终返回黑棋
            }).encode())
        elif self.path == '/check_game_over':
            # 检查游戏是否结束
            if not game_over:
                game_over = is_game_over()

            result = {
                'game_over': game_over,
                'winner': None,
                'black_total': 0,
                'white_total': 0,
                'margin': 0
            }

            if game_over:
                score = calculate_winner()
                result['winner'] = score['winner']
                result['black_total'] = score['black_total']
                result['white_total'] = score['white_total']
                result['margin'] = score['margin']

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path == '/score':
            # 计算当前局势（数子法）
            score = calculate_winner()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(score).encode())
        elif self.path == '/set_difficulty':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            new_difficulty = data['difficulty']
            
            # 更新难度级别
            global difficulty
            difficulty = new_difficulty
            
            # 重启KataGo以应用新的难度设置
            global katago_process
            if katago_process:
                try:
                    katago_process.terminate()
                    katago_process.wait(timeout=5)
                except:
                    pass
            init_katago()
            
            # 返回响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

if __name__ == '__main__':
    # 初始化KataGo
    init_katago()
    
    # 启动服务器
    PORT = 8000
    with socketserver.TCPServer(('', PORT), MyHandler) as httpd:
        print(f"服务器启动在 http://localhost:{PORT}")
        print("请在浏览器中打开上述地址开始对弈")
        httpd.serve_forever()
