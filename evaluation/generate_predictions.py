"""
Generate predictions on test data and create submission CSV
"""

import pandas as pd
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.recommender import RecommendationEngine


def generate_predictions(test_csv_path: str, output_csv_path: str, chroma_dir: str = "./chroma_db"):
    """
    Generate predictions for test queries and save to CSV
    
    Args:
        test_csv_path: Path to test CSV with 'query' column
        output_csv_path: Path to save predictions CSV
        chroma_dir: Path to ChromaDB directory
    """
    # Load test data
    print(f"Loading test data from {test_csv_path}")
    test_df = pd.read_csv(test_csv_path)
    
    if 'query' not in test_df.columns:
        raise ValueError("Test CSV must have a 'query' column")
    
    print(f"Found {len(test_df)} test queries")
    
    # Initialize recommendation engine
    print("Initializing recommendation engine...")
    engine = RecommendationEngine(chroma_dir=chroma_dir)
    
    # Generate predictions
    results = []
    
    for idx, row in test_df.iterrows():
        query = row['query']
        print(f"\n[{idx+1}/{len(test_df)}] Processing: {query[:80]}...")
        
        try:
            # Get recommendations (5-10 results)
            recommendations = engine.get_recommendations(query, min_results=5, max_results=10)
            
            # Add to results
            for rec in recommendations:
                results.append({
                    'query': query,
                    'Assessment_url': rec['url']
                })
            
            print(f"  → Generated {len(recommendations)} recommendations")
            
        except Exception as e:
            print(f"  → Error: {e}")
            continue
    
    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Save to CSV
    results_df.to_csv(output_csv_path, index=False)
    print(f"\n✅ Saved {len(results_df)} predictions to {output_csv_path}")
    print(f"   Unique queries: {results_df['query'].nunique()}")
    print(f"   Avg recommendations per query: {len(results_df) / results_df['query'].nunique():.1f}")
    
    return results_df


def main():
    """Generate predictions on test set"""
    # Paths
    test_csv = "data/test_data.csv"
    output_csv = "data/test_predictions.csv"
    chroma_dir = "./chroma_db"
    
    # Check if test data exists
    if not os.path.exists(test_csv):
        print(f"❌ Test data not found at {test_csv}")
        print("Please create test_data.csv with a 'query' column")
        return
    
    # Generate predictions
    generate_predictions(test_csv, output_csv, chroma_dir)


if __name__ == "__main__":
    main()
