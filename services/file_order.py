import re

def numeric_file_key(name: str):
    nums=re.findall(r'\d+',name)
    return (int(nums[-1]) if nums else 10**9,name.lower())
