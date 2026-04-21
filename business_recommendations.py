"""
🎯 BUSINESS RECOMMENDATIONS & INTERPRETATION SYSTEM
====================================================
File này chứa các functions để:
1. Phân tích feature importance
2. Tạo recommendations cho từng khách hàng
3. Export kết quả với business insights
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import permutation_importance

# =============================================================================
# 📊 PHẦN 1: FEATURE IMPORTANCE ANALYSIS
# =============================================================================

def analyze_feature_importance(model, X_test, y_test, feature_names, top_n=20):
    """
    Phân tích feature importance của model
    
    Parameters:
    -----------
    model : trained model
    X_test : test features (đã được transform nếu có pipeline)
    y_test : test labels
    feature_names : list of feature names
    top_n : number of top features to display
    
    Returns:
    --------
    DataFrame with feature importance
    """
    print("="*80)
    print("🔍 FEATURE IMPORTANCE ANALYSIS")
    print("="*80)
    
    # Nếu model là Pipeline, cần lấy ra preprocessor transform
    if hasattr(model, 'named_steps'):
        # Transform X_test qua preprocessing steps
        clf = model.named_steps['clf']
        
        # Với tree-based models
        if hasattr(clf, 'feature_importances_'):
            # Get feature names sau khi onehot encoding
            preprocess_step = model.named_steps.get('preprocess')
            if preprocess_step:
                feature_names_transformed = preprocess_step.get_feature_names_out()
            else:
                feature_names_transformed = feature_names
                
            importances = clf.feature_importances_
            
            imp_df = pd.DataFrame({
                'feature': feature_names_transformed,
                'importance': importances
            }).sort_values('importance', ascending=False).head(top_n)
            
            print(f"\n📈 Top {top_n} Most Important Features:\n")
            print(imp_df.to_string(index=False))
            
            # Visualize
            plt.figure(figsize=(10, 8))
            plt.barh(imp_df['feature'], imp_df['importance'])
            plt.xlabel('Importance')
            plt.title(f'Top {top_n} Feature Importance')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.show()
            
            return imp_df
    
    # Fallback: Permutation importance
    print("\nUsing Permutation Importance (this may take a while)...")
    r = permutation_importance(model, X_test, y_test, n_repeats=10, 
                               random_state=42, scoring='roc_auc', n_jobs=-1)
    
    imp_df = pd.DataFrame({
        'feature': feature_names,
        'importance': r.importances_mean,
        'std': r.importances_std
    }).sort_values('importance', ascending=False).head(top_n)
    
    print(f"\n📈 Top {top_n} Most Important Features:\n")
    print(imp_df.to_string(index=False))
    
    # Visualize
    plt.figure(figsize=(10, 8))
    plt.barh(imp_df['feature'], imp_df['importance'])
    plt.xlabel('Importance')
    plt.title(f'Top {top_n} Feature Importance (Permutation)')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()
    
    return imp_df


# =============================================================================
# 🎯 PHẦN 2: CLUSTER NAMING & INTERPRETATION
# =============================================================================

def assign_cluster_names(df_cluster, cluster_col='cluster'):
    """
    Tự động gán tên có ý nghĩa cho các clusters dựa trên profile
    
    Parameters:
    -----------
    df_cluster : DataFrame chứa thông tin cluster và features
    cluster_col : tên cột cluster
    
    Returns:
    --------
    Dictionary mapping cluster_id -> cluster_name
    """
    print("="*80)
    print("🏷️  AUTO-NAMING CLUSTERS BASED ON PROFILE")
    print("="*80)
    
    cluster_profiles = {}
    
    for cluster_id in sorted(df_cluster[cluster_col].unique()):
        cluster_data = df_cluster[df_cluster[cluster_col] == cluster_id]
        
        profile = {
            'n_customers': len(cluster_data),
            'avg_tx_cnt': cluster_data['tx_cnt'].mean(),
            'avg_transfer_cnt': cluster_data['transfer_cnt'].mean(),
            'avg_loan': cluster_data['total_loan_est'].mean(),
            'avg_td_balance': cluster_data['avg_td_balance'].mean(),
            'avg_ca_balance': cluster_data['avg_ca_balance'].mean(),
            'avg_activity': cluster_data['activity_cnt'].mean(),
            'creditcard_rate': cluster_data.get('has_creditcard', pd.Series([0])).mean()
        }
        
        cluster_profiles[cluster_id] = profile
    
    # Phân loại dựa trên profile
    cluster_names = {}
    
    # Tìm cluster có loan cao nhất
    max_loan_cluster = max(cluster_profiles.items(), 
                          key=lambda x: x[1]['avg_loan'])[0]
    
    # Tìm cluster có transfer cao nhất
    max_transfer_cluster = max(cluster_profiles.items(), 
                               key=lambda x: x[1]['avg_transfer_cnt'])[0]
    
    # Tìm cluster có td_balance cao nhất
    max_td_cluster = max(cluster_profiles.items(), 
                        key=lambda x: x[1]['avg_td_balance'])[0]
    
    # Tìm cluster có activity thấp nhất
    min_activity_cluster = min(cluster_profiles.items(), 
                              key=lambda x: x[1]['avg_activity'])[0]
    
    for cluster_id in cluster_profiles.keys():
        if cluster_id == max_loan_cluster:
            cluster_names[cluster_id] = "Nhóm Thường Xuyên Vay"
        elif cluster_id == max_transfer_cluster:
            cluster_names[cluster_id] = "Nhóm Hay Chuyển Khoản"
        elif cluster_id == max_td_cluster:
            cluster_names[cluster_id] = "Nhóm Gửi Tiền Tiết Kiệm"
        elif cluster_id == min_activity_cluster:
            cluster_names[cluster_id] = "Nhóm Ít Sử Dụng Dịch Vụ"
        else:
            cluster_names[cluster_id] = f"Nhóm Đa Dạng {cluster_id}"
    
    print("\n📋 CLUSTER NAMING RESULTS:\n")
    for cluster_id, name in cluster_names.items():
        profile = cluster_profiles[cluster_id]
        print(f"Cluster {cluster_id}: {name}")
        print(f"  - Số khách: {profile['n_customers']:,}")
        print(f"  - Tỷ lệ có thẻ tín dụng: {profile['creditcard_rate']*100:.1f}%")
        print(f"  - Đặc điểm nổi bật:")
        print(f"    • Giao dịch TB: {profile['avg_tx_cnt']:.0f} lần")
        print(f"    • Khoản vay TB: {profile['avg_loan']:,.0f} VNĐ")
        print(f"    • Tiết kiệm TB: {profile['avg_td_balance']:,.0f} VNĐ")
        print()
    
    return cluster_names, cluster_profiles


# =============================================================================
# 💡 PHẦN 3: RECOMMENDATION SYSTEM
# =============================================================================

def create_creditcard_recommendations(df_with_predictions, cluster_names):
    """
    Tạo recommendations cho từng khách hàng dựa trên cluster và probability
    
    Parameters:
    -----------
    df_with_predictions : DataFrame chứa cluster, probability, và features
    cluster_names : dict mapping cluster_id -> cluster_name
    
    Returns:
    --------
    DataFrame with recommendations
    """
    print("="*80)
    print("💡 CREDIT CARD RECOMMENDATION SYSTEM")
    print("="*80)
    
    def recommend_strategy(row):
        cluster_id = row['cluster']
        prob = row['creditcard_probability']
        cluster_name = cluster_names.get(cluster_id, f"Cluster {cluster_id}")
        
        # Logic recommendation
        if cluster_name == "Nhóm Thường Xuyên Vay":
            if prob > 0.7:
                return {
                    'priority': 'HIGH',
                    'strategy': 'Priority Target - Offer Premium Card',
                    'product': 'Premium Credit Card với hạn mức cao',
                    'channel': 'Direct Call + Email',
                    'message': 'Ưu đãi đặc biệt cho khách hàng VIP - Thẻ tín dụng với hạn mức lên đến 500M'
                }
            elif prob > 0.4:
                return {
                    'priority': 'MEDIUM',
                    'strategy': 'Potential Target - Offer Standard Card',
                    'product': 'Standard Credit Card',
                    'channel': 'Email + SMS',
                    'message': 'Mở thẻ tín dụng ngay - Nhận ưu đãi lãi suất 0% 90 ngày đầu'
                }
            else:
                return {
                    'priority': 'LOW',
                    'strategy': 'Nurture - Digital Promotions',
                    'product': 'Basic Credit Card hoặc Debit Card Upgrade',
                    'channel': 'In-app Notification',
                    'message': 'Khám phá ưu đãi thẻ tín dụng dành cho bạn'
                }
        
        elif cluster_name == "Nhóm Hay Chuyển Khoản":
            if prob > 0.6:
                return {
                    'priority': 'HIGH',
                    'strategy': 'Cashback Card for Active Users',
                    'product': 'Cashback Credit Card',
                    'channel': 'Direct Call + Email',
                    'message': 'Hoàn tiền lên đến 5% cho mọi giao dịch chuyển khoản và thanh toán'
                }
            elif prob > 0.3:
                return {
                    'priority': 'MEDIUM',
                    'strategy': 'Offer Rewards Card',
                    'product': 'Rewards Credit Card',
                    'channel': 'Email + In-app',
                    'message': 'Tích điểm thưởng cho mỗi giao dịch - Đổi quà hấp dẫn'
                }
            else:
                return {
                    'priority': 'LOW',
                    'strategy': 'Digital Banking Benefits',
                    'product': 'Enhanced Debit Services',
                    'channel': 'In-app Notification',
                    'message': 'Nâng cấp trải nghiệm banking với các ưu đãi độc quyền'
                }
        
        elif cluster_name == "Nhóm Gửi Tiền Tiết Kiệm":
            if prob > 0.5:
                return {
                    'priority': 'MEDIUM',
                    'strategy': 'Secure Spender Card',
                    'product': 'Low-interest Credit Card',
                    'channel': 'Email + Branch Visit',
                    'message': 'Thẻ tín dụng lãi suất thấp - An toàn cho chi tiêu thông minh'
                }
            else:
                return {
                    'priority': 'LOW',
                    'strategy': 'Focus on Deposit Products',
                    'product': 'Investment & Savings Products',
                    'channel': 'Email Newsletter',
                    'message': 'Khám phá các gói tiết kiệm lãi suất cao và sản phẩm đầu tư'
                }
        
        else:  # Nhóm Ít Sử Dụng Dịch Vụ
            if prob > 0.4:
                return {
                    'priority': 'MEDIUM',
                    'strategy': 'Re-engagement with Basic Card',
                    'product': 'Basic Credit Card',
                    'channel': 'SMS + Email',
                    'message': 'Quay lại với VIB - Nhận thẻ tín dụng miễn phí năm đầu'
                }
            else:
                return {
                    'priority': 'LOW',
                    'strategy': 'General Awareness Campaign',
                    'product': 'General Banking Services',
                    'channel': 'SMS',
                    'message': 'Cập nhật các ưu đãi mới nhất từ VIB'
                }
    
    # Apply recommendation logic
    recommendations = df_with_predictions.apply(recommend_strategy, axis=1)
    
    # Convert to DataFrame
    rec_df = pd.DataFrame(recommendations.tolist())
    
    # Combine with original data
    result = pd.concat([
        df_with_predictions[['CUSTOMER_NUMBER', 'cluster', 'creditcard_probability', 
                             'has_creditcard', 'age', 'tx_cnt', 'total_loan_est']],
        rec_df
    ], axis=1)
    
    # Add cluster name
    result['cluster_name'] = result['cluster'].map(cluster_names)
    
    # Statistics
    print("\n📊 RECOMMENDATION STATISTICS:\n")
    print(result['priority'].value_counts())
    print("\n" + "="*80)
    
    return result


# =============================================================================
# 📤 PHẦN 4: EXPORT RESULTS
# =============================================================================

def export_results(df_recommendations, output_file='credit_card_recommendations.xlsx'):
    """
    Export kết quả ra Excel với nhiều sheets
    
    Parameters:
    -----------
    df_recommendations : DataFrame chứa recommendations
    output_file : tên file output
    """
    print("="*80)
    print(f"📤 EXPORTING RESULTS TO {output_file}")
    print("="*80)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: All recommendations
        df_recommendations.to_excel(writer, sheet_name='All_Recommendations', index=False)
        
        # Sheet 2: High priority only
        high_priority = df_recommendations[df_recommendations['priority'] == 'HIGH']
        high_priority.to_excel(writer, sheet_name='High_Priority', index=False)
        
        # Sheet 3: By cluster
        for cluster_name in df_recommendations['cluster_name'].unique():
            cluster_data = df_recommendations[df_recommendations['cluster_name'] == cluster_name]
            safe_sheet_name = cluster_name[:31]  # Excel sheet name limit
            cluster_data.to_excel(writer, sheet_name=safe_sheet_name, index=False)
        
        # Sheet 4: Summary statistics
        summary = pd.DataFrame({
            'Cluster': df_recommendations.groupby('cluster_name').size(),
            'Avg Probability': df_recommendations.groupby('cluster_name')['creditcard_probability'].mean(),
            'High Priority Count': df_recommendations[df_recommendations['priority'] == 'HIGH'].groupby('cluster_name').size(),
            'Medium Priority Count': df_recommendations[df_recommendations['priority'] == 'MEDIUM'].groupby('cluster_name').size(),
            'Low Priority Count': df_recommendations[df_recommendations['priority'] == 'LOW'].groupby('cluster_name').size(),
        }).fillna(0)
        
        summary.to_excel(writer, sheet_name='Summary')
    
    print(f"✅ Exported successfully to {output_file}")
    print(f"   - All Recommendations: {len(df_recommendations):,} rows")
    print(f"   - High Priority: {len(high_priority):,} customers")
    print(f"   - Sheets: {len(df_recommendations['cluster_name'].unique()) + 3}")


# =============================================================================
# 🎯 PHẦN 5: MAIN WORKFLOW
# =============================================================================

def run_complete_analysis(df_cluster, best_model, X_test, y_test, feature_names):
    """
    Chạy toàn bộ workflow analysis và recommendations
    
    Parameters:
    -----------
    df_cluster : DataFrame với cluster assignments
    best_model : trained best model
    X_test : test features
    y_test : test labels
    feature_names : list of feature names
    
    Returns:
    --------
    df_recommendations : DataFrame with all recommendations
    """
    print("\n" + "🚀"*40)
    print("🎯 BẮT ĐẦU COMPLETE BUSINESS ANALYSIS WORKFLOW")
    print("🚀"*40 + "\n")
    
    # Step 1: Feature Importance
    print("\n📍 STEP 1: Feature Importance Analysis")
    feature_imp = analyze_feature_importance(best_model, X_test, y_test, feature_names)
    
    # Step 2: Cluster Naming
    print("\n📍 STEP 2: Cluster Naming & Interpretation")
    cluster_names, cluster_profiles = assign_cluster_names(df_cluster)
    
    # Step 3: Predictions on all data
    print("\n📍 STEP 3: Making Predictions on Full Dataset")
    # Cần prepare X_full từ df_cluster với features tương ứng
    X_full = df_cluster[feature_names].copy()
    X_full = X_full.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    predictions = best_model.predict_proba(X_full)[:, 1]
    df_cluster['creditcard_probability'] = predictions
    
    print(f"✅ Predicted for {len(df_cluster):,} customers")
    print(f"   Average probability: {predictions.mean():.4f}")
    
    # Step 4: Create Recommendations
    print("\n📍 STEP 4: Creating Personalized Recommendations")
    df_recommendations = create_creditcard_recommendations(df_cluster, cluster_names)
    
    # Step 5: Export Results
    print("\n📍 STEP 5: Exporting Results")
    export_results(df_recommendations)
    
    print("\n" + "✅"*40)
    print("🎉 HOÀN THÀNH WORKFLOW!")
    print("✅"*40 + "\n")
    
    return df_recommendations


# =============================================================================
# 📝 USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    print("""
    ===================================================================
    🎯 BUSINESS RECOMMENDATIONS & INTERPRETATION SYSTEM
    ===================================================================
    
    Để sử dụng file này, trong notebook của bạn, thêm cell:
    
    ```python
    # Import module
    from business_recommendations import run_complete_analysis
    
    # Chạy complete workflow
    df_recommendations = run_complete_analysis(
        df_cluster=df_cluster,           # DataFrame với cluster assignments
        best_model=model_D,               # Model tốt nhất (ví dụ: Gradient Boosting)
        X_test=X2_test,                   # Test features
        y_test=y2_test,                   # Test labels
        feature_names=base_features + ["cluster"]  # List feature names
    )
    
    # Xem top recommendations
    print(df_recommendations.head(20))
    ```
    
    Output:
    - Feature importance analysis với visualization
    - Cluster names với business interpretation
    - Personalized recommendations cho từng khách hàng
    - Excel file với multiple sheets
    """)
