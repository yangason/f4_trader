import pandas as pd
import numpy as np

def sum_specified_keep_others(dataframes, sum_columns, keep_strategy='first'):
    """
    对指定字段求和，其他字段保持不变
    
    Parameters:
    -----------
    dataframes : list of DataFrame
    sum_columns : list
        需要求和的字段列表
    keep_strategy : str
        其他字段的保持策略：'first', 'last', 'most_frequent'
    """
    if not dataframes:
        return pd.DataFrame()
    
    # 合并所有 DataFrame
    combined = pd.concat(dataframes, sort=False)
    
    # 分离需要求和的列和其他列
    sum_cols = [col for col in sum_columns if col in combined.columns]
    other_cols = [col for col in combined.columns if col not in sum_columns]
    
    result_parts = []
    
    # 1. 对指定字段求和
    if sum_cols:
        sum_result = combined[sum_cols].groupby(level=0).sum()
        result_parts.append(sum_result)
    
    # 2. 对其他字段按策略处理
    if other_cols:
        if keep_strategy == 'first':
            other_result = combined[other_cols].groupby(level=0).first()
        elif keep_strategy == 'last':
            other_result = combined[other_cols].groupby(level=0).last()
        elif keep_strategy == 'most_frequent':
            # 对每列取众数
            other_result = combined[other_cols].groupby(level=0).agg(
                lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
            )
        else:
            raise ValueError("keep_strategy 必须是 'first', 'last', 或 'most_frequent'")
        
        result_parts.append(other_result)
    
    # 合并结果
    if result_parts:
        result = pd.concat(result_parts, axis=1)
        # 保持原始列的顺序
        original_order = combined.columns.tolist()
        result = result[[col for col in original_order if col in result.columns]]
        return result
    else:
        return pd.DataFrame()