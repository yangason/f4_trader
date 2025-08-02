from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import sys

# 添加项目根目录到路径
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)

# 简化导入，避免akshare依赖问题
import mysql.connector
from datetime import datetime, timedelta
from vnpy.trader.constant import Interval

# 导入项目基础类
try:
    from project_base import PROJECT_REGISTER, get_project, list_projects, register_project
except ImportError as e:
    print(f"⚠️  导入project_base模块失败: {e}")
    # 如果导入失败，创建空的注册表
    PROJECT_REGISTER = {}
    def get_project(name):
        return PROJECT_REGISTER.get(name)
    def list_projects():
        return list(PROJECT_REGISTER.keys())
    def register_project(project):
        PROJECT_REGISTER[project.name] = project

# 导入技术指标工具
try:
    from indicator_tools import calculate_indicators_from_bars
    print("✅ 成功导入技术指标工具")
except ImportError as e:
    print(f"⚠️  导入技术指标工具失败: {e}")
    calculate_indicators_from_bars = None

# 尝试导入策略项目（可能因为依赖问题失败）
MonthlyMinMarketValueProject = None
try:
    from monthly_min_market_value import MonthlyMinMarketValueProject
    print("✅ 成功导入MonthlyMinMarketValueProject")
except ImportError as e:
    print(f"⚠️  导入MonthlyMinMarketValueProject失败: {e}")
    print("   这通常是因为缺少依赖包或导入路径问题")
    print("   项目注册功能将不可用，但其他功能正常")

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局数据对象，用于存储策略数据
class Data:
    def __init__(self):
        self.tech_data_dict = {}
        self.trade_data_dict = {}
        self.start_date = None
        self.end_date = None

data = Data()

def auto_register_projects():
    """自动注册所有可用的项目"""
    try:
        print("📋 开始自动注册项目...")
        
        # 注册每月市值最低策略（如果可用）
        if MonthlyMinMarketValueProject is not None:
            monthly_strategy = MonthlyMinMarketValueProject(
                name="monthly_min_market_value",
                initial_capital=1000000,
                top_n=10
            )
            register_project(monthly_strategy)
            print(f"✅ 已注册项目: {monthly_strategy.name}")
        else:
            print("⚠️  MonthlyMinMarketValueProject不可用，跳过注册")
            print("   请检查依赖包或导入路径")
            return
        
        # 可以在这里添加更多项目的自动注册
        # 例如：
        # other_strategy = OtherStrategyProject(name="other_strategy")
        # register_project(other_strategy)
        # print(f"✅ 已注册项目: {other_strategy.name}")
        
        print(f"📊 项目注册完成，共 {len(PROJECT_REGISTER)} 个项目")
        print(f"   已注册项目: {list(PROJECT_REGISTER.keys())}")
        
    except Exception as e:
        print(f"❌ 自动注册项目失败: {e}")
        print("   这可能是由于依赖包缺失或配置问题")

