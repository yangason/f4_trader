#!/bin/bash

# 增强版多窗口行情系统 - 完整启动脚本

echo "🚀 启动增强版多窗口行情系统..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 项目根目录: $PROJECT_ROOT"
echo "📁 脚本目录: $SCRIPT_DIR"

# 检查Python依赖
echo "📦 检查Python依赖..."
python3 -c "import flask, flask_cors, mysql.connector, pandas, numpy, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少必要的Python依赖，正在安装..."
    echo "🚀 运行install.py安装依赖..."
    cd "$PROJECT_ROOT"
    python3 install.py -r
    cd "$SCRIPT_DIR"
    
    # 再次检查依赖
    echo "🔍 再次检查依赖..."
    python3 -c "import flask, flask_cors, mysql.connector, pandas, numpy, requests" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，请手动运行: python3 install.py -r"
        exit 1
    fi
    echo "✅ 依赖安装成功"
else
    echo "✅ Python依赖检查通过"
fi

# 检查MySQL连接
echo "🔍 检查MySQL连接..."
python3 -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='ASTOCK'
    )
    print('✅ MySQL连接成功')
    conn.close()
except Exception as e:
    print(f'❌ MySQL连接失败: {e}')
    exit(1)
"

# 检查API服务器是否已经在运行
echo "🔍 检查API服务器状态..."
if curl -s http://localhost:8800/api/health > /dev/null 2>&1; then
    echo "⚠️  API服务器已经在运行 (端口8800)"
    read -p "是否要停止现有服务器并重新启动? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 停止现有API服务器..."
        pkill -f "api_server.py" 2>/dev/null
        sleep 2
    else
        echo "✅ 使用现有API服务器"
    fi
fi

# 启动API服务器
echo "🌐 启动API服务器..."
python3 api_server.py &
API_PID=$!

# 等待API服务器启动
echo "⏳ 等待API服务器启动..."
for i in {1..15}; do
    if curl -s http://localhost:8800/api/health > /dev/null 2>&1; then
        echo "✅ API服务器启动成功"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ API服务器启动失败"
        kill $API_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# 检查项目自动注册
echo "📋 检查项目自动注册..."
sleep 2
PROJECTS_RESPONSE=$(curl -s http://localhost:8800/api/projects 2>/dev/null)
if echo "$PROJECTS_RESPONSE" | grep -q "monthly_min_market_value"; then
    echo "✅ 项目自动注册成功"
else
    echo "⚠️  项目自动注册可能失败，尝试手动重新加载..."
    curl -s -X POST http://localhost:8800/api/reload_projects > /dev/null 2>&1
    sleep 2
    PROJECTS_RESPONSE=$(curl -s http://localhost:8800/api/projects 2>/dev/null)
    if echo "$PROJECTS_RESPONSE" | grep -q "monthly_min_market_value"; then
        echo "✅ 项目重新加载成功"
    else
        echo "⚠️  项目注册失败，但系统仍可正常使用"
    fi
fi

# 启动HTML页面
echo "📊 启动HTML页面..."
if command -v open > /dev/null; then
    # macOS
    open chart_enhanced.html
elif command -v xdg-open > /dev/null; then
    # Linux
    xdg-open chart_enhanced.html
elif command -v start > /dev/null; then
    # Windows
    start chart_enhanced.html
else
    echo "请手动打开 chart_enhanced.html 文件"
fi

echo ""
echo "🎉 系统启动完成！"
echo "📊 HTML页面: chart_enhanced.html"
echo "🌐 API服务器: http://localhost:8800"
echo "📈 健康检查: http://localhost:8800/api/health"
echo "📋 股票列表: http://localhost:8800/api/stocks"
echo ""
echo "📋 使用说明:"
echo "1. 在浏览器中选择股票和日期范围"
echo "2. 点击'加载股票数据'查看K线图"
echo "3. 点击'项目列表'查看已注册的策略项目"
echo "4. 点击'运行项目'执行策略"
echo "5. 点击'加载策略数据'查看策略信息"
echo "6. 使用'策略面板'按钮查看详细策略数据"
echo ""
echo "按 Ctrl+C 停止服务器"

# 等待用户中断
trap "echo '🛑 正在停止服务器...'; kill $API_PID 2>/dev/null; echo '✅ 服务器已停止'; exit 0" INT
wait 