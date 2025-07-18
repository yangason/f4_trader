import pandas as pd
import os
import mysql.connector

def create_connection():
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

def import_xlsx_to_mysql(xlsx_file_path, connection):
    """导入单个xlsx文件到MySQL"""
    try:
        # 读取xlsx文件
        df = pd.read_excel(xlsx_file_path, dtype={'股票代码': str})

        # 数据清洗和转换
        df.rename(columns={
            '股票代码': 'symbol',
            '股票名称': 'name',
            '市场': 'market',
            '更新时间': 'update_time',
            '总股本': 'total_shares',
            '净利润率(非金融类指标)': 'net_profit_margin',
            '五、净利润': 'net_profit'
        }, inplace=True)
        df = df.filter(items=['symbol', 'name', 'market', 'update_time', 'total_shares', 'net_profit_margin', 'net_profit'])

        # 插入数据到MySQL
        cursor = connection.cursor()
        insert_query = """
        INSERT IGNORE INTO finance (symbol, name, market, update_time, total_shares, net_profit_margin, net_profit)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        for index, row in df.iterrows():
            cursor.execute(insert_query, tuple(row))
        
        connection.commit()
        cursor.close()
        print(f"成功导入文件: {xlsx_file_path}")
        
    except Exception as e:
        print(f"导入文件失败 {xlsx_file_path}: {e}")

def main():
    """主函数"""
    # 连接数据库
    connection = create_connection()
    if not connection:
        return
    
    # xlsx文件目录路径
    xlsx_directory = "data"
    
    # 检查目录是否存在
    if not os.path.exists(xlsx_directory):
        print(f"目录 {xlsx_directory} 不存在")
        return
    
    # 获取所有xlsx文件
    xlsx_files = [f for f in os.listdir(xlsx_directory) if f.endswith('.xlsx')]
    
    if not xlsx_files:
        print("没有找到xlsx文件")
        return
    
    print(f"找到 {len(xlsx_files)} 个xlsx文件")
    
    # 逐个导入xlsx文件
    cnt = 0
    for xlsx_file in xlsx_files:
        xlsx_path = os.path.join(xlsx_directory, xlsx_file)
        import_xlsx_to_mysql(xlsx_path, connection)
        cnt += 1        
                
        print(f"已导入 {cnt}/{len(xlsx_files)} 个文件")

    # 关闭连接
    connection.close()
    print("所有文件导入完成")

if __name__ == "__main__":
    main()