def select_target_bars_direct(symbol, start_date, end_date):
    """直接查询数据库获取K线数据"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        query = """
        SELECT datetime, open_price, high_price, low_price, close_price, volume, turnover
        FROM daily 
        WHERE symbol = %s AND datetime BETWEEN %s AND %s 
        ORDER BY datetime
        """
        cursor.execute(query, (symbol, start_date, end_date))
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        if not results:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(results, columns=['datetime', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'turnover'])
        df.set_index('datetime', inplace=True)
        
        return df
    except Exception as e:
        print(f"查询数据失败: {e}")
        return None

def create_mysql_connection():
    """创建MySQL连接"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456',
            database='ASTOCK'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"连接MySQL失败: {e}")
        return None

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """获取所有可用的股票列表"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'error': '数据库连接失败'}), 500
        
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM daily ORDER BY symbol")
        stocks = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return jsonify({'stocks': stocks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bars', methods=['GET'])
def get_bars():
    """获取K线数据"""
    try:
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not symbol or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 转换日期格式
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        connection = create_mysql_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        query = """
        SELECT datetime, open_price, high_price, low_price, close_price, volume, turnover
        FROM daily 
        WHERE symbol = %s AND datetime >= %s AND datetime < %s 
        ORDER BY datetime
        """
        cursor.execute(query, (symbol, start_dt, end_dt))
        
        
        bars_data = []
        for row in cursor.fetchall():
            bars_data.append({
                'time': int(row[0].timestamp()),
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': float(row[5])
        })

        cursor.close()
        connection.close()        
        return jsonify({'bars': bars_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/volume', methods=['GET'])
def get_volume():
    """获取成交量数据"""
    try:
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not symbol or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 转换日期格式
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 查询成交量数据
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'error': '数据库连接失败'}), 500
        
        cursor = connection.cursor()
        query = """
        SELECT datetime, volume, turnover 
        FROM daily 
        WHERE symbol = %s AND datetime >= %s AND datetime < %s 
        ORDER BY datetime
        """
        cursor.execute(query, (symbol, start_dt, end_dt))
        
        volume_data = []
        for row in cursor.fetchall():
            volume_data.append({
                'time': int(row[0].timestamp()),
                'volume': float(row[1]),
                'turnover': float(row[2]) if row[2] else 0
            })
        
        cursor.close()
        connection.close()
        return jsonify({'volume': volume_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """获取交易数据"""
    try:
        symbol = request.args.get('symbol')
        
        if not symbol:
            return jsonify({'error': '缺少股票代码参数'}), 400
        
        # 从全局数据对象获取交易数据
        trade_df = data.trade_data_dict.get(symbol, pd.DataFrame())
        
        if trade_df.empty:
            return jsonify({'trades': []})
        
        trades_data = []
        for index, row in trade_df.iterrows():
            trades_data.append({
                'time': int(index.timestamp()),
                'price': float(row['price']),
                'volume': float(row['volume']),
                'direction': str(row['direction']),
                'offset': str(row['offset'])
            })
        
        return jsonify({'trades': trades_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy_data', methods=['GET'])
def get_strategy_data():
    """获取策略数据"""
    try:
        symbol = request.args.get('symbol')
        
        if not symbol:
            return jsonify({'error': '缺少股票代码参数'}), 400
        
        # 从全局数据对象获取策略数据
        tech_data = data.tech_data_dict.get(symbol, {})
        
        # 检查是否有直接的balance和drawdown数据
        if 'balance' in tech_data and 'drawdown' in tech_data:
            strategy_data = {
                'daily_pnl': tech_data.get('daily_df', []),
                'balance': tech_data.get('balance', []),
                'drawdown': tech_data.get('drawdown', [])
            }
            return jsonify({'strategy_data': strategy_data})
        
        # 传统的DataFrame处理方式
        daily_df = tech_data.get('daily_df', pd.DataFrame())
        
        if isinstance(daily_df, list):
            # 如果是列表格式，直接返回
            strategy_data = {
                'daily_pnl': daily_df,
                'balance': tech_data.get('balance', []),
                'drawdown': tech_data.get('drawdown', [])
            }
            return jsonify({'strategy_data': strategy_data})
        
        if daily_df.empty:
            return jsonify({'strategy_data': {}})
        
        strategy_data = {
            'daily_pnl': [],
            'drawdown': [],
            'cumulative_pnl': []
        }
        
        for index, row in daily_df.iterrows():
            strategy_data['daily_pnl'].append({
                'time': int(index.timestamp()),
                'value': float(row['net_pnl']) if 'net_pnl' in row else 0
            })
            
            strategy_data['drawdown'].append({
                'time': int(index.timestamp()),
                'value': float(row['drawdown']) if 'drawdown' in row else 0
            })
            
            if 'cumulative_pnl' in row:
                strategy_data['cumulative_pnl'].append({
                    'time': int(index.timestamp()),
                    'value': float(row['cumulative_pnl'])
                })
        
        return jsonify({'strategy_data': strategy_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_strategy_data', methods=['POST'])
def update_strategy_data():
    """更新策略数据"""
    try:
        request_data = request.get_json()
        symbol = request_data.get('symbol')
        tech_data = request_data.get('tech_data', {})
        trade_data = request_data.get('trade_data', [])
        
        if symbol:
            # 更新技术数据
            if tech_data:
                data.tech_data_dict[symbol] = tech_data
            
            # 更新交易数据
            if trade_data:
                trade_df = pd.DataFrame(trade_data)
                if not trade_df.empty:
                    trade_df['datetime'] = pd.to_datetime(trade_df['time'], unit='s')
                    trade_df.set_index('datetime', inplace=True)
                    data.trade_data_dict[symbol] = trade_df
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/indicators', methods=['GET'])
def get_indicators():
    """获取技术指标数据"""
    try:
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        indicator = request.args.get('indicator', 'ma5')  # ma5, ma10, ma20, ma60, rsi, macd等
        
        print(f"🔍 技术指标请求: symbol={symbol}, start_date={start_date}, end_date={end_date}, indicator={indicator}")
        
        if not symbol or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 转换日期格式
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        init_dt = start_dt - timedelta(days=200)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        print(f"📅 日期转换: start_dt={start_dt}, end_dt={end_dt}")
        
        # 获取K线数据
        bars_df = select_target_bars_direct(symbol, init_dt, end_dt)
        
        if bars_df is None or bars_df.empty:
            print(f"❌ 未找到K线数据: symbol={symbol}")
            return jsonify({'error': '未找到数据'}), 404
        
        print(f"✅ 获取到K线数据: {len(bars_df)} 条")
        
        # 检查技术指标工具是否可用
        if calculate_indicators_from_bars is None:
            print("❌ 技术指标工具不可用")
            return jsonify({'error': '技术指标工具不可用'}), 500
        
        # 转换DataFrame为bars_data格式
        bars_data = []
        for index, row in bars_df.iterrows():
            try:
                bars_data.append({
                    'time': int(index.timestamp()),
                    'open': float(row['open_price']),
                    'high': float(row['high_price']),
                    'low': float(row['low_price']),
                    'close': float(row['close_price']),
                    'volume': int(row['volume'])
                })
            except Exception as e:
                print(f"❌ 转换数据行失败: {e}, row={row}")
                continue
        
        print(f"✅ 转换数据完成: {len(bars_data)} 条")
        
        if len(bars_data) == 0:
            return jsonify({'error': '数据转换失败'}), 500
        
        # 计算所有技术指标
        try:
            all_indicators = calculate_indicators_from_bars(bars_data)
            clean_all_indicators = {}
            end_timestamp = end_dt.timestamp()
            
            for key in all_indicators.keys():
                if key == 'macd':
                    # MACD是一个包含多个子系列的字典
                    macd_data = all_indicators[key]
                    if isinstance(macd_data, dict):
                        clean_all_indicators[key] = {
                            'macd': [item for item in macd_data.get('macd', []) if item['time'] < end_timestamp],
                            'signal': [item for item in macd_data.get('signal', []) if item['time'] < end_timestamp],
                            'histogram': [item for item in macd_data.get('histogram', []) if item['time'] < end_timestamp]
                        }
                    else:
                        # 如果不是字典格式，按普通数组处理
                        clean_all_indicators[key] = [daily_value for daily_value in macd_data if daily_value['time'] < end_timestamp and daily_value['time'] >= start_dt.timestamp()]
                else:
                    # 其他指标是简单的数组格式
                    clean_all_indicators[key] = [daily_value for daily_value in all_indicators[key] if daily_value['time'] < end_timestamp and daily_value['time'] >= start_dt.timestamp()]

            print(f"✅ 计算指标完成: {list(clean_all_indicators.keys())}")
            
            # 打印过滤后的数据统计
            for key, data in clean_all_indicators.items():
                if key == 'macd' and isinstance(data, dict):
                    print(f"   {key}: MACD={len(data.get('macd', []))}, Signal={len(data.get('signal', []))}, Histogram={len(data.get('histogram', []))}")
                else:
                    print(f"   {key}: {len(data)} 条数据")
                    
        except Exception as e:
            print(f"❌ 计算指标失败: {e}")
            return jsonify({'error': f'计算指标失败: {str(e)}'}), 500
        
        # 根据请求的指标类型返回数据
        if indicator in clean_all_indicators:
            indicator_data = clean_all_indicators[indicator]
            print(f"✅ 返回指标数据: {indicator}, 数据条数: {len(indicator_data)}")
            return jsonify({'indicator': indicator_data})
        elif indicator == 'macd':
            # MACD返回多个系列
            if 'macd' in clean_all_indicators:
                macd_data = clean_all_indicators['macd']
                print(f"✅ 返回MACD数据: MACD={len(macd_data['macd'])}, Signal={len(macd_data['signal'])}, Histogram={len(macd_data['histogram'])}")
                return jsonify({'indicator': macd_data})
            else:
                return jsonify({'error': 'MACD数据不可用'}), 500
        else:
            print(f"❌ 不支持的指标类型: {indicator}")
            return jsonify({'error': f'不支持的指标类型: {indicator}'}), 400
        
    except Exception as e:
        import traceback
        print(f"❌ 技术指标API异常: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'message': 'API服务器运行正常'})

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有注册的项目"""
    try:
        projects = list_projects()
        return jsonify({'projects': projects})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<project_name>', methods=['GET'])
