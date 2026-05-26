


"""
增强版缓存分区机器学习预测器
包含实时学习、特征重要性分析和置信度校准
"""

import numpy as np
import json
import pickle
import os
import time
import warnings
from typing import List, Dict, Any, Tuple, Optional, Union
from collections import deque, defaultdict
from dataclasses import dataclass, asdict, field
import threading


@dataclass
class CacheMetrics:
    """缓存指标数据点"""
    timestamp: float
    cache_size: int
    max_size: int
    current_partitions: int
    min_partitions: int
    max_partitions: int
    partition_sizes: List[int]
    hit_rate: float
    read_write_ratio: float
    total_lock_wait_time: float
    total_lock_wait_count: int
    rebalance_count: int
    actual_partitions_changed: Optional[int] = None  # 实际调整后的分区数
    actual_performance_change: Optional[float] = None  # 实际性能变化
    performance_score: float = 0.0


@dataclass
class FeatureImportance:
    """特征重要性分析结果"""
    feature_name: str
    importance_score: float
    rank: int
    description: str
    impact_direction: str  # 'positive', 'negative', 'mixed'


@dataclass
class CalibrationInfo:
    """置信度校准信息"""
    predicted_confidence: float
    calibrated_confidence: float
    calibration_factor: float
    reliability_score: float
    uncertainty_level: str  # 'low', 'medium', 'high'


@dataclass
class PartitionPrediction:
    """增强版分区预测结果"""
    optimal_partitions: int
    base_confidence: float
    calibrated_confidence: CalibrationInfo
    predicted_performance_gain: float
    uncertainty_range: Tuple[float, float]  # 性能增益的不确定性范围
    feature_importances: List[FeatureImportance]
    reason: str
    features: Dict[str, float]
    timestamp: float
    model_version: str = "v1.0"
    online_learning_update: bool = False  # 是否通过在线学习更新


