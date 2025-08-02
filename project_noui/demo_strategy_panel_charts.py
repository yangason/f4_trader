#!/usr/bin/env python3
"""
策略面板Balance和Drawdown曲线功能演示
"""

import requests
import json
import webbrowser
import os

def demo_strategy_panel_charts():
    """演示策略面板图表功能"""
    
    base_url = "http://localhost:8800"
    
    print("🎯 策略面板Balance和Drawdown曲线功能演示")
    print("=" * 60)
    
    try:
        # 1. 检查API服务器状态
        print("1. 检查API服务器状态...")
        response = requests.get(f"{base_url}/api/projects", timeout=5)
        if response.status_code == 200:
            print("✅ API服务器运行正常")
        else:
            print("❌ API服务器响应异常:", response.status_code)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("💡 请先启动API服务器: python3 api_server.py")
        return False
    except Exception as e:
        print("❌ 连接错误:", e)
        return False
    
    # 2. 检查项目数据
    print("\n2. 检查可用的项目和数据...")
    try:
        # 检查项目
        response = requests.get(f"{base_url}/api/projects")
        projects_data = response.json()
        
        if 'projects' in projects_data and projects_data['projects']:
            projects = projects_data['projects']
            print(f"✅ 找到项目: {', '.join(projects)}")
            
            # 检查第一个项目的数据
            project_name = projects[0]
            response = requests.get(f"{base_url}/api/project/{project_name}/data")
            
            if response.status_code == 200:
                data = response.json()
                if 'strategy_data' in data:
                    strategy_data = data['strategy_data']
                    
                    balance_count = len(strategy_data.get('balance', []))
                    drawdown_count = len(strategy_data.get('drawdown', []))
                    trades_count = len(strategy_data.get('trades', []))
                    
                    print(f"📊 项目 {project_name} 数据:")
                    print(f"   - Balance数据: {balance_count} 个数据点")
                    print(f"   - Drawdown数据: {drawdown_count} 个数据点")
                    print(f"   - 交易数据: {trades_count} 笔交易")
                    
                    if balance_count > 0 and drawdown_count > 0:
                        print("✅ 数据完整，可以显示图表")
                    else:
                        print("⚠️  数据不完整，图表可能无法显示")
                else:
                    print("❌ 没有策略数据")
            else:
                print(f"❌ 获取项目数据失败: {response.status_code}")
        
        # 检查简单测试数据
        response = requests.get(f"{base_url}/api/strategy_data?symbol=simple_test")
        if response.status_code == 200:
            data = response.json()
            strategy_data = data.get('strategy_data', {})
            
            if strategy_data.get('balance') and strategy_data.get('drawdown'):
                print("✅ 简单测试数据也可用 (simple_test)")
            
    except Exception as e:
        print("❌ 检查数据失败:", e)
        return False
    
    # 3. 功能演示说明
    print("\n3. 策略面板图表功能说明...")
    print("📋 已实现的功能:")
    print("   ✅ 策略面板扩展布局 (400px宽度，600px最大高度)")
    print("   ✅ Balance曲线图表 (绿色线条，150px高度)")
    print("   ✅ Drawdown曲线图表 (红色线条，150px高度)")
    print("   ✅ 响应式设计 (窗口大小调整时图表自动适配)")
    print("   ✅ 错误处理 (图表创建失败时的错误提示)")
    print("   ✅ 数据验证 (检查LightweightCharts库和DOM元素)")
    
    print("\n📊 图表特性:")
    print("   - 使用TradingView Lightweight Charts V5")
    print("   - 支持缩放、平移、十字线显示")
    print("   - 深色主题适配")
    print("   - 时间轴同步显示")
    
    print("\n🎯 使用步骤:")
    print("   1. 打开 chart_enhanced.html")
    print("   2. 选择标的 (monthly_min_market_value 或 simple_test)")
    print("   3. 点击'加载策略数据'按钮")
    print("   4. 点击'策略面板'按钮")
    print("   5. 查看Balance和Drawdown曲线图表")
    
    # 4. 尝试打开浏览器
    print("\n4. 准备打开演示页面...")
    html_path = os.path.join(os.getcwd(), 'chart_enhanced.html')
    
    if os.path.exists(html_path):
        print(f"✅ 找到HTML文件: {html_path}")
        
        try:
            # 尝试打开浏览器
            webbrowser.open(f'file://{html_path}')
            print("🌐 浏览器已打开，请按照使用步骤操作")
        except Exception as e:
            print(f"⚠️  无法自动打开浏览器: {e}")
            print(f"💡 请手动打开: file://{html_path}")
    else:
        print("❌ 未找到HTML文件")
    
    print("\n✅ 演示准备完成！")
    print("\n🔧 故障排除:")
    print("   - 如果图表不显示，请检查浏览器控制台错误")
    print("   - 确保LightweightCharts库正确加载")
    print("   - 检查策略面板中的DOM元素是否存在")
    print("   - 验证数据格式是否正确")
    
    return True

if __name__ == "__main__":
    demo_strategy_panel_charts()