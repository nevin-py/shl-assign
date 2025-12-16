"""
Evaluation Module for SHL Assessment Recommendation System
Implements Mean Recall@K metric
"""

import pandas as pd
import json
from typing import List, Dict
import os


class EvaluationMetrics:
    def __init__(self):
        pass
    
    def recall_at_k(self, true_urls: List[str], predicted_urls: List[str], k: int = 10) -> float:
        """
        Calculate Recall@K for a single query
        
        Recall@K = (Number of relevant assessments in top K) / (Total relevant assessments)
        
        Args:
            true_urls: List of ground truth assessment URLs
            predicted_urls: List of predicted assessment URLs
            k: Number of top predictions to consider
        
        Returns:
            Recall@K score (between 0 and 1)
        """
        if not true_urls:
            return 0.0
        
        # Take only top K predictions
        predicted_top_k = predicted_urls[:k]
        
        # Normalize URLs for comparison (remove trailing slashes, etc.)
        true_urls_normalized = {self._normalize_url(url) for url in true_urls}
        predicted_urls_normalized = {self._normalize_url(url) for url in predicted_top_k}
        
        # Count matches
        matches = len(true_urls_normalized.intersection(predicted_urls_normalized))
        
        # Calculate recall
        recall = matches / len(true_urls)
        
        return recall
    
    def mean_recall_at_k(self, evaluation_data: List[Dict], k: int = 10) -> float:
        """
        Calculate Mean Recall@K across all queries
        
        Mean Recall@K = (1/N) × Σ(Recall@K_i) for i=1 to N
        
        Args:
            evaluation_data: List of dicts with 'query', 'true_urls', 'predicted_urls'
            k: Number of top predictions to consider
        
        Returns:
            Mean Recall@K score (between 0 and 1)
        """
        if not evaluation_data:
            return 0.0
        
        recall_scores = []
        
        for item in evaluation_data:
            true_urls = item.get('true_urls', [])
            predicted_urls = item.get('predicted_urls', [])
            
            recall = self.recall_at_k(true_urls, predicted_urls, k)
            recall_scores.append(recall)
        
        mean_recall = sum(recall_scores) / len(recall_scores)
        
        return mean_recall
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        # Remove trailing slash
        url = url.rstrip('/')
        # Convert to lowercase
        url = url.lower()
        # Remove http/https
        url = url.replace('https://', '').replace('http://', '')
        return url
    
    def evaluate_from_csv(self, predictions_csv: str, ground_truth_csv: str, k: int = 10) -> Dict:
        """
        Evaluate predictions from CSV files
        
        Args:
            predictions_csv: Path to predictions CSV (columns: query, Assessment_url)
            ground_truth_csv: Path to ground truth CSV (columns: query, Assessment_url)
            k: Number of top predictions to consider
        
        Returns:
            Dictionary with evaluation results
        """
        # Load predictions
        pred_df = pd.read_csv(predictions_csv)
        truth_df = pd.read_csv(ground_truth_csv)
        
        # Group by query
        pred_grouped = pred_df.groupby('query')['Assessment_url'].apply(list).to_dict()
        truth_grouped = truth_df.groupby('query')['Assessment_url'].apply(list).to_dict()
        
        # Prepare evaluation data
        evaluation_data = []
        for query in truth_grouped.keys():
            evaluation_data.append({
                'query': query,
                'true_urls': truth_grouped[query],
                'predicted_urls': pred_grouped.get(query, [])
            })
        
        # Calculate metrics
        mean_recall = self.mean_recall_at_k(evaluation_data, k)
        
        # Calculate per-query metrics
        per_query_results = []
        for item in evaluation_data:
            recall = self.recall_at_k(item['true_urls'], item['predicted_urls'], k)
            per_query_results.append({
                'query': item['query'],
                'recall@10': recall,
                'num_true': len(item['true_urls']),
                'num_predicted': len(item['predicted_urls'])
            })
        
        results = {
            'mean_recall@10': mean_recall,
            'num_queries': len(evaluation_data),
            'per_query_results': per_query_results
        }
        
        return results
    
    def print_evaluation_report(self, results: Dict):
        """Print a formatted evaluation report"""
        print("="*80)
        print("EVALUATION REPORT")
        print("="*80)
        print(f"\nMean Recall@10: {results['mean_recall@10']:.4f}")
        print(f"Number of Queries: {results['num_queries']}")
        print("\n" + "="*80)
        print("PER-QUERY RESULTS")
        print("="*80)
        
        for i, item in enumerate(results['per_query_results'], 1):
            print(f"\n{i}. Query: {item['query'][:80]}...")
            print(f"   Recall@10: {item['recall@10']:.4f}")
            print(f"   True Assessments: {item['num_true']}")
            print(f"   Predicted: {item['num_predicted']}")


def main():
    """Example usage"""
    evaluator = EvaluationMetrics()
    
    # Example evaluation data
    evaluation_data = [
        {
            'query': 'Java developer with collaboration skills',
            'true_urls': [
                'https://www.shl.com/solutions/products/assessments/java-test/',
                'https://www.shl.com/solutions/products/assessments/teamwork-test/',
                'https://www.shl.com/solutions/products/assessments/communication-test/'
            ],
            'predicted_urls': [
                'https://www.shl.com/solutions/products/assessments/java-test/',
                'https://www.shl.com/solutions/products/assessments/programming-test/',
                'https://www.shl.com/solutions/products/assessments/teamwork-test/',
                'https://www.shl.com/solutions/products/assessments/leadership-test/'
            ]
        }
    ]
    
    # Calculate Mean Recall@10
    mean_recall = evaluator.mean_recall_at_k(evaluation_data, k=10)
    print(f"Mean Recall@10: {mean_recall:.4f}")
    
    # Example per-query recall
    for item in evaluation_data:
        recall = evaluator.recall_at_k(item['true_urls'], item['predicted_urls'], k=10)
        print(f"\nQuery: {item['query']}")
        print(f"Recall@10: {recall:.4f}")


if __name__ == "__main__":
    main()
