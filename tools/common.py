import pandas as pd
import numpy as np


def sum_specified_keep_others(dataframes, sum_columns):
    """
    对指定列中index相同的行求和，index去重保留，其他列删除
    
    Parameters:
    -----------
    dataframes : list of DataFrame
        要合并的DataFrame列表
    sum_columns : list
        需要求和的字段列表
        
    Returns:
    --------
    pd.DataFrame
        只包含指定求和列的DataFrame，相同index的行已求和
    """
    if not dataframes:
        return pd.DataFrame()
    
    # 合并所有 DataFrame
    combined = pd.concat(dataframes, sort=False)
    
    # 只保留需要求和的列
    sum_cols = [col for col in sum_columns if col in combined.columns]
    
    if not sum_cols:
        # 如果没有指定的求和列，返回空DataFrame
        return pd.DataFrame()
    
    # 只选择需要求和的列
    combined_sum_only = combined[sum_cols]
    
    # 对相同index的行进行求和，index自动去重
    result = combined_sum_only.groupby(level=0).sum()
    
    return result