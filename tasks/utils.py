from datetime import datetime
import logging

def get_pipeline_execution_id():
    """
    Construct pipeline run id

    Returns:
        str: Pipeline execution id (16 digits), e.g. 1631530000000000 to the microseconds
        
    """
    return int(datetime.now().timestamp().__str__().replace('.',''))


def get_max_dynamics_datetime(
    data, 
    current_watermark: str, 
    column: str ='modifiedon'
    ):
    """
    Calculate the maximum modifiedon date in the data

    Args:
        data (_type_): json array of records from response object.
        current_watermark (str): string representation of dynamics datetime value
        column (str, optional): column to determine a max value for. Defaults to 'modifiedon'.
        logger (logging.Logger, optional): _description_. Defaults to None.

    Returns:
        max of the column within the json array object
    """
    modifiedon_dates = [datetime.strptime(record[column], '%Y-%m-%dT%H:%M:%S%z') for record in data['value'] if column in record]
    if not modifiedon_dates:
        max_modifiedon = current_watermark
    else:
        max_modifiedon = max(modifiedon_dates).strftime('%Y-%m-%dT%H:%M:%S%z').replace('+0000', 'Z')
        if max_modifiedon is None:
            max_modifiedon = current_watermark
    return max_modifiedon

def get_most_recent_datetime(datetime_value_1, datetime_value_2):
    """
    Get the most recent datetime value

    Args:
        datetime_value_1 (str): datetime value
        datetime_value_2 (str): datetime value

    Returns:
        str: most recent datetime value
    """
    date_1 = datetime.strptime(datetime_value_1, '%Y-%m-%dT%H:%M:%S%z')
    date_2 = datetime.strptime(datetime_value_2, '%Y-%m-%dT%H:%M:%S%z')
    return datetime_value_1 if date_1 > date_2 else datetime_value_2