class EnhancedCachePredictor:
    """
    增强版缓存分区预测器
    包含实时学习、特征重要性分析和置信度校准
    """
    
    def __init__(self, 
                 history_size: int = 5000,
                 model_path: str = None,
                 online_learning_rate: float = 0.01,
                 calibration_window: int = 100):
        """
        初始化增强版预测器
        
        Args:
            history_size: 历史数据最大存储量
            model_path: 模型保存路径
            online_learning_rate: 在线学习率
            calibration_window: 置信度校准窗口大小
        """
        self.history = deque(maxlen=history_size)
        self.predictions = deque(maxlen=200)
        self.actual_outcomes = deque(maxlen=100)  # 实际结果用于校准
        self.model_path = model_path or ".enhanced_cache_predictor.pkl"
        
        # 在线学习参数
        self.online_learning_rate = online_learning_rate
        self.online_learning_enabled = True
        self.last_online_update = 0
        self.online_update_interval = 60  # 每60秒在线更新一次
        
        # 置信度校准
        self.calibration_window = calibration_window
        self.calibration_data = deque(maxlen=calibration_window)
        self.confidence_calibration_model = None
        self.calibration_lock = threading.RLock()
        
        # 特征重要性跟踪
        self.feature_importance_history = deque(maxlen=100)
        self.feature_correlation_stats = defaultdict(lambda: {'sum': 0.0, 'count': 0, 'squares': 0.0})
        
        # 模型组件
        self.model = None
        self.feature_scaler = None
        self.feature_names = None
        self.model_version = "1.0.0"
        self.last_training_time = 0
        self.training_interval = 1800  # 每30分钟重新训练
        
        # 性能监控
        self.prediction_stats = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'high_confidence_correct': 0,
            'high_confidence_total': 0,
            'avg_absolute_error': 0.0,
            'calibration_error': 0.0,
        }
        
        # 初始化
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型"""
        try:
            # 尝试加载现有模型
            if self.load_model():
                print(f"[EnhancedCachePredictor] 加载模型 v{self.model_version}")
                return
            
            # 初始化新模型
            print("[EnhancedCachePredictor] 初始化新模型")
            self._create_initial_model()
            
        except Exception as e:
            print(f"[EnhancedCachePredictor] 初始化失败: {e}")
            self._create_fallback_model()
    
    def _create_initial_model(self):
        """创建初始模型"""
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.preprocessing import StandardScaler
            
            # 初始模型
            self.model = RandomForestRegressor(
                n_estimators=50,  # 初始较小，在线学习会增加
                max_depth=8,
                random_state=42,
                warm_start=True,  # 支持在线学习
                n_jobs=-1
            )
            
            self.feature_scaler = StandardScaler()
            self.model_version = "1.0.0-initial"
            
        except ImportError:
            self._create_fallback_model()
    
    def _create_fallback_model(self):
        """创建备用的启发式模型"""
        self.model = "heuristic"
        self.model_version = "1.0.0-heuristic"
        print("[EnhancedCachePredictor] 使用启发式模型")
    
    def extract_features(self, metrics: CacheMetrics) -> Tuple[Dict[str, float], List[str]]:
        """提取特征，返回特征字典和特征名列表"""
        partition_sizes = metrics.partition_sizes
        if not partition_sizes:
            partition_sizes = [0]
        
        # 计算基础统计
        avg_size = sum(partition_sizes) / len(partition_sizes)
        max_size = max(partition_sizes) if partition_sizes else 0
        min_size = min(partition_sizes) if partition_sizes else 0
        
        # 特征工程
        features = {
            # 基础特征
            'cache_size': float(metrics.cache_size),
            'load_ratio': metrics.cache_size / max(1, metrics.max_size),
            'current_partitions': float(metrics.current_partitions),
            'partition_range': max_size - min_size,
            
            # 性能特征
            'hit_rate': metrics.hit_rate,
            'hit_rate_squared': metrics.hit_rate ** 2,
            'imbalance_ratio': max_size / avg_size if avg_size > 0 else 1.0,
            'gini_imbalance': self._calculate_gini_coefficient(partition_sizes),
            'lock_intensity': (metrics.total_lock_wait_time / 
                             max(1, metrics.total_lock_wait_count)),
            'read_intensity': min(metrics.read_write_ratio, 10.0) / 10.0,
            
            # 派生特征
            'size_per_partition': float(metrics.cache_size) / max(1, metrics.current_partitions),
            'log_cache_size': np.log1p(float(metrics.cache_size)),
            'sqrt_partitions': np.sqrt(float(metrics.current_partitions)),
            'partitions_per_log_size': float(metrics.current_partitions) / np.log1p(max(1, metrics.cache_size)),
            
            # 时间序列特征
            'time_since_rebalance': min(metrics.rebalance_count, 100) / 100.0,
            'rebalance_frequency': metrics.rebalance_count / max(1, metrics.cache_size),
            
            # 高阶交互特征
            'size_imbalance_interaction': float(metrics.cache_size) * (max_size / avg_size if avg_size > 0 else 1.0),
            'lock_load_interaction': (metrics.total_lock_wait_time / max(1, metrics.total_lock_wait_count)) * 
                                   (metrics.cache_size / max(1, metrics.max_size)),
        }
        
        # 特征名列表
        feature_names = list(features.keys())
        
        return features, feature_names
    
    def _calculate_gini_coefficient(self, values: List[int]) -> float:
        """计算基尼系数，衡量不均衡程度"""
        if not values or len(values) < 2:
            return 0.0
        
        values = sorted(values)
        n = len(values)
        total = sum(values)
        
        if total == 0:
            return 0.0
        
        # 计算基尼系数
        cumulative = 0
        for i, value in enumerate(values, 1):
            cumulative += value * (2 * i - n - 1)
        
        gini = cumulative / (n * total)
        return abs(gini)
    
    def add_metrics_with_outcome(self, 
                                metrics: CacheMetrics,
                                outcome_metrics: Optional[CacheMetrics] = None):
        """添加指标和实际结果（用于在线学习）"""
        with self.calibration_lock:
            self.history.append(metrics)
            
            # 如有实际结果，用于在线学习
            if outcome_metrics is not None:
                self.actual_outcomes.append((metrics, outcome_metrics))
                
                # 立即进行在线学习更新
                if (self.online_learning_enabled and 
                    time.time() - self.last_online_update > self.online_update_interval):
                    self._online_learning_update()
    
    def _online_learning_update(self):
        """在线学习更新"""
        if self.model is None or self.model == "heuristic":
            return
        
        if len(self.actual_outcomes) < 10:
            return  # 数据不足
        
        try:
            from sklearn.ensemble import RandomForestRegressor
            
            if not isinstance(self.model, RandomForestRegressor):
                return
            
            # 准备在线学习数据
            X_online = []
            y_online = []
            
            for before_metrics, after_metrics in list(self.actual_outcomes)[-50:]:  # 最近50个
                # 计算实际性能变化
                before_score = self.calculate_performance_score(before_metrics)
                after_score = self.calculate_performance_score(after_metrics)
                actual_change = after_score - before_score
                
                # 提取特征
                features, _ = self.extract_features(before_metrics)
                X_online.append(list(features.values()))
                y_online.append(actual_change)
            
            if len(X_online) < 5:
                return
            
            X_online = np.array(X_online)
            y_online = np.array(y_online)
            
            # 标准化特征
            if self.feature_scaler is not None:
                X_scaled = self.feature_scaler.transform(X_online)
            else:
                X_scaled = X_online
            
            # 在线学习：部分拟合
            # 注意：随机森林在线学习有限，这里使用增量更新策略
            self.model.n_estimators += 5  # 增加5棵树
            self.model.fit(X_scaled, y_online)
            
            self.last_online_update = time.time()
            self.model_version = f"{self.model_version.split('-')[0]}-online"
            
            print(f"[EnhancedCachePredictor] 在线学习更新完成，增加5棵树，总{self.model.n_estimators}棵树")
            
            # 更新特征重要性
            self._update_feature_importance()
            
        except Exception as e:
            print(f"[EnhancedCachePredictor] 在线学习失败: {e}")
    
    def _update_feature_importance(self):
        """更新特征重要性分析"""
        if self.model is None or self.model == "heuristic":
            return
        
        try:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                
                # 与特征名关联
                if self.feature_names is not None and len(importances) == len(self.feature_names):
                    feature_importance_list = []
                    for i, (name, importance) in enumerate(zip(self.feature_names, importances)):
                        # 确定影响方向
                        direction = self._determine_feature_impact_direction(name, importance)
                        
                        feature_importance = FeatureImportance(
                            feature_name=name,
                            importance_score=importance,
                            rank=i+1,
                            description=self._get_feature_description(name),
                            impact_direction=direction
                        )
                        feature_importance_list.append(feature_importance)
                    
                    # 按重要性排序
                    feature_importance_list.sort(key=lambda x: x.importance_score, reverse=True)
                    self.feature_importance_history.append(feature_importance_list)
                    
        except Exception as e:
            print(f"[EnhancedCachePredictor] 特征重要性更新失败: {e}")
    
    def _determine_feature_impact_direction(self, feature_name: str, importance: float) -> str:
        """确定特征影响方向"""
        # 基于特征名和重要性符号的简单启发式
        positive_indicators = ['hit_rate', 'read_intensity', 'size_per_partition']
        negative_indicators = ['imbalance_ratio', 'lock_intensity', 'gini_imbalance']
        
        if any(indicator in feature_name for indicator in positive_indicators):
            return 'positive'
        elif any(indicator in feature_name for indicator in negative_indicators):
            return 'negative'
        else:
            return 'mixed'
    
    def _get_feature_description(self, feature_name: str) -> str:
        """获取特征描述"""
        descriptions = {
            'cache_size': '缓存总大小',
            'load_ratio': '缓存负载比例',
            'current_partitions': '当前分区数量',
            'hit_rate': '缓存命中率',
            'imbalance_ratio': '分区负载不均衡比例',
            'gini_imbalance': '基尼不均衡系数',
            'lock_intensity': '锁争用强度',
            'read_intensity': '读取操作强度',
            'size_per_partition': '每分区平均大小',
            'log_cache_size': '缓存大小的对数',
            'sqrt_partitions': '分区数量的平方根',
        }
        return descriptions.get(feature_name, feature_name)
    
    def calculate_performance_score(self, metrics: CacheMetrics) -> float:
        """计算综合性能评分"""
        partition_sizes = metrics.partition_sizes
        if not partition_sizes:
            return 0.5
        
        # 1. 命中率权重 (35%)
        hit_rate_score = metrics.hit_rate * 0.35
        
        # 2. 锁争用权重 (25%)
        avg_lock_wait = (metrics.total_lock_wait_time / 
                        max(1, metrics.total_lock_wait_count))
        lock_score = max(0, 1.0 - min(avg_lock_wait * 2000, 1.0)) * 0.25  # 更敏感
        
        # 3. 负载均衡权重 (25%)
        avg_size = sum(partition_sizes) / len(partition_sizes)
        if avg_size > 0:
            imbalance = max(partition_sizes) / avg_size
            balance_score = max(0, 2.5 - imbalance) * 0.25  # 更严格
        else:
            balance_score = 0.25
        
        # 4. 分区效率权重 (15%)
        ideal_partitions = int(np.sqrt(max(1, metrics.cache_size))) + 1
        partitions_diff = abs(metrics.current_partitions - ideal_partitions)
        efficiency_score = max(0, 1.0 - partitions_diff / 15.0) * 0.15
        
        total_score = hit_rate_score + lock_score + balance_score + efficiency_score
        return min(1.0, max(0.0, total_score))
    
    def predict_with_calibration(self, 
                                metrics: CacheMetrics,
                                min_partitions: int = 2,
                                max_partitions: int = 16) -> PartitionPrediction:
        """带置信度校准的预测"""
        
        # 1. 基础预测
        features, feature_names = self.extract_features(metrics)
        self.feature_names = feature_names  # 保存特征名用于重要性分析
        
        base_prediction = self._base_prediction(metrics, features, min_partitions, max_partitions)
        
        # 2. 特征重要性分析
        feature_importances = self._analyze_feature_importance(features)
        
        # 3. 置信度校准
        calibration_info = self._calibrate_confidence(base_prediction, features, metrics)
        
        # 4. 不确定性范围估计
        uncertainty_range = self._estimate_uncertainty_range(base_prediction, calibration_info)
        
        # 5. 生成解释
        reason = self._generate_enhanced_reason(
            metrics, base_prediction, feature_importances, calibration_info
        )
        
        prediction = PartitionPrediction(
            optimal_partitions=base_prediction['optimal_partitions'],
            base_confidence=base_prediction['confidence'],
            calibrated_confidence=calibration_info,
            predicted_performance_gain=base_prediction['predicted_gain'],
            uncertainty_range=uncertainty_range,
            feature_importances=feature_importances[:5],  # 只返回最重要的5个
            reason=reason,
            features=features,
            timestamp=time.time(),
            model_version=self.model_version,
            online_learning_update=(time.time() - self.last_online_update) < 300
        )
        
        # 6. 更新统计
        self._update_prediction_stats(prediction)
        self.predictions.append(prediction)
        
        return prediction
    
    def _base_prediction(self, metrics: CacheMetrics, features: Dict[str, float], 
                        min_partitions: int, max_partitions: int) -> Dict[str, Any]:
        """基础预测逻辑"""
        if self.model is None or self.model == "heuristic":
            return self._heuristic_prediction(metrics, min_partitions, max_partitions)
        
        try:
            # 使用机器学习模型
            X = np.array([list(features.values())])
            
            if self.feature_scaler is not None:
                X_scaled = self.feature_scaler.transform(X)
            else:
                X_scaled = X
            
            # 预测性能评分
            predicted_score = self.model.predict(X_scaled)[0]
            
            # 搜索最优分区
            candidate_partitions = list(range(min_partitions, max_partitions + 1, 1))
            best_partitions = metrics.current_partitions
            best_score = self.calculate_performance_score(metrics)
            
            # 简单启发式结合
            ideal_by_size = int(np.sqrt(max(1, metrics.cache_size))) + 1
            ideal_by_size = max(min_partitions, min(max_partitions, ideal_by_size))
            
            # 置信度估计
            confidence = self._estimate_prediction_confidence(features, predicted_score)
            
            # 选择最优分区
            if predicted_score > best_score + 0.05:  # 显著提升
                optimal_partitions = ideal_by_size
            else:
                optimal_partitions = metrics.current_partitions
            
            # 确保在范围内
            optimal_partitions = max(min_partitions, min(max_partitions, optimal_partitions))
            
            return {
                'optimal_partitions': optimal_partitions,
                'confidence': confidence,
                'predicted_gain': max(0, predicted_score - best_score),
                'method': 'machine_learning'
            }
            
        except Exception as e:
            print(f"[EnhancedCachePredictor] 机器学习预测失败: {e}")
            return self._heuristic_prediction(metrics, min_partitions, max_partitions)
    
    def _heuristic_prediction(self, metrics: CacheMetrics, 
                             min_partitions: int, max_partitions: int) -> Dict[str, Any]:
        """启发式预测"""
        cache_size = metrics.cache_size
        
        # 基于缓存大小的启发式
        if cache_size < 50:
            optimal = max(min_partitions, 2)
        elif cache_size < 200:
            optimal = max(min_partitions, 4)
        elif cache_size < 1000:
            optimal = max(min_partitions, 6)
        else:
            optimal = min(max_partitions, 8)
        
        # 调整基于性能指标
        avg_lock_wait = (metrics.total_lock_wait_time / 
                        max(1, metrics.total_lock_wait_count))
        if avg_lock_wait > 0.001:
            optimal = min(max_partitions, optimal + 2)
        
        current_score = self.calculate_performance_score(metrics)
        confidence = 0.5  # 启发式方法置信度中等
        
        return {
            'optimal_partitions': optimal,
            'confidence': confidence,
            'predicted_gain': 0.05,  # 启发式方法预计小幅度提升
            'method': 'heuristic'
        }
    
    def _estimate_prediction_confidence(self, features: Dict[str, float], 
                                       predicted_score: float) -> float:
        """估计预测置信度"""
        confidence = 0.7  # 基础置信度
        
        # 基于特征质量调整
        if features.get('cache_size', 0) > 100:
            confidence += 0.1  # 大数据更可靠
        
        if features.get('hit_rate', 0) > 0.5:
            confidence += 0.05  # 高命中率系统更稳定
        
        # 基于预测值合理性
        if 0.3 <= predicted_score <= 0.9:
            confidence += 0.1
        else:
            confidence -= 0.2  # 极端值可靠性较低
        
        return min(0.95, max(0.3, confidence))
    
    def _analyze_feature_importance(self, features: Dict[str, float]) -> List[FeatureImportance]:
        """分析特征重要性"""
        if not self.feature_importance_history:
            return []
        
        # 使用最近的特征重要性分析
        recent_importance = self.feature_importance_history[-1] if self.feature_importance_history else []
        
        # 为当前特征值添加上下文
        enhanced_importance = []
        for importance in recent_importance:
            feature_name = importance.feature_name
            current_value = features.get(feature_name, 0)
            
            # 根据当前值调整重要性描述
            description = f"{importance.description} (当前值: {current_value:.3f})"
            
            enhanced_importance.append(FeatureImportance(
                feature_name=feature_name,
                importance_score=importance.importance_score,
                rank=importance.rank,
                description=description,
                impact_direction=importance.impact_direction
            ))
        
        return enhanced_importance
    
    def _calibrate_confidence(self, 
                             base_prediction: Dict[str, Any],
                             features: Dict[str, float],
                             metrics: CacheMetrics) -> CalibrationInfo:
        """置信度校准"""
        predicted_confidence = base_prediction['confidence']
        
        # 简单校准模型
        calibration_factor = 1.0
        
        # 基于历史准确性校准
        if len(self.calibration_data) > 10:
            recent_accuracy = sum(1 for c in self.calibration_data if c['accurate']) / len(self.calibration_data)
            calibration_factor *= (recent_accuracy / 0.7)  # 以70%为基准
        
        # 基于特征稳定性校准
        feature_stability = self._calculate_feature_stability(features)
        calibration_factor *= feature_stability
        
        # 基于数据充分性校准
        data_sufficiency = min(1.0, len(self.history) / 100.0)
        calibration_factor *= (0.5 + 0.5 * data_sufficiency)
        
        calibrated_confidence = predicted_confidence * calibration_factor
        calibrated_confidence = min(0.99, max(0.1, calibrated_confidence))
        
        # 可靠性评分
        reliability_score = self._calculate_reliability_score(features, metrics)
        
        # 不确定性等级
        if calibrated_confidence > 0.8:
            uncertainty_level = 'low'
        elif calibrated_confidence > 0.6:
            uncertainty_level = 'medium'
        else:
            uncertainty_level = 'high'
        
        return CalibrationInfo(
            predicted_confidence=predicted_confidence,
            calibrated_confidence=calibrated_confidence,
            calibration_factor=calibration_factor,
            reliability_score=reliability_score,
            uncertainty_level=uncertainty_level
        )
    
    def _calculate_feature_stability(self, features: Dict[str, float]) -> float:
        """计算特征稳定性"""
        if len(self.history) < 10:
            return 0.7
        
        # 计算最近特征值的变化
        recent_features = []
        for metrics in list(self.history)[-10:]:
            recent_feat, _ = self.extract_features(metrics)
            recent_features.append(recent_feat)
        
        # 简单稳定性评分
        stability = 0.8  # 基础稳定性
        
        return stability
    
    def _calculate_reliability_score(self, features: Dict[str, float], 
                                    metrics: CacheMetrics) -> float:
        """计算可靠性评分"""
        score = 0.5  # 基础评分
        
        # 基于数据质量
        if metrics.cache_size > 50:
            score += 0.2
        
        if metrics.hit_rate > 0.3:
            score += 0.1
        
        # 基于特征合理性
        if 0.3 <= features.get('imbalance_ratio', 1.0) <= 3.0:
            score += 0.1
        
        if features.get('lock_intensity', 0) < 0.01:
            score += 0.1
        
        return min(1.0, score)
    
    def _estimate_uncertainty_range(self, 
                                   base_prediction: Dict[str, Any],
                                   calibration: CalibrationInfo) -> Tuple[float, float]:
        """估计不确定性范围"""
        base_gain = base_prediction['predicted_gain']
        confidence = calibration.calibrated_confidence
        
        # 基于置信度计算不确定性范围
        if confidence > 0.8:
            uncertainty = base_gain * 0.2  # ±20%
        elif confidence > 0.6:
            uncertainty = base_gain * 0.4  # ±40%
        else:
            uncertainty = base_gain * 0.6  # ±60%
        
        lower_bound = max(0, base_gain - uncertainty)
        upper_bound = min(1.0, base_gain + uncertainty)
        
        return (lower_bound, upper_bound)
    
    def _generate_enhanced_reason(self,
                                 metrics: CacheMetrics,
                                 base_prediction: Dict[str, Any],
                                 feature_importances: List[FeatureImportance],
                                 calibration: CalibrationInfo) -> str:
        """生成增强版预测原因"""
        parts = []
        
        # 基础预测信息
        if base_prediction['optimal_partitions'] > metrics.current_partitions:
            parts.append(f"建议从 {metrics.current_partitions} 分区增加到 {base_prediction['optimal_partitions']} 分区")
        elif base_prediction['optimal_partitions'] < metrics.current_partitions:
            parts.append(f"建议从 {metrics.current_partitions} 分区减少到 {base_prediction['optimal_partitions']} 分区")
        else:
            parts.append(f"保持当前 {metrics.current_partitions} 分区配置")
        
        # 添加性能预测
        if base_prediction['predicted_gain'] > 0.05:
            parts.append(f"预计性能提升 {base_prediction['predicted_gain']:.1%}")
        
        # 添加关键特征影响
        if feature_importances:
            top_feature = feature_importances[0]
            parts.append(f"主要影响因素: {top_feature.description}")
        
        # 添加置信度信息
        if calibration.uncertainty_level == 'high':
            parts.append("预测不确定性较高，建议谨慎实施")
        elif calibration.uncertainty_level == 'medium':
            parts.append("预测有中等不确定性")
        else:
            parts.append("预测可靠性较高")
        
        return "；".join(parts)
    
    def _update_prediction_stats(self, prediction: PartitionPrediction):
        """更新预测统计"""
        self.prediction_stats['total_predictions'] += 1
        
        # 记录用于后续校准
        self.calibration_data.append({
            'timestamp': time.time(),
            'predicted_confidence': prediction.calibrated_confidence.predicted_confidence,
            'calibrated_confidence': prediction.calibrated_confidence.calibrated_confidence,
            'predicted_gain': prediction.predicted_performance_gain,
            'accurate': None  # 将在实际执行后更新
        })
    
    def record_prediction_outcome(self, 
                                 prediction: PartitionPrediction,
                                 actual_partitions: int,
                                 actual_performance_change: float):
        """记录预测结果与实际结果的对比"""
        # 查找对应的校准数据
        for i, cal_data in enumerate(self.calibration_data):
            if abs(cal_data['timestamp'] - prediction.timestamp) < 1.0:
                # 检查预测准确性
                predicted_correct = (abs(prediction.optimal_partitions - actual_partitions) <= 1)
                cal_data['accurate'] = predicted_correct
                cal_data['actual_performance_change'] = actual_performance_change
                
                # 更新统计
                if predicted_correct:
                    self.prediction_stats['correct_predictions'] += 1
                
                # 高置信度预测统计
                if prediction.calibrated_confidence.calibrated_confidence > 0.7:
                    self.prediction_stats['high_confidence_total'] += 1
                    if predicted_correct:
                        self.prediction_stats['high_confidence_correct'] += 1
                
                # 更新校准误差
                error = abs(prediction.predicted_performance_gain - actual_performance_change)
                self.prediction_stats['avg_absolute_error'] = (
                    self.prediction_stats['avg_absolute_error'] * 0.9 + error * 0.1
                )
                
                break
    
    def save_model(self):
        """保存模型"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'feature_scaler': self.feature_scaler,
                    'feature_names': self.feature_names,
                    'model_version': self.model_version,
                    'last_training_time': self.last_training_time,
                    'prediction_stats': self.prediction_stats,
                }, f)
        except Exception as e:
            print(f"[EnhancedCachePredictor] 保存模型失败: {e}")
    
    def load_model(self):
        """加载模型"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.feature_scaler = data.get('feature_scaler')
                    self.feature_names = data.get('feature_names')
                    self.model_version = data.get('model_version', '1.0.0')
                    self.last_training_time = data.get('last_training_time', 0)
                    self.prediction_stats = data.get('prediction_stats', self.prediction_stats)
                return True
        except Exception as e:
            print(f"[EnhancedCachePredictor] 加载模型失败: {e}")
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        high_confidence_accuracy = 0
        if self.prediction_stats['high_confidence_total'] > 0:
            high_confidence_accuracy = (
                self.prediction_stats['high_confidence_correct'] / 
                self.prediction_stats['high_confidence_total']
            )
        
        overall_accuracy = 0
        if self.prediction_stats['total_predictions'] > 0:
            overall_accuracy = (
                self.prediction_stats['correct_predictions'] / 
                self.prediction_stats['total_predictions']
            )
        
        return {
            'model_version': self.model_version,
            'total_predictions': self.prediction_stats['total_predictions'],
            'correct_predictions': self.prediction_stats['correct_predictions'],
            'overall_accuracy': overall_accuracy,
            'high_confidence_accuracy': high_confidence_accuracy,
            'avg_absolute_error': self.prediction_stats['avg_absolute_error'],
            'history_size': len(self.history),
            'actual_outcomes': len(self.actual_outcomes),
            'feature_importance_updates': len(self.feature_importance_history),
            'online_learning_enabled': self.online_learning_enabled,
            'last_online_update': self.last_online_update,
        }


# 全局增强预测器实例
_enhanced_predictor_instance = None

def get_enhanced_cache_predictor() -> EnhancedCachePredictor:
    """获取全局增强缓存预测器实例"""
    global _enhanced_predictor_instance
    if _enhanced_predictor_instance is None:
        _enhanced_predictor_instance = EnhancedCachePredictor()
        _enhanced_predictor_instance.load_model()
    return _enhanced_predictor_instance


if __name__ == '__main__':
    # 简单测试
    predictor = EnhancedCachePredictor()
    print("增强版缓存分区预测器初始化完成")
    stats = predictor.get_statistics()
    print(f"模型状态: {stats}")


