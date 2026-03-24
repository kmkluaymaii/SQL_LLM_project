import pandas as pd

# Function to read the csv file
def load_data(file_path):
    data = pd.read_csv(file_path)
    return data

# Create a schema based on the data types of the columns
def create_schema(data):
    schema = {}
    for col in data.columns:
        data_type = str(data[col].dtype)
        if 'int' in data_type:
            schema[col] = 'INTEGER'
        elif 'float' in data_type:
            schema[col] = 'REAL'
        else:
            schema[col] = 'TEXT' 
    return schema

# Insert the data into the database
def insert_data(data):
    ...