def get_project_data(project_name):
    """获取指定项目的数据"""
    try:
        project = get_project(project_name)
        if not project:
            return jsonify({'error': f'项目 {project_name} 不存在'}), 404
        
        summary = project.get_summary()
        return jsonify({'project': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<project_name>/data', methods=['GET'])
def get_project_strategy_data(project_name):
    """获取指定项目的策略数据"""
    try:
        project = get_project(project_name)
        if not project:
            return jsonify({'error': f'项目 {project_name} 不存在'}), 404
        
        # 返回策略数据
        strategy_data = {
            'daily_pnl': project.daily_pnl,
            'drawdown': project.drawdown,
            'balance': project.balance,
            'trades': project.trades
        }
        
        return jsonify({'strategy_data': strategy_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run_project', methods=['POST'])
def run_project():
    """运行指定项目"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        print(f"🚀 开始运行项目 {project_name}")
        print(f"📅 时间范围: {start_date} 到 {end_date}")
        
        if not project_name or not start_date or not end_date:
            return jsonify({'error': '缺少必要参数'}), 400
        
        project = get_project(project_name)
        if not project:
            return jsonify({'error': f'项目 {project_name} 不存在'}), 404
        
        print(f"✅ 找到项目: {project_name}")
        
        # 运行项目
        project.run(start_date, end_date)
        
        print(f"🎉 项目 {project_name} 运行完成")
        return jsonify({'success': True, 'message': f'项目 {project_name} 运行完成'})
    except Exception as e:
        print(f"❌ 运行项目失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/register_project', methods=['POST'])
def register_project_api():
    """手动注册项目"""
    try:
        data = request.get_json()
        project_type = data.get('project_type')
        project_name = data.get('project_name')
        
        if not project_type or not project_name:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 根据项目类型创建项目实例
        if project_type == 'monthly_min_market_value':
            if MonthlyMinMarketValueProject is None:
                return jsonify({'error': 'MonthlyMinMarketValueProject不可用，请检查依赖包'}), 500
            project = MonthlyMinMarketValueProject(
                name=project_name,
                initial_capital=data.get('initial_capital', 1000000),
                top_n=data.get('top_n', 10)
            )
            register_project(project)
            return jsonify({
                'success': True, 
                'message': f'项目 {project_name} 注册成功',
                'project': project.get_summary()
            })
        else:
            return jsonify({'error': f'不支持的项目类型: {project_type}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reload_projects', methods=['POST'])
def reload_projects():
    """重新加载所有项目"""
    try:
        # 清空现有注册表
        PROJECT_REGISTER.clear()
        
        # 重新注册项目
        auto_register_projects()
        
        return jsonify({
            'success': True,
            'message': '项目重新加载成功',
            'projects': list_projects()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 启动简化版API服务器 (端口8800)...")
    
    # 自动注册项目
    auto_register_projects()
    
    print("📊 健康检查: http://localhost:8800/api/health")
    print("📈 股票列表: http://localhost:8800/api/stocks")
    print("📋 项目列表: http://localhost:8800/api/projects")
    print("🚀 项目运行: POST http://localhost:8800/api/run_project")
    
    app.run(debug=True, host='0.0.0.0', port=8800) 