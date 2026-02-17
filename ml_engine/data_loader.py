import pandas as pd
import numpy as np
import glob
import os
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split

class DataLoader:
    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.scaler = MinMaxScaler()
        self.label_encoder = LabelEncoder()
        
    def load_data(self, sample_size=None):
        """
        Loads CICIDS2017 data from CSV files in the data_path.
        If sample_size is provided, it loads a random sample of the data.
        """
        all_files = glob.glob(os.path.join(self.data_path, "*.csv"))
        if not all_files:
            raise FileNotFoundError(f"No CSV files found in {self.data_path}. Please download the CICIDS2017 dataset and place it there.")
        
        df_list = []
        for filename in all_files:
            print(f"Loading {filename}...")
            df = pd.read_csv(filename, index_col=None, header=0)
            df_list.append(df)
            
        df = pd.concat(df_list, axis=0, ignore_index=True)
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        if sample_size:
            if len(df) < sample_size:
                print(f"Dataset size {len(df)} is smaller than requested sample size {sample_size}. Using full dataset.")
            else:
                df = df.sample(n=sample_size, random_state=42)
            
        return df

    def preprocess(self, df):
        """
        Preprocesses the dataframe:
        - Handles NaNs and Infinity
        - Encodes labels
        - Normalizes features
        """
        print("Preprocessing data...")
        
        # Replace Infinity with NaN and drop NaNs
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        # Separate features and target
        # 'Label' is the target column in CICIDS2017
        if 'Label' not in df.columns:
             raise ValueError("Label column not found in dataset")
             
        y = df['Label']
        X = df.drop(['Label'], axis=1)
        
        # Identify non-numeric columns (if any, besides Label which is already separated)
        # In CICIDS2017, some implementations might have other categorical columns like IP/Port if not removed.
        # For this implementation, we assume standard feature set.
        # We will drop columns that are object type but not the label if any remain
        X = X.select_dtypes(include=[np.number])
        
        # Binary Classification: Benign vs Attack
        # If label contains 'Benign', it's 0, else 1
        y_binary = y.apply(lambda x: 0 if 'Benign' in str(x) else 1)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y_binary

    def get_data_split(self, test_size=0.2, val_size=0.1):
        """
        Loads, preprocesses, and splits data into Train, Validation, and Test sets.
        """
        df = self.load_data(sample_size=100000) # Use sample for dev
        X, y = self.preprocess(df)
        
        # First split: Train + Val vs Test
        X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
        
        # Second split: Train vs Val
        # Adjust val_size relative to the remaining data
        relative_val_size = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=relative_val_size, random_state=42, stratify=y_train_val)
        
        print(f"Train shape: {X_train.shape}, Val shape: {X_val.shape}, Test shape: {X_test.shape}")
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)

if __name__ == "__main__":
    # Test the loader
    try:
        loader = DataLoader(data_path="c:/Users/akhil/Downloads/Minor_Project/ml_engine/data") # Adjust path for local testing
        loader.get_data_split()
    except Exception as e:
        print(e)
