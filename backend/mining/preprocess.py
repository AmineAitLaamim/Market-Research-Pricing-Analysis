import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any, TYPE_CHECKING
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

if TYPE_CHECKING:
    from apps.search.models import RawPrice


def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Builds the Scikit-Learn ColumnTransformer for numeric and categorical fields.
    """
    numeric_features = ['price_mad', 'seller_rating']
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
        ('scaler', StandardScaler())
    ])
    
    categorical_features = ['platform', 'condition']
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop'  # Drop the 'id' column or any other unlisted columns
    )
    
    return preprocessor


def preprocess(raw_prices: List['RawPrice']) -> Tuple[np.ndarray, pd.DataFrame, List[Dict[str, Any]]]:
    """
    Cleans raw price items, standardizes currency to MAD, removes duplicates/nulls,
    and applies the Scikit-Learn preprocessing pipeline.
    
    Returns:
        X_scaled: Numeric np.ndarray (scaled prices and ratings).
        X_encoded: Boolean pd.DataFrame (one-hot encoded platforms and conditions).
        clean_items: The list of cleaned dictionaries for downstream reference.
    """
    if not raw_prices:
        return np.array([]), pd.DataFrame(), []

    # 1. Convert to MAD and structure data
    items: List[Dict[str, Any]] = []
    seen_urls = set()
    
    for rp in raw_prices:
        # Drop duplicates by URL
        if rp.url in seen_urls:
            continue
            
        try:
            # Convert to float to handle Decimal types or strings safely
            price_val = float(rp.price)
        except (TypeError, ValueError):
            continue
            
        price_mad = price_val * float(rp.exchange_rate)
        
        # Remove null or zero prices
        if not price_mad or price_mad <= 0:
            continue
            
        seen_urls.add(rp.url)
        items.append({
            'id': rp.id,
            'price_mad': price_mad,
            'seller_rating': float(rp.seller_rating) if rp.seller_rating is not None else np.nan,
            'platform': rp.platform,
            'condition': rp.condition if rp.condition else np.nan
        })

    if not items:
        return np.array([]), pd.DataFrame(), []

    # 2. Build DataFrame
    df = pd.DataFrame(items)
    
    # 3. Fit-Transform Pipeline
    pipeline = build_preprocessing_pipeline()
    transformed_data = pipeline.fit_transform(df)
    
    # The output of ColumnTransformer is a single numpy array concatenating the transformers in order.
    # We specified: ('num', num_trans, num_cols) then ('cat', cat_trans, cat_cols).
    # The first 2 columns belong to the numeric transformer ('price_mad', 'seller_rating').
    # The rest belong to the categorical transformer (OneHotEncoder).
    
    # Get feature names for the categorical part from the OneHotEncoder
    try:
        # sklearn > 1.0 supports get_feature_names_out on ColumnTransformer
        cat_feature_names = pipeline.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(['platform', 'condition'])
    except AttributeError:
        # Fallback for older sklearn
        cat_feature_names = pipeline.named_transformers_['cat'].named_steps['onehot'].get_feature_names(['platform', 'condition'])

    # Slice the array
    num_cols_count = 2
    X_scaled = transformed_data[:, :num_cols_count]
    X_encoded_arr = transformed_data[:, num_cols_count:]
    
    # Convert categorical part to a boolean DataFrame
    # OneHotEncoder with sparse_output=False returns float64 by default
    X_encoded = pd.DataFrame(X_encoded_arr, columns=cat_feature_names, index=df.index).astype(bool)

    # Note: returning clean_items list so algorithms can tie results back to DB IDs
    return X_scaled, X_encoded, items
