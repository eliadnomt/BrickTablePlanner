from . import Catalog


def get_category(file_name):
    for part in Catalog:
        if part.file_name == file_name:
            return part.category
    raise ValueError(f"Unknown part detected in catalog lookup: {file_name}")


def get_metadata(file_name):
    for part in Catalog:
        if part.file_name == file_name:
            return part
    raise ValueError(f"Unknown part detected in catalog metadata lookup: {file_name}")


def get_size(file_name):
    part = get_metadata(file_name)
    if part.width is None or part.length is None:
        return None
    return part.width, part.length


def build_index_for_category(category):
    index = {}
    
    for part in Catalog:
        if part.category != category:
            continue
        
        if part.width is None or part.length is None:
            continue
        
        if part.modified:
            continue
        
        index.setdefault(part.width, {})[part.length] = part.file_name
    
    return index
