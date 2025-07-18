import pandas as pd
import os
from datetime import datetime

import mysql.connector

def create_connection():
    """创建MySQL连接"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456',
            database='ASTOCK'  # 请替换为实际数据库名
        )
        return connection
    except mysql.connector.Error as e:
        print(f"连接MySQL失败: {e}")
        return None

def import_csv_to_mysql(csv_file_path, connection):
    """导入单个CSV文件到MySQL"""
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file_path, encoding='utf-8', dtype={'股票代码': str})

        
        # 数据清洗和转换
        df['datetime'] = pd.to_datetime(df['日期'])
        df['symbol'] = df['股票代码']
        df['exchange'] = 'SSE' if str(df['股票代码'].iloc[0]).startswith('6') else 'SZSE'
        df['interval'] = 'daily'
        df['volume'] = df['成交量']
        df['turnover'] = df['成交额']
        df['open_interest'] = 0  # CSV中没有此字段，设为0
        df['open_price'] = df['开盘']
        df['high_price'] = df['最高']
        df['low_price'] = df['最低']
        df['close_price'] = df['收盘']
        
        # 选择需要的列
        columns_to_insert = ['symbol', 'exchange', 'datetime', 'interval', 
                           'volume', 'turnover', 'open_interest', 'open_price', 
                           'high_price', 'low_price', 'close_price']
        df_clean = df[columns_to_insert]
        
        # 插入数据到MySQL
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO daily (symbol, exchange, datetime, `interval`, volume, 
                                   turnover, open_interest, open_price, high_price, 
                                   low_price, close_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for index, row in df_clean.iterrows():
            cursor.execute(insert_query, tuple(row))
        
        connection.commit()
        cursor.close()
        print(f"成功导入文件: {csv_file_path}")
        
    except Exception as e:
        print(f"导入文件失败 {csv_file_path}: {e}")

def main():
    """主函数"""
    # 连接数据库
    connection = create_connection()
    if not connection:
        return
    
    # daily_hfq目录路径
    csv_directory = "daily"
    
    # 检查目录是否存在
    if not os.path.exists(csv_directory):
        print(f"目录 {csv_directory} 不存在")
        return
    
    # 获取所有CSV文件
    csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]
    
    if not csv_files:
        print("没有找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    # 逐个导入CSV文件
    cnt = 0
    for csv_file in csv_files:
        csv_path = os.path.join(csv_directory, csv_file)
        import_csv_to_mysql(csv_path, connection)
        cnt += 1        
                
        # 其余代码保持不变...
        print(f"已导入 {cnt}/{len(csv_files)} 个文件")

    # 关闭连接
    connection.close()
    print("所有文件导入完成")

if __name__ == "__main__":
    main()