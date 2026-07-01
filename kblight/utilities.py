"""
Basic utilities scripts
"""
import json, csv
from json import JSONEncoder
import pandas as pd
import datetime
from time import gmtime, strftime, time
import math
import os
import requests
import yaml

# UUID libraries
import uuid
import shortuuid


def truncated_uuid(length=12):
    """
    Returns a truncated short UUID4 with specific length.

    Args:
            length(int): Number of characters of ID. Default is 12.

    Returns:
            truncated_id(str): Truncated short UUID string.

    """
    u = uuid.uuid4()
    s = shortuuid.encode(u)

    truncated_id = s[:length]

    return truncated_id


def yaml2dict(yml_path, encoding="utf-8"):
    with open(yml_path, "r", encoding=encoding) as f:
        entity_data = yaml.safe_load(f)
    return entity_data


def dict2yaml(d, yml_path, encoding="utf-8", allow_unicode=True, sort_keys=False):
    with open(yml_path, "w", encoding=encoding) as f:
        yaml.dump(d, f, allow_unicode=allow_unicode, sort_keys=sort_keys)


def csv2dict(csv_filename, encoding="utf-8-sig", orient="records", na_values=""):
    df = pd.read_csv(csv_filename, encoding=encoding)
    df = df.fillna(na_values)
    d = df.to_dict(orient=orient)
    return d


def dict2csv(d, csv_filename, separator: str = ",", index: bool = False):
    df = pd.DataFrame(data=d)
    df.to_csv(csv_filename, sep=separator, index=index)


def json2dict(json_filename):  # imports a JSON file as dictionary
    with open(json_filename, "r") as f:
        json_file = json.load(f)
        return json_file


def dict2json(d, json_filename, ensure_ascii=False, indent=2):
    # export a dictionary to JSON file
    class DateTimeEncoder(JSONEncoder):
        # Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()

    with open(json_filename, "w") as json_file:
        json.dump(
            d, json_file, indent=indent, ensure_ascii=ensure_ascii, cls=DateTimeEncoder
        )


def get_current_date():
    return strftime("%Y-%m-%d", gmtime())


def get_latest_file(basepath):  # returns latest file path in a directory
    files = os.listdir(basepath)
    paths = [os.path.join(basepath, basename) for basename in files]
    return max(paths, key=os.path.getctime)
