"""
接口性能分析
"""
import os

folder = os.path.join(os.path.dirname(__file__), 'output')

filename = sorted(os.listdir(folder)).pop()

# filename = '1705722518-GET-api.test.user-info-253ms.prof'

os.system(f'snakeviz {os.path.join(folder, filename)